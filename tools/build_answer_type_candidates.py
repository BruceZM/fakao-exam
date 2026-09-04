from __future__ import annotations
import argparse,json,re,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
 items=[]
 for r in con.execute('select question_id,subject,question_type,answer,answer_raw,source_page from questions'):
  raw=(r['answer_raw'] or '').strip(); m=re.match(r'^([A-D]{2,4})(?:\s|$)',raw.upper())
  if m and len(set(m.group(1)))>1 and r['question_type']=='single_choice': items.append({'question_id':r['question_id'],'subject':r['subject'],'current_question_type':r['question_type'],'current_answer':r['answer'],'raw_choice_sequence':m.group(1),'source_page':r['source_page'],'candidate_question_type':'multiple_choice','status':'needs_human_review'})
 out={'schema_version':1,'status':'answer_type_candidates','summary':{'items':len(items)},'items':items,'notes':['候选仅由原始答案开头的连续选项字母生成，不自动改写题型或答案。','须回看原始题册确认是否为多选题、答案是否完整。']}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print('items='+str(len(items)))
if __name__=='__main__':main()
