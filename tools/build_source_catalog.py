"""Build a reviewable catalog connecting question sources to archive metadata."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    rows = db.execute(
        """SELECT s.source_id, s.title, s.subject, s.stage, s.source_type,
                  s.archive_path, s.license_status, s.review_status,
                  COUNT(q.question_id),
                  SUM(CASE WHEN COALESCE(TRIM(q.answer),'')<>'' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN COALESCE(TRIM(q.explanation),'')<>'' THEN 1 ELSE 0 END)
           FROM sources s LEFT JOIN questions q ON q.source_id=s.source_id
           GROUP BY s.source_id ORDER BY s.subject, s.title"""
    ).fetchall()
    records = []
    for source_id, title, subject, stage, source_type, archive, license, review, total, answered, explained in rows:
        records.append({"source_id": source_id, "title": title, "subject": subject, "stage": stage, "source_type": source_type, "archive_path": archive, "license_status": license, "review_status": review, "question_count": total, "answered_count": answered, "explained_count": explained})
    lines = [
        "# 法考知识库来源目录",
        "",
        "本页由 `tools/build_source_catalog.py` 生成，连接扫描归档、结构化题目和来源审校状态。授权状态为 `unknown` 的来源不得直接进入产品层。",
        "",
        f"来源总数：**{len(rows)}**；题目总数：**{sum(r[8] for r in rows)}**。",
        "",
        "| 来源 | 科目 | 阶段 | 题量 | 答案 | 解析 | 归档目录 | 授权/审校 |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for source_id, title, subject, stage, source_type, archive, license, review, total, answered, explained in rows:
        label = title or source_id
        status = f"{license}/{review}"
        lines.append(f"| {label} (`{source_id}`) | {subject} | {stage} | {total} | {answered} | {explained} | `{archive or '未登记'}` | `{status}` |")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps({"schema_version": 1, "sources": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"sources={len(rows)} questions={sum(r[8] for r in rows)} output={args.output}")


if __name__ == "__main__":
    main()
