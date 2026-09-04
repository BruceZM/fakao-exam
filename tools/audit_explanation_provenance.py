"""Audit provenance fields for non-empty question explanations."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--questions-dir',type=Path,required=True); ap.add_argument('--sources',type=Path); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    source_paths={}
    if a.sources and a.sources.exists():
        doc=json.loads(a.sources.read_text(encoding='utf-8'))
        entries = doc.get('sources', doc.get('items', doc if isinstance(doc,list) else []))
        for s in entries: source_paths[s.get('source_id')]=s.get('archive_path')
    from collections import defaultdict
    stats=defaultdict(lambda: {'source_id':'','total':0,'explained':0,'missing_provenance':0})
    queue=[]
    for p in sorted(a.questions_dir.glob('*.enriched.json')):
        doc=json.loads(p.read_text(encoding='utf-8'))
        for q in doc.get('items',[]):
            sid=q.get('source_id','unknown'); x=stats[sid]; x['source_id']=sid; x['total']+=1
            if str(q.get('explanation','')).strip():
                x['explained']+=1
                if not str(q.get('explanation_source','')).strip():
                    x['missing_provenance']+=1
                    queue.append({'question_id':q.get('question_id'),'source_id':sid,'source_page':q.get('source_page'),'archive_path':source_paths.get(sid)})
    rows=sorted(stats.values(),key=lambda x:(-x['missing_provenance'],x['source_id']))
    out={'schema_version':1,'status':'explanation_provenance_audit','summary':{'explained':sum(x['explained'] for x in rows),'explained_missing_provenance':sum(x['missing_provenance'] for x in rows)},'items':rows,'review_queue':queue}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(out['summary'])
if __name__=='__main__': main()
