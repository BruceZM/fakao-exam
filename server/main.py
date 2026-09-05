"""法考练习服务：题库适配、确定性判题与有依据的 AI 反馈。"""
import asyncio
import hashlib
import hmac
import json
import os
import random
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / 'deploy.txt')
load_dotenv(ROOT / '.env')
from server.practice import load_questions, public, reference
from server.grading import grade

QUESTIONS = load_questions()
BY_ID = {q['question_id']: q for q in QUESTIONS}
app = FastAPI(title='法考智能练习')
app.mount('/static', StaticFiles(directory=ROOT / 'server/static'), name='static')


def authenticate(code):
    users = []
    try:
        raw = json.loads(os.getenv('ACCESS_USERS') or '{}')
        if isinstance(raw, list):
            users = [(hashlib.sha256(v.encode()).hexdigest()[:24], f'学习者 {i}', v) for i, v in enumerate(raw, 1) if isinstance(v, str)]
        elif isinstance(raw, dict):
            for uid, value in raw.items():
                if isinstance(value, str):
                    users.append((uid, uid, value))
                elif isinstance(value, dict):
                    users.append((uid, str(value.get('name') or uid), str(value.get('code') or '')))
    except ValueError:
        pass
    default = os.getenv('ACCESS_CODE', '1234')
    if not any(v == default for _, _, v in users):
        users.append(('default', '学习者', default))
    for uid, name, secret in users:
        if code and secret and hmac.compare_digest(code.encode(), secret.encode()):
            return {'id': hashlib.sha256(('fakao-user:' + str(uid)).encode()).hexdigest()[:24], 'name': name}
    return None


def require(x_access_code: Optional[str] = Header(default=None)):
    user = authenticate(x_access_code or '')
    if not user:
        raise HTTPException(403, '口令错误，请重新输入')
    return user


class VerifyIn(BaseModel):
    code: str = Field(max_length=200)


class Submission(BaseModel):
    question_id: str
    answer: str = Field(default='', max_length=16000)
    selected: list[str] = Field(default_factory=list, max_length=8)


def lookup(question_id):
    if question_id not in BY_ID:
        raise HTTPException(404, '题目不存在')
    return BY_ID[question_id]


@app.get('/')
def index():
    return FileResponse(ROOT / 'server/static/index.html')


@app.get('/api/health')
def health():
    return {'status': 'ok', 'mode': 'research', 'questions': len(QUESTIONS), 'revision': os.getenv('DEPLOY_REVISION', 'local')}


@app.post('/api/verify')
def verify(body: VerifyIn):
    user = authenticate(body.code)
    if not user:
        raise HTTPException(403, '口令错误，请重新输入')
    return {'user': user}


@app.get('/api/subjects')
def subjects(user=Depends(require)):
    items = []
    for stage in ('objective', 'subjective'):
        for subject in sorted({q['subject'] for q in QUESTIONS if q['practice_stage'] == stage}):
            rows = [q for q in QUESTIONS if q['subject'] == subject and q['practice_stage'] == stage]
            items.append({'stage': stage, 'subject': subject, 'count': len(rows), 'practice_count': sum(q['practice_ready'] for q in rows), 'scored_count': sum(bool(q['rubrics']) for q in rows)})
    return {'subjects': items}


def filtered(stage=None, subject=None, knowledge=None, mode='practice'):
    return [q for q in QUESTIONS if (not stage or q['practice_stage'] == stage) and (not subject or q['subject'] == subject) and (not knowledge or knowledge in q.get('knowledge_points', [])) and (mode == 'browse' or q['practice_ready'])]


@app.get('/api/questions')
def questions(stage: Optional[str] = None, subject: Optional[str] = None, knowledge: Optional[str] = None, mode: str = Query('practice', pattern='^(practice|browse)$'), limit: int = Query(100, ge=1, le=1500), offset: int = Query(0, ge=0), user=Depends(require)):
    rows = filtered(stage, subject, knowledge, mode)
    return {'total': len(rows), 'items': [public(q) for q in rows[offset:offset + limit]]}


@app.get('/api/next')
def next_question(stage: str, subject: str, current: str = '', order: str = Query('seq', pattern='^(seq|random)$'), knowledge: Optional[str] = None, user=Depends(require)):
    rows = filtered(stage, subject, knowledge)
    if not rows:
        return {'question': None}
    ids = [q['question_id'] for q in rows]
    q = random.choice([q for q in rows if q['question_id'] != current] or rows) if order == 'random' else rows[(ids.index(current) + 1) % len(rows) if current in ids else 0]
    return {'question': public(q)}


@app.get('/api/questions/{question_id}')
def question(question_id: str, user=Depends(require)):
    return public(lookup(question_id))


@app.get('/api/questions/{question_id}/reference')
def question_reference(question_id: str, user=Depends(require)):
    return reference(lookup(question_id))


@app.post('/api/submit')
def submit(body: Submission, user=Depends(require)):
    q = lookup(body.question_id)
    if q['practice_stage'] != 'objective' or not q['practice_ready']:
        raise HTTPException(422, '本题暂不能自动判分')
    keys = {o['key'] for o in q['options']}
    if not body.selected or len(body.selected) != len(set(body.selected)) or not set(body.selected) <= keys or (q['question_type'] != 'multiple_choice' and len(body.selected) != 1):
        raise HTTPException(422, '请选择有效选项')
    return {**reference(q), 'correct': set(body.selected) == set(q['answer_keys']), 'selected': body.selected}


@app.post('/api/grade_stream')
async def grade_stream(body: Submission, user=Depends(require)):
    q = lookup(body.question_id)
    if q['practice_stage'] != 'subjective' or not body.answer.strip():
        raise HTTPException(422, '请先填写主观题作答')
    async def events():
        def event(kind, data):
            return 'event: ' + kind + '\ndata: ' + json.dumps(data, ensure_ascii=False) + '\n\n'
        task = asyncio.create_task(grade(q, body.answer))
        try:
            yield event('progress', {'message': '正在核对作答与参考依据…'})
            while not task.done():
                done, _ = await asyncio.wait({task}, timeout=5)
                if not done:
                    yield ': keepalive\n\n'
            result = task.result()
            for p in result['points']:
                yield event('point', p)
            yield event('complete', {**result, 'reference': reference(q)})
        except asyncio.CancelledError:
            raise
        except Exception:
            yield event('error', {'message': '批改暂时未完成，作答已保留。请重试；若持续失败，请检查模型服务配置。'})
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.post('/api/grade')
async def grade_answer(body: Submission, user=Depends(require)):
    q = lookup(body.question_id)
    if q['practice_stage'] != 'subjective' or not body.answer.strip():
        raise HTTPException(422, '请先填写主观题作答')
    try:
        return {**await grade(q, body.answer), 'reference': reference(q)}
    except Exception:
        raise HTTPException(502, '批改暂时失败，请重试')
