"""Backfill explanation provenance only when text is directly found in archived OCR."""
from __future__ import annotations
import argparse, json, re, shutil, difflib
from datetime import datetime, timezone
from pathlib import Path

def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--questions-dir',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--backup-dir',type=Path,required=True)
    ap.add_argument('--lineage-dir',type=Path,required=True)
    args=ap.parse_args()
    sources=json.loads(args.sources.read_text(encoding='utf-8')).get('sources',[])
    paths={s.get('source_id'):s.get('archive_path') for s in sources}
    override_path=args.root/'data/provenance/explanation_ocr_overrides.json'
    if override_path.exists():
        overrides=json.loads(override_path.read_text(encoding='utf-8')).get('items',[])
        override_map={x.get('source_id'):x.get('ocr_ref') for x in overrides if x.get('source_id') and x.get('ocr_ref')}
    else:
        override_map={}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    changed=[]
    for p in sorted(args.questions_dir.glob('*.enriched.json')):
        doc=json.loads(p.read_text(encoding='utf-8'))
        original=p.read_bytes(); items=doc.get('items',[]); file_changes=[]
        for q in items:
            e=str(q.get('explanation','')).strip()
            if not e or str(q.get('explanation_source','')).strip(): continue
            sid=q.get('source_id')
            override_ref=override_map.get(sid)
            if override_ref:
                ocr=args.root/override_ref
            else:
                archive_rel=paths.get(sid)
                if not archive_rel: continue
                ocr=args.root/archive_rel/'ocr.txt'
            if not ocr.exists(): continue
            text=ocr.read_text(encoding='utf-8',errors='ignore')
            prefix=norm(e[:80])
            if len(prefix)<20: continue
            normalized_text=norm(text)
            direct=prefix in normalized_text
            fuzzy=False
            if not direct:
                key=prefix[:8]
                for pos in [m.start() for m in re.finditer(re.escape(key), normalized_text)][:20]:
                    cand=normalized_text[pos:pos+len(prefix)]
                    if difflib.SequenceMatcher(None,prefix,cand).ratio() >= 0.985:
                        fuzzy=True; break
            if not (direct or fuzzy): continue
            q['explanation_source']='source_ocr'
            q['explanation_source_ref']=str(ocr.relative_to(args.root))
            q['explanation_provenance_status']='matched_in_ocr'
            q['explanation_review_status']='needs_human_review'
            file_changes.append(q.get('question_id'))
        if file_changes:
            backup=args.backup_dir/f'{p.stem}.{stamp}.json'
            backup.parent.mkdir(parents=True,exist_ok=True); backup.write_bytes(original)
            p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            changed.append({'file':str(p),'backup':str(backup),'question_ids':file_changes})
    lineage=args.lineage_dir/f'{stamp}-explanation-provenance-backfill.json'
    lineage.parent.mkdir(parents=True,exist_ok=True)
    lineage.write_text(json.dumps({'schema_version':1,'status':'completed','method':'normalized_explanation_prefix_exact_or_high_similarity_match_in_archived_ocr','changed_questions':sum(len(x['question_ids']) for x in changed),'files':changed,'created_at':stamp},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'changed_questions':sum(len(x['question_ids']) for x in changed),'changed_files':len(changed),'lineage':str(lineage)},ensure_ascii=False))
if __name__=='__main__': main()
