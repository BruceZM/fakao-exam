"""Build a review queue for questions without knowledge-point links."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    rows = con.execute("""
        SELECT q.question_id, q.source_id, q.subject, q.stage, q.question_type,
               q.source_page, substr(q.stem, 1, 240)
        FROM questions q
        WHERE NOT EXISTS (
          SELECT 1 FROM question_knowledge_points k WHERE k.question_id=q.question_id
        )
        ORDER BY q.subject, q.source_id, q.question_id
    """).fetchall()
    items = [{"question_id": r[0], "source_id": r[1], "subject": r[2], "stage": r[3], "question_type": r[4], "source_page": r[5], "stem_preview": r[6], "status": "needs_manual_knowledge_point_mapping"} for r in rows]
    by_subject = {}
    for item in items:
        by_subject[item["subject"]] = by_subject.get(item["subject"], 0) + 1
    result = {"schema_version": 1, "status": "knowledge_point_review_queue", "summary": {"items": len(items), "by_subject": by_subject}, "items": items, "notes": ["仅列出当前没有知识点关联的题目。自动标签和人工标签均需结合考试大纲、题干和解析复核。"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"queued={len(items)} by_subject={by_subject} output={args.output}")


if __name__ == "__main__":
    main()
