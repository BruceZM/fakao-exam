from __future__ import annotations
import argparse,json,re
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args(); d=json.loads(a.input.read_text(encoding='utf-8')); changed=[]
 for x in d.get('items',[]):
  ans=(x.get('answer') or '').strip().upper(); raw=(x.get('answer_raw') or '').strip()
  if not re.fullmatch('[A-D]',ans) or not raw: continue
  m=re.match(r'^([A-Da-d])(?:\s+|$)',raw)
  if m and m.group(1).upper()==ans and len(raw)>1:
   x['answer_raw']=ans; x['answer_normalization_status']='cleaned_ocr_residue_from_answer_raw'; x['answer_review_status']='needs_human_review'; changed.append(x['question_id'])
 a.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'cleaned={len(changed)}'); print('\n'.join(changed))
if __name__=='__main__':main()
