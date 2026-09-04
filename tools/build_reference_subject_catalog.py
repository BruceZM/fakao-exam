"""Build a subject summary for OCR reference documents."""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--markdown',type=Path,required=True); a=ap.parse_args(); c=sqlite3.connect(a.db); rows=c.execute('select path,title,ocr_text from reference_documents').fetchall(); names=['民法','刑法','民事诉讼法','刑事诉讼法','行政法','商经知','三国法','理论法']; out={s:{'documents':0,'characters':0,'paths':[]} for s in names}; out['其他']={'documents':0,'characters':0,'paths':[]}
 for path,title,text in rows:
  s=next((x for x in names if x in (title or '') or x in path),'其他'); out[s]['documents']+=1; out[s]['characters']+=len(text or ''); out[s]['paths'].append(path)
 report={'schema_version':1,'status':'reference_subject_catalog','summary':{'documents':len(rows),'characters':sum(len(r[2] or '') for r in rows)},'subjects':out}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# 参考资料科目目录','','当前 OCR 参考文档的科目归类和文本规模。参考资料不等同于标准答案或已授权题库。','','| 科目 | 文档数 | OCR 字符数 |','|---|---:|---:|']+[f"| {s} | {v['documents']} | {v['characters']} |" for s,v in out.items()]; a.markdown.parent.mkdir(parents=True,exist_ok=True); a.markdown.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(report['summary'])
if __name__=='__main__': main()
