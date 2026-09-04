"""Parse dated daily short-answer Q&A OCR blocks."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--source-id',required=True); ap.add_argument('--subject',default='民法'); a=ap.parse_args()
 raw=re.sub(r'\s+',' ',a.input.read_text(encoding='utf-8',errors='replace')); marks=list(re.finditer(r'(?:【?(?:2026[^】]{0,20}法考民法每日一题|每日一题)\s*([0-9]{1,2})】?)',raw)); items=[]
 for i,m in enumerate(marks):
  end=marks[i+1].start() if i+1<len(marks) else len(raw); b=raw[m.end():end].strip(); cue=re.search(r'(?:问：|答案：|答：)',b)
  if not cue: continue
  question=b[:cue.start()].strip(); tail=b[cue.start():]; am=re.search(r'(?:答案|答)\s*[:：]\s*',tail); answer=tail[am.end():].strip() if am else ''
  # The answer text may contain explanatory prompts; preserve verbatim for review.
  items.append({'question_id':f'{a.source_id}-{len(items)+1:03d}','stage':'objective_subjective_common','subject':a.subject,'question_type':'short_answer','stem':question,'options':[],'answer':answer or None,'answer_raw':answer,'explanation':'','knowledge_points':[],'statutes':[],'source_id':a.source_id,'source_page':None,'source_page_status':'needs_page_mapping','license_status':'unknown','content_status':'parsed','review_status':'needs_human_review','source_question_number':int(m.group(1))})
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'schema_version':1,'status':'parsed_daily_short_qa','items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'items={len(items)} answered={sum(bool(i["answer"]) for i in items)} output={a.output}')
if __name__=='__main__': main()
