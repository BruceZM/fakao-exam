"""Render source admission items as a licensing review queue."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 x=json.loads(a.input.read_text(encoding='utf-8')); items=x.get('items',[])
 lines=['# 法考知识库来源授权复核队列','','本页由 `tools/build_license_review_markdown.py` 生成。授权状态未知时，资料可留在内部审校区，但不得进入产品准入数据。','',f'来源总数：**{len(items)}**；当前已准入：**{sum(i.get("product_admission")=="admitted" for i in items)}**','', '| 来源 | 类型 | 科目/阶段 | 内容状态 | 授权状态 | 产品准入 | 建议动作 |','|---|---|---|---|---|---|---|']
 for i in items:
  action='核验原作者/机构授权并留存凭证'
  if i.get('source_type')=='recalled_exam': action='确认回忆题整理来源及商业使用边界'
  elif 'answer' in (i.get('source_type') or ''): action='确认答案/解析转载授权及与题目版对应关系'
  lines.append(f"| `{i.get('source_id','')}` {i.get('title','')} | `{i.get('source_type','')}` | {i.get('subject','')}/{i.get('stage','')} | {i.get('content_status','')} | {i.get('license_status','')} | {i.get('product_admission','')} | {action} |")
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'sources={len(items)} output={a.output}')
if __name__=='__main__': main()
