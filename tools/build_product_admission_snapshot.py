"""Summarize which questions may enter a product release."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
 rows=con.execute('''select q.question_id,q.stage,q.subject,s.license_status,s.review_status from questions q join sources s on s.source_id=q.source_id''').fetchall()
 admitted=[r['question_id'] for r in rows if r['license_status']=='licensed' and r['review_status']=='reviewed']
 blocked=[r['question_id'] for r in rows if r['question_id'] not in set(admitted)]
 reasons={}
 for r in rows:
  if r['question_id'] in admitted: continue
  key=f"license_status={r['license_status']};review_status={r['review_status']}"; reasons[key]=reasons.get(key,0)+1
 out={'schema_version':1,'status':'product_admission_snapshot','summary':{'questions':len(rows),'admitted':len(admitted),'blocked':len(blocked),'reasons':reasons},'admitted_question_ids':admitted,'notes':['准入仅在来源授权为 licensed 且来源审校为 reviewed 时成立。','blocked 不代表题目不可研究，仅表示当前不能直接进入产品发布层。']}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"questions={len(rows)} admitted={len(admitted)} blocked={len(blocked)} output={a.output}")
if __name__=='__main__': main()
