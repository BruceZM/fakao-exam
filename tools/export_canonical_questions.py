from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--canonical-map',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args()
 m=json.loads(a.canonical_map.read_text(encoding='utf-8')); mapped={x['question_id'] for x in m.get('items',[])}; excluded={x['question_id'] for x in m.get('items',[]) if not x.get('is_canonical')}; ids=None; con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
 rows=con.execute('select * from questions order by question_id').fetchall(); out={}
 for stage in ('objective','subjective'):
  p=a.output_dir/f'canonical_{stage}_questions.jsonl'; n=0
  with p.open('w',encoding='utf-8') as f:
   for r in rows:
    if r['question_id'] in excluded: continue
    if stage=='subjective':
     if r['stage'] not in ('subjective','objective_subjective_common'): continue
    elif r['stage']!='objective': continue
    x=dict(r); x['options']=[dict(z) for z in con.execute('select option_key as key,option_text as text from options where question_id=? order by option_key',(r['question_id'],))]; x['knowledge_points']=[z[0] for z in con.execute('select knowledge_point from question_knowledge_points where question_id=? order by knowledge_point',(r['question_id'],))]; x['product_admission']='blocked_pending_license_or_review'; f.write(json.dumps(x,ensure_ascii=False)+'\n'); n+=1
  out[stage]=n
 print(out)
if __name__=='__main__':main()
