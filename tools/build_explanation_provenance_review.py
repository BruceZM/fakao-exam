"""Render a question-level review list for explanations lacking provenance."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--audit',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 d=json.loads(a.audit.read_text(encoding='utf-8')); items=d.get('review_queue',[])
 lines=['# 解析来源链人工核验清单','', '以下记录已有 explanation，但尚未找到可确认的原始 OCR/解析页。请补充原始文件或准确页码后再回填；不得根据相似文本猜测来源。','',f'待核验：**{len(items)} 条**','', '| 题目 | 来源 | 页码 | 归档目录 |','|---|---|---:|---|']
 for x in items: lines.append(f"| `{x.get('question_id','')}` | `{x.get('source_id','')}` | {x.get('source_page') or ''} | `{x.get('archive_path') or ''}` |")
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'items={len(items)} output={a.output}')
if __name__=='__main__': main()
