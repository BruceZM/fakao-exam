"""Build a source-aware queue for missing explanations."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    c=sqlite3.connect(a.db); c.row_factory=sqlite3.Row
    rows=[]
    for r in c.execute("select q.source_id,s.title,s.archive_path,count(*) total,sum(case when coalesce(trim(q.explanation),'')='' then 1 else 0 end) missing from questions q left join sources s on s.source_id=q.source_id group by q.source_id,s.title,s.archive_path having missing>0 order by missing desc"):
        archive=a.root/r['archive_path'] if r['archive_path'] else None
        text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in archive.glob('ocr.txt')) if archive and archive.exists() else ''
        rows.append({'source_id':r['source_id'],'title':r['title'],'archive_path':r['archive_path'],'total':r['total'],'missing_explanation':r['missing'],'ocr_explanation_markers':text.count('解析'),'recommendation':'核对 OCR/答案解析版后回填' if text.count('解析') else '补充解析版或专家讲解后回填'})
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'schema_version':1,'status':'explanation_acquisition_queue','items':rows,'missing_explanation':sum(x['missing_explanation'] for x in rows)},ensure_ascii=False,indent=2)+'\n')
    md=a.root/'docs/EXPLANATION_ACQUISITION_QUEUE.md'; lines=['# 法考知识库解析获取队列','', '本页按来源汇总缺失解析，并标注已归档 OCR 是否出现解析标记。OCR 有标记不等于已经完成法律核验。','', '| 来源 | 缺失解析 | OCR 解析标记 | 建议 |','|---|---:|---:|---|']
    for x in rows: lines.append(f"| {x['title']} (`{x['source_id']}`) | {x['missing_explanation']} | {x['ocr_explanation_markers']} | {x['recommendation']} |")
    lines += ['',f"当前缺失解析：**{sum(x['missing_explanation'] for x in rows)} 条**。"]
    md.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f"sources={len(rows)} missing_explanations={sum(x['missing_explanation'] for x in rows)} output={a.output}")
if __name__=='__main__': main()
