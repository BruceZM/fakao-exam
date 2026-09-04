"""Audit extracted subjective rubric candidates for structural integrity."""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--rubrics',type=Path,required=True); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 data=json.loads(a.rubrics.read_text(encoding='utf-8')); items=data.get('items',[]); con=sqlite3.connect(a.db)
 qids={r[0] for r in con.execute('select question_id from questions')}; ids=set(); errors=[]
 for x in items:
  rid=x.get('rubric_id');
  if not rid or rid in ids: errors.append({'rubric_id':rid,'error':'missing_or_duplicate_id'})
  ids.add(rid)
  if not str(x.get('point_text','')).strip(): errors.append({'rubric_id':rid,'error':'empty_point_text'})
  if not isinstance(x.get('score'),(int,float)) or x.get('score',0)<=0: errors.append({'rubric_id':rid,'error':'invalid_score'})
  if x.get('question_id') not in qids: errors.append({'rubric_id':rid,'error':'orphan_question_id'})
 result={'schema_version':1,'status':'rubric_audit','ok':not errors,'summary':{'items':len(items),'errors':len(errors)},'errors':errors}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"items={len(items)} errors={len(errors)} output={a.output}")
if __name__=='__main__': main()
