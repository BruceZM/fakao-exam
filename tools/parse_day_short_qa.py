"""Parse DAY-marked civil-procedure daily Q&A OCR blocks."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--source-id',required=True); ap.add_argument('--subject',default='民诉法'); a=ap.parse_args()
 raw=re.sub(r'\s+',' ',a.input.read_text(encoding='utf-8',errors='replace')); marks=list(re.finditer(r'DAY\s*([0-9]+|T|④)\s*(?:（[^）]*）|\([^)]*\))?',raw,re.I)); items=[]
 for i,m in enumerate(marks):
  end=marks[i+1].start() if i+1<len(marks) else len(raw); b=raw[m.end():end].strip(); b=re.sub(r'[@©◎③]\s*民诉韩[^ ]{0,8}','',b)
  cue=re.search(r'(?:今日答案来[咯啦]|今日准确率[^ ]*|答案来咯|答案来啦|解析\s*[:：])',b)
  if not cue: continue
  stem=b[:cue.start()].strip(); tail=b[cue.end():].strip(); tail=re.sub(r'^Day\s*\d+\s*解析\s*[:：]?\s*','',tail,flags=re.I); tail=re.sub(r'^解析\s*[:：]?\s*','',tail)
  n=m.group(1); n=1 if n.upper()=='T' else 4 if n=='④' else int(n)
  items.append({'question_id':f'{a.source_id}-{len(items)+1:03d}','stage':'objective_subjective_common','subject':a.subject,'question_type':'short_answer','stem':stem,'options':[],'answer':None,'answer_raw':'','explanation':tail,'knowledge_points':[],'statutes':[],'source_id':a.source_id,'source_page':None,'source_page_status':'needs_page_mapping','license_status':'unknown','content_status':'parsed','review_status':'needs_human_review','source_question_number':n})
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'schema_version':1,'status':'parsed_day_short_qa','items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'items={len(items)} output={a.output}')
if __name__=='__main__': main()
