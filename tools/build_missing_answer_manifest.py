"""Create a stable question-id manifest for the current missing-answer queue."""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); c=sqlite3.connect(a.db); c.row_factory=sqlite3.Row
 rows=c.execute("select q.question_id,q.source_id,q.subject,q.stage,q.source_page,s.archive_path from questions q left join sources s on s.source_id=q.source_id where coalesce(trim(q.answer),'')='' order by q.source_id,q.question_id").fetchall()
 items=[dict(r) for r in rows]; out={'schema_version':1,'status':'open_missing_answer_manifest','count':len(items),'items':items}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'count={len(items)} output={a.output}')
if __name__=='__main__': main()
