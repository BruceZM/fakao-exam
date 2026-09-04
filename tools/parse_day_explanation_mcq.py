"""Parse DAY<n> answer-and-explanation OCR documents into MCQ records."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--source-id',required=True); ap.add_argument('--subject',default='刑法'); a=ap.parse_args()
    raw=a.input.read_text(encoding='utf-8',errors='replace')
    blocks=re.split(r'(?m)^DAY\s*([0-9]+)\s*$',raw)
    items=[]
    for i in range(1,len(blocks),2):
        n=int(blocks[i]); b=re.sub(r'\s+',' ',blocks[i+1]).strip()
        am=re.search(r'本题答案\s*[:：]?\s*([A-D]{1,4})',b,re.I)
        answer=am.group(1).upper() if am else None
        pre=b[:am.start()] if am else b
        option_area=b[am.end():] if am else ''
        # remove page/source residues and split the question's options
        om=list(re.finditer(r'(?<![A-Za-z])([A-D])\s*[\.．、:：]',option_area))
        if om:
            stem=pre.strip(); opts=[]
            for j,m in enumerate(om):
                end=om[j+1].start() if j+1<len(om) else len(option_area)
                txt=option_area[m.end():end].strip(); opts.append({'key':m.group(1),'text':txt})
        else: stem=pre.strip(); opts=[]
        explanation=b[am.end():].strip() if am else ''
        items.append({'question_id':f'{a.source_id}-{n:03d}','stage':'objective','subject':a.subject,'question_type':'multiple_choice' if '多选' in stem else 'single_choice','stem':stem,'options':opts,'answer':answer,'answer_raw':answer or '','explanation':explanation,'knowledge_points':[],'statutes':[],'source_id':a.source_id,'source_page':None,'source_page_status':'needs_page_mapping','license_status':'unknown','content_status':'parsed','review_status':'needs_human_review'})
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'schema_version':1,'status':'parsed_day_explanation_mcq','items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'items={len(items)} answers={sum(bool(x["answer"]) for x in items)} output={a.output}')
if __name__=='__main__': main()
