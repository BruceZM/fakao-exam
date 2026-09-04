"""Render subject-level prioritization from the readiness report."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--readiness',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    x=json.loads(a.readiness.read_text(encoding='utf-8')); rows=[]
    for s in x['subjects']: rows.append((s['n']-s['answered'],s['n']-s['explained'],s['subject'],s['n'],s['answer_rate'],s['explanation_rate'],s['sources']))
    rows.sort(reverse=True); lines=['# 法考知识库补齐优先级','','按缺失答案数量排序；优先处理答案和解析同时缺口较大的科目。统计由当前 readiness 快照生成，不能替代内容审校。','','| 优先级 | 科目 | 题量 | 缺失答案 | 缺失解析 | 答案覆盖 | 解析覆盖 | 来源数 |','|---:|---|---:|---:|---:|---:|---:|---:|']
    for i,(ma,me,sub,n,ar,er,src) in enumerate(rows,1): lines.append(f'| {i} | {sub} | {n} | {ma} | {me} | {ar:.2%} | {er:.2%} | {src} |')
    lines += ['',f'当前全库缺失答案：**{x["totals"]["questions"]-x["totals"]["answered"]}** 条；缺失解析：**{x["totals"]["questions"]-x["totals"]["explained"]}** 条。']
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'subjects={len(rows)} output={a.output}')
if __name__=='__main__': main()
