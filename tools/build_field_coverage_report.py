"""Build field-level coverage metrics for the legal-exam question bank."""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
 fields={'stem':'stem','question_type':'question_type','source_id':'source_id','source_page':'source_page','answer':'answer','explanation':'explanation'}
 rows=con.execute('select * from questions').fetchall(); cov={}
 for name,col in fields.items(): cov[name]={'present':sum(bool(str(r[col]).strip()) if r[col] is not None else False for r in rows),'total':len(rows)}; cov[name]['rate']=round(cov[name]['present']/len(rows),4)
 for name,sql in [('options','select count(distinct question_id) from options'),('knowledge_points','select count(distinct question_id) from question_knowledge_points'),('statutes','select count(distinct question_id) from question_statutes')]:
  n=con.execute(sql).fetchone()[0]; cov[name]={'present':n,'total':len(rows),'rate':round(n/len(rows),4)}
 by_stage={}
 for stage,label in [('objective','objective'),('subjective','subjective')]:
  subset=[r for r in rows if (r['stage']=='objective' if stage=='objective' else r['stage'] in ('subjective','objective_subjective_common'))]
  by_stage[label]={'total':len(subset)}
  for name,col in fields.items():
   n=sum(bool(str(r[col]).strip()) if r[col] is not None else False for r in subset); by_stage[label][name]={'present':n,'rate':round(n/len(subset),4) if subset else 0}
  n=con.execute('select count(distinct o.question_id) from options o join questions q on q.question_id=o.question_id where q.stage=?' ,(stage,)).fetchone()[0] if stage=='objective' else con.execute("select count(distinct o.question_id) from options o join questions q on q.question_id=o.question_id where q.stage in ('subjective','objective_subjective_common')").fetchone()[0]
  by_stage[label]['options']={'present':n,'rate':round(n/len(subset),4) if subset else 0}
 out={'schema_version':1,'status':'field_coverage_report','total_questions':len(rows),'fields':cov,'by_stage':by_stage,'notes':['字段存在不代表内容已人工核验。','答案、解析、法条和授权状态仍需按审校队列处理。']}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"questions={len(rows)} output={a.output}")
if __name__=='__main__': main()
