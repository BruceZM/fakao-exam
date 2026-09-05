"""Build the phase-one app bundle from canonical question exports."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--exports-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 rows=[]
 for name in ('canonical_objective_questions.jsonl','canonical_subjective_questions.jsonl'):
  p=a.exports_dir/name
  if not p.exists(): raise SystemExit(f'missing export: {p}')
  for line in p.read_text(encoding='utf-8').splitlines():
   if line.strip(): rows.append(json.loads(line))
 ids=[x.get('question_id') for x in rows]
 if len(ids)!=len(set(ids)): raise SystemExit('duplicate question_id in bundle')
 payload={'schema_version':1,'mode':'research','source_exports':['canonical_objective_questions.jsonl','canonical_subjective_questions.jsonl'],'questions':rows}

 for key, filename in [('rubric_candidates', 'rubrics/candidates.json'), ('canonical_map', 'provenance/canonical_question_map.json')]:
  source=a.exports_dir.parent/filename
  if not source.exists(): raise SystemExit(f'missing metadata: {source}')
  payload[key]=json.loads(source.read_text(encoding='utf-8'))
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
 print(f'questions={len(rows)} output={a.output}')
if __name__=='__main__': main()
