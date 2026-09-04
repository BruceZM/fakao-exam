"""Export a bounded, reviewable batch from an open question queue."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--issue',default='missing_answer'); ap.add_argument('--limit',type=int,default=50); ap.add_argument('--offset',type=int,default=0); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    c=sqlite3.connect(a.db); c.row_factory=sqlite3.Row
    if a.issue!='missing_answer': raise SystemExit('only missing_answer is currently supported')
    rows=c.execute("select q.question_id,q.source_id,q.subject,q.stage,q.question_type,q.source_page,q.stem,q.answer_raw,s.title source_title,s.archive_path,s.license_status source_license_status,s.review_status source_review_status from questions q left join sources s on s.source_id=q.source_id where coalesce(trim(q.answer),'')='' order by q.source_id,q.question_id limit ? offset ?",(a.limit,a.offset)).fetchall()
    items=[]
    for r in rows:
        options=[dict(x) for x in c.execute('select option_key,option_text from options where question_id=? order by option_key',(r['question_id'],)).fetchall()]
        items.append({**dict(r),'options':options,'review_status':'queued','review_note':''})
    out={'schema_version':1,'status':'open_review_batch','issue':a.issue,'limit':a.limit,'offset':a.offset,'count':len(items),'items':items}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'count={len(items)} output={a.output}')
if __name__=='__main__': main()
