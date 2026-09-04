"""Small product-facing smoke test for the legal-exam knowledge base."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); a=ap.parse_args(); r=a.root.resolve(); errors=[]
    con=sqlite3.connect(r/'data/fakao_knowledge_base.sqlite')
    for keyword in ('抵押权','盗窃罪'):
        n=con.execute("select count(*) from questions where stem like ? or explanation like ?",(f'%{keyword}%',f'%{keyword}%')).fetchone()[0]
        if n==0: errors.append(f'query_no_results:{keyword}')
    for name in ('objective_questions.jsonl','subjective_questions.jsonl','canonical_objective_questions.jsonl','canonical_subjective_questions.jsonl'):
        p=r/'data/exports'/name
        if not p.exists() or p.stat().st_size==0: errors.append(f'empty_export:{name}')
    ids={}
    for name in ('objective_questions.jsonl','subjective_questions.jsonl','canonical_objective_questions.jsonl','canonical_subjective_questions.jsonl'):
        p=r/'data/exports'/name
        if not p.exists(): continue
        seen=[]
        for line in p.read_text(encoding='utf-8').splitlines():
            try: seen.append(json.loads(line)['question_id'])
            except Exception: errors.append(f'invalid_export_row:{name}')
        if len(seen)!=len(set(seen)): errors.append(f'duplicate_export_ids:{name}')
        ids[name]=len(seen)
    for base, canonical in (('objective_questions.jsonl','canonical_objective_questions.jsonl'),('subjective_questions.jsonl','canonical_subjective_questions.jsonl')):
        bp=r/'data/exports'/base; cp=r/'data/exports'/canonical
        if bp.exists() and cp.exists():
            base_ids={json.loads(line)['question_id'] for line in bp.read_text(encoding='utf-8').splitlines() if line.strip()}
            canonical_ids={json.loads(line)['question_id'] for line in cp.read_text(encoding='utf-8').splitlines() if line.strip()}
            if not canonical_ids.issubset(base_ids): errors.append(f'canonical_ids_not_subset:{canonical}')
    result={'status':'passed' if not errors else 'failed','errors':errors,'checks':{'chinese_queries':2,'exports':4,'export_rows':ids}}
    (r/'data/provenance').mkdir(parents=True,exist_ok=True)
    (r/'data/provenance/smoke_test_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2)); raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
