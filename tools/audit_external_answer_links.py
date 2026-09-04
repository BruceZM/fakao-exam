"""Audit external answer-link candidates without fetching protected content."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 data=json.loads(a.input.read_text(encoding='utf-8')); items=data.get('items',[]); seen=set(); errors=[]
 for x in items:
  key=(x.get('source_id'),x.get('question_no'),x.get('url'))
  if key in seen: errors.append({'item':key,'error':'duplicate'})
  seen.add(key)
  if not x.get('source_id'): errors.append({'item':key,'error':'missing_source_id'})
  if not isinstance(x.get('question_no'),int) or x['question_no']<=0: errors.append({'item':key,'error':'invalid_question_no'})
  if not re.match(r'^https?://t\.cn/[A-Za-z0-9]+$',str(x.get('url',''))): errors.append({'item':key,'error':'invalid_short_url'})
 result={'schema_version':1,'status':'external_answer_link_audit','ok':not errors,'summary':{'items':len(items),'errors':len(errors)},'errors':errors}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"items={len(items)} errors={len(errors)} output={a.output}")
if __name__=='__main__': main()
