"""Build a queue for objective-answer/type conflicts and residue."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--db", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    con = sqlite3.connect(args.db)
    rows = con.execute("SELECT question_id,source_id,subject,question_type,answer,answer_raw,substr(stem,1,180) FROM questions WHERE question_type IN ('single_choice','multiple_choice') AND answer_raw IS NOT NULL AND trim(answer_raw)!=''").fetchall()
    items=[]
    for qid,sid,subject,qtype,answer,raw,preview in rows:
        raw=str(raw).strip().upper().translate(str.maketrans('ＡＢＣＤ','ABCD'))
        letters=''.join(re.findall('[A-D]',raw)); residue=re.sub(r'[A-D\s,，、。．.;；:：()（）\[\]【】]+','',raw)
        flags=[]
        if qtype=='single_choice' and len(set(letters))>1 and not residue: flags.append('single_type_but_multiple_raw_choices')
        if qtype=='multiple_choice' and len(set(letters))>=2 and not residue and ''.join(dict.fromkeys(letters)) != (answer or '').strip().upper(): flags.append('answer_differs_from_clean_raw')
        if residue and any(x in raw for x in ('PAGE','路遥','法考','解析','项')): flags.append('answer_raw_residue')
        if flags: items.append({'question_id':qid,'source_id':sid,'subject':subject,'question_type':qtype,'answer':answer,'answer_raw':raw,'stem_preview':preview,'flags':flags,'status':'needs_manual_answer_review'})
    result={'schema_version':1,'status':'answer_conflict_queue','summary':{'items':len(items),'single_type_but_multiple_raw_choices':sum('single_type_but_multiple_raw_choices' in x['flags'] for x in items),'answer_differs_from_clean_raw':sum('answer_differs_from_clean_raw' in x['flags'] for x in items),'answer_raw_residue':sum('answer_raw_residue' in x['flags'] for x in items)},'items':items,'notes':['队列仅提示字段冲突，不自动判断标准答案；需结合原始题册和题型说明人工确认。']}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"queued={len(items)} summary={result['summary']} output={args.output}")


if __name__=='__main__': main()
