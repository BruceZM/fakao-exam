# -*- coding: utf-8 -*-
"""法考第一阶段研究版：无状态题库服务，学习进度由浏览器保存。"""
from __future__ import annotations
import hashlib, hmac, json, os, pathlib, sqlite3
from typing import Optional
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()
ROOT=pathlib.Path(__file__).resolve().parent.parent
bundle=json.loads((ROOT/'app/data/questions.json').read_text(encoding='utf-8'))
QUESTIONS=bundle['questions']
ACCESS_CODE=os.getenv('ACCESS_CODE','1234')
DB_PATH=pathlib.Path(os.getenv('ANALYTICS_DB_PATH','data/runtime/visitor_stats.db'))
DB_PATH.parent.mkdir(parents=True,exist_ok=True)

def authorized(code): return hmac.compare_digest(code or '',ACCESS_CODE)
def require(code):
 if not authorized(code): raise HTTPException(403,'口令错误')
def public(q):
 return {k:q.get(k) for k in ('question_id','subject','stage','question_type','stem','options','source_page','source_title','review_status','product_admission','knowledge_points')}
def track(req):
 try:
  with sqlite3.connect(DB_PATH) as c:
   c.execute('create table if not exists events(ts text, path text)')
   c.execute('insert into events values(?,?)',(datetime.now(timezone.utc).isoformat(),req.url.path))
 except Exception: pass
app=FastAPI(title='法考备考研究版')
app.mount('/static',StaticFiles(directory=ROOT/'server/static'),name='static')
@app.get('/')
def index(): return FileResponse(ROOT/'server/static/index.html')
@app.get('/api/health')
def health(): return {'status':'ok','mode':bundle['mode'],'questions':len(QUESTIONS)}
@app.get('/api/subjects')
def subjects(x_access_code:Optional[str]=Header(default=None),request:Request=None):
 require(x_access_code); track(request)
 out={}
 for q in QUESTIONS:
  k=(q.get('subject') or '其他',q.get('stage') or 'unknown'); out.setdefault(k,0); out[k]+=1
 return [{'subject':s,'stage':st,'count':n} for (s,st),n in sorted(out.items())]
@app.get('/api/questions')
def questions(subject:Optional[str]=None,stage:Optional[str]=None,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),x_access_code:Optional[str]=Header(default=None),request:Request=None):
 require(x_access_code); track(request)
 rows=[public(q) for q in QUESTIONS if (not subject or q.get('subject')==subject) and (not stage or q.get('stage')==stage)]
 return {'total':len(rows),'items':rows[offset:offset+limit]}
@app.get('/api/questions/{question_id}')
def question(question_id:str,x_access_code:Optional[str]=Header(default=None),request:Request=None):
 require(x_access_code); track(request)
 for q in QUESTIONS:
  if q.get('question_id')==question_id:
   return {**public(q),'answer':q.get('answer'),'explanation':q.get('explanation'),'statutes':q.get('statutes',[])}
 raise HTTPException(404,'题目不存在')
