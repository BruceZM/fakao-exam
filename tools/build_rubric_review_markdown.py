"""Render subjective rubric candidates as a reviewable markdown queue."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 x=json.loads(a.input.read_text(encoding='utf-8')); items=x.get('items',[])
 lines=['# 主观题评分点审校队列','','本页由 `tools/build_rubric_review_markdown.py` 生成。评分点来自答案文字的候选提取，必须结合原始评分标准和法律依据人工确认。','',f'当前候选评分点：**{len(items)} 条**','', '| 题目 | 来源 | 科目 | 分值 | 评分点候选 | 状态 |','|---|---|---|---:|---|---|']
 for i in items:
  lines.append(f"| `{i.get('question_id','')}` | `{i.get('source_id','')}` | {i.get('subject','')} | {i.get('score','')} | {str(i.get('point_text','')).replace('|','/')} | {i.get('review_status','')} |")
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'rubrics={len(items)} output={a.output}')
if __name__=='__main__': main()
