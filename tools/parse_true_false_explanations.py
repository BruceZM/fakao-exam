"""Parse numbered true/false explanation OCR into reviewable records."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--source-id',required=True); ap.add_argument('--subject',default='民法'); a=ap.parse_args()
 raw=a.input.read_text(encoding='utf-8',errors='replace'); raw=re.sub(r'\s+',' ',raw); marks=list(re.finditer(r'(?<!\d)(\d{1,2})\.\s*',raw)); items=[]
 for i,m in enumerate(marks):
  end=marks[i+1].start() if i+1<len(marks) else len(raw); b=raw[m.end():end].strip()
  if '答案' not in b and '解析' not in b: continue
  cue=re.search(r'(?:我投给了[^【]{0,30})?【?答案】?\s*[:：]?\s*(正确|错误)',b)
  if not cue: continue
  stem=b[:cue.start()].strip(); explanation=b[cue.end():].strip(); n=int(m.group(1))
  items.append({'question_id':f'{a.source_id}-{len(items)+1:03d}','stage':'objective','subject':a.subject,'question_type':'true_false','stem':stem,'options':[],'answer':cue.group(1),'answer_raw':cue.group(1),'explanation':explanation,'knowledge_points':[],'statutes':[],'source_id':a.source_id,'source_page':None,'source_page_status':'needs_page_mapping','license_status':'unknown','content_status':'parsed','review_status':'needs_human_review','source_question_number':n})
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'schema_version':1,'status':'parsed_true_false_explanations','items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'items={len(items)} answers={sum(bool(i["answer"]) for i in items)} output={a.output}')
if __name__=='__main__': main()
