"""Backfill source pages using a unique stem + first-option OCR match."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def compact(s: str) -> str: return re.sub(r"\s+", "", s or "")

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('--sources',type=Path,required=True); ap.add_argument('output',type=Path); args=ap.parse_args()
    doc=json.loads(args.input.read_text(encoding='utf-8')); sources={x['source_id']:x for x in json.loads(args.sources.read_text(encoding='utf-8'))['sources']}; cache={}; changed=[]
    for item in doc.get('items',[]):
        if item.get('source_page') is not None: continue
        source=sources.get(item.get('source_id'),{}); ocr=Path(source.get('archive_path',''))/'ocr.txt'
        if not ocr.exists(): continue
        if str(ocr) not in cache:
            chunks=re.split(r"===== page-(\d+)\.png =====",ocr.read_text(encoding='utf-8',errors='replace')); cache[str(ocr)]={int(chunks[i]):compact(chunks[i+1]) for i in range(1,len(chunks),2)}
        stem=compact(item.get('stem','')); opt=(item.get('options') or [{}])[0].get('text','');
        if not stem or not opt: continue
        matches=[p for p,t in cache[str(ocr)].items() if stem[:12] in t and compact(opt)[:18] in t]
        if len(matches)==1:
            item['source_page']=matches[0]; item['source_page_status']='located_by_stem_and_first_option_high_confidence'; changed.append({'question_id':item['question_id'],'page':matches[0]})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"items={len(doc.get('items',[]))} located={len(changed)} output={args.output}"); [print(x['question_id'],x['page']) for x in changed]

if __name__=='__main__': main()
