from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--scanned-root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); c=sqlite3.connect(a.db); c.row_factory=sqlite3.Row; items=[]
 for r in c.execute('select source_id,title,archive_path from sources order by source_id'):
  paths=list(a.scanned_root.glob('*/ocr.txt'))
  # Prefer the authoritative archive_path recorded in sources. The title
  # fallback keeps older records usable when an archive path is unavailable.
  archive_dir=Path(r['archive_path'])
  if not archive_dir.is_absolute():
   archive_dir=(a.scanned_root.parent.parent.parent / archive_dir).resolve()
  matches=[]
  if archive_dir.exists():
   matches=list(archive_dir.glob('ocr.txt'))
  if not matches:
   matches=[p for p in paths if r['title'].split('（')[0][:6] in p.parent.name or r['title'][:6] in p.parent.name]
  text='\n'.join(p.read_text(errors='ignore') for p in matches)
  items.append({'source_id':r['source_id'],'title':r['title'],'archive_path':r['archive_path'],'archive_ocr_files':len(matches),'answer_marker_count':text.count('答案'),'explanation_marker_count':text.count('解析'),'availability':'answer_markers_present' if '答案' in text else 'no_answer_marker_found'})
 out={'schema_version':1,'status':'source_answer_availability','items':items,'notes':['仅统计 OCR 文本中的“答案/解析”字样，不代表答案已完整或正确。']}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print('sources='+str(len(items)))
if __name__=='__main__':main()
