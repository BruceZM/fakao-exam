"""Render the current missing-answer review batch index."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--provenance',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    rows=[]
    for p in sorted(a.provenance.glob('review_batch_missing_answer_*.json')):
        d=json.loads(p.read_text(encoding='utf-8')); items=d.get('items',[])
        if not items: continue
        rows.append((p.name,d.get('offset',0),len(items),items[0].get('question_id',''),items[-1].get('question_id','')))
    total=sum(x[2] for x in rows)
    lines=['# 答案审校批次索引','', '当前缺失答案题已按题号排序切分为以下批次。批次文件是题号快照，只用于人工核对，不等同于标准答案；答案补录后会由重建流程自动刷新。','', '| 批次 | offset | 数量 | 首题 | 末题 |','|---|---:|---:|---|---|']
    lines += [f'| {name} | {offset} | {count} | {first} | {last} |' for name,offset,count,first,last in rows]
    lines += ['',f'当前批次数：**{len(rows)}**；覆盖题目：**{total}**。']
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'batches={len(rows)} items={total} output={a.output}')
if __name__=='__main__': main()
