"""Canonical question adapter and evidence-backed practice rules."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPES = {'single_choice': '单选题', 'multiple_choice': '多选题', 'true_false': '判断 · 基础巩固', 'short_answer': '简答训练', 'case_analysis': '案例分析'}


def adapt(q):
    q = dict(q)
    q['practice_stage'] = 'objective' if q['question_type'] in ('single_choice', 'multiple_choice', 'true_false') else 'subjective'
    q['type_label'] = TYPES.get(q['question_type'], '资料')
    options = q.get('options') or []
    answer = str(q.get('answer') or '').strip()
    if q['question_type'] == 'true_false':
        options = [{'key': 'T', 'text': '正确'}, {'key': 'F', 'text': '错误'}]
        keys = {'正确': ['T'], '错误': ['F'], '对': ['T'], '错': ['F']}.get(answer, [])
    else:
        keys = sorted(set(re.sub(r'[\s,，、;；]', '', answer.upper()))) if re.fullmatch(r'[A-H\s,，、;；]+', answer.upper()) else []
    q['options'] = options
    valid_options = (len(options) >= 2 and all(isinstance(o, dict) and re.fullmatch('[A-HTF]', str(o.get('key', ''))) and str(o.get('text', '')).strip() for o in options))
    option_keys = [o.get('key') for o in options if isinstance(o, dict)]
    valid_options = valid_options and len(option_keys) == len(set(option_keys))
    valid_answer = bool(keys) and set(keys).issubset(option_keys)
    if q['question_type'] in ('single_choice', 'true_false'):
        valid_answer = valid_answer and len(keys) == 1
    q['answer_keys'] = keys
    q['practice_ready'] = bool(str(q.get('stem') or '').strip()) and (q['practice_stage'] == 'subjective' or (valid_options and valid_answer))
    q['unavailable_reason'] = '' if q['practice_ready'] else '答案或选项尚不完整，本题仅供资料浏览'
    q['foundation'] = q.get('stage') == 'objective_subjective_common' or q['question_type'] == 'true_false'
    return q


def attach_rubrics(questions, candidates, mapping):
    by_id = {q['question_id']: q for q in questions}
    aliases = {m['question_id']: m['canonical_question_id'] for m in mapping.get('items', [])}
    groups = {}
    for rule in candidates.get('items', []):
        original = rule['question_id']
        canonical = aliases.get(original, original)
        if canonical in by_id:
            groups.setdefault((canonical, original), []).append(rule)
    for q in questions:
        q['rubrics'] = []
        q['max_score'] = None
        source = '\n'.join(str(q.get(k) or '') for k in ('answer_raw', 'answer', 'explanation'))
        compact = re.sub(r'\s', '', source)
        totals = re.findall(r'[（(]\s*(\d+(?:\.\d+)?)\s*分\s*[）)]', q.get('stem', ''))
        # Require an explicit single question total and verbatim source evidence.
        if len(totals) != 1:
            continue
        total = float(totals[0])
        for (canonical, original), rules in groups.items():
            if canonical != q['question_id']:
                continue
            valid = all(r.get('extraction_status') == 'explicit_from_answer' and str(r.get('point_text') or '').strip() and re.sub(r'\s', '', r['point_text']) in compact and isinstance(r.get('score'), (float, int)) and r['score'] > 0 for r in rules)
            if valid and abs(sum(r['score'] for r in rules) - total) < 0.001 and len({r['point_text'] for r in rules}) == len(rules):
                q['rubrics'] = rules
                q['max_score'] = total
                break
    return questions


def load_questions():
    bundle = json.loads((ROOT / 'app/data/questions.json').read_text())
    return attach_rubrics([adapt(q) for q in bundle['questions']], bundle.get('rubric_candidates', {}), bundle.get('canonical_map', {}))


def public(q):
    fields = ('question_id', 'subject', 'question_type', 'stem', 'options', 'knowledge_points', 'practice_stage', 'type_label', 'practice_ready', 'unavailable_reason', 'foundation', 'source_id', 'source_page', 'review_status')
    return {**{k: q.get(k) for k in fields}, 'can_score': bool(q['rubrics']), 'max_score': q['max_score']}


def reference(q):
    return {'answer': q.get('answer_raw') or q.get('answer') or '参考答案待补充', 'answer_keys': q['answer_keys'], 'explanation': q.get('explanation') or '解析待补充', 'source_id': q.get('source_id'), 'source_page': q.get('source_page'), 'review_note': '资料与评分点仍待专业审校；当前为参考练习。'}
