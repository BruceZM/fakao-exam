"""Build a review queue for questions whose source page is still unknown."""
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
        select q.question_id,q.source_id,s.title,s.archive_path,q.subject,q.stage,q.question_type,q.stem
        from questions q join sources s on s.source_id=q.source_id
        where q.source_page is null order by q.source_id,q.question_id
    """).fetchall()
    items = [{"question_id": r[0], "source_id": r[1], "source_title": r[2], "archive_path": r[3], "subject": r[4], "stage": r[5], "question_type": r[6], "stem_preview": r[7][:120], "status": "needs_manual_page_mapping"} for r in rows]
    result = {"schema_version": 1, "status": "source_page_review_queue", "summary": {"items": len(items)}, "items": items, "notes": ["仅列出尚未定位原始页码的题目；不代表题目内容本身有误。"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"queued={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
