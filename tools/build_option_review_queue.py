"""Build a review queue for malformed objective-question option structures."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--quality", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    quality = json.loads(args.quality.read_text(encoding="utf-8"))
    malformed = {
        item["question_id"]: next(
            int(issue.rsplit("_", 1)[1])
            for issue in item.get("issues", [])
            if issue.startswith("option_count_")
        )
        for item in quality.get("items", [])
        if any(issue.startswith("option_count_") for issue in item.get("issues", []))
    }
    rows = con.execute(
        """
        select q.question_id,q.source_id,s.title,s.archive_path,q.source_page,
               q.subject,q.stage,q.question_type,q.answer,q.stem,count(o.option_key) option_count
        from questions q join sources s on s.source_id=q.source_id
        left join options o on o.question_id=q.question_id
        where q.question_type in ('single_choice','multiple_choice')
        group by q.question_id
        having option_count not in (2,3,4)
        order by q.source_id,q.question_id
        """
    ).fetchall()
    by_id = {r["question_id"]: r for r in rows}
    # SQLite enforces unique option keys and can hide duplicated OCR labels;
    # use the raw audit count as the authoritative malformed count.
    missing = [qid for qid in malformed if qid not in by_id]
    if missing:
        placeholders = ",".join("?" for _ in missing)
        extra = con.execute(
            f"select q.question_id,q.source_id,s.title,s.archive_path,q.source_page,q.subject,q.stage,q.question_type,q.answer,q.stem from questions q join sources s on s.source_id=q.source_id where q.question_id in ({placeholders})",
            missing,
        ).fetchall()
        for r in extra:
            by_id[r["question_id"]] = r
    items = [
        {
            "question_id": r["question_id"],
            "source_id": r["source_id"],
            "source_title": r["title"],
            "archive_path": r["archive_path"],
            "source_page": r["source_page"],
            "subject": r["subject"],
            "stage": r["stage"],
            "question_type": r["question_type"],
            "answer": r["answer"],
            "option_count": malformed.get(r["question_id"], r["option_count"] if "option_count" in r.keys() else None),
            "stem_preview": (r["stem"] or "")[:120],
            "status": "needs_manual_option_boundary_review",
        }
        for r in by_id.values()
        if r["question_id"] in malformed
    ]
    result = {
        "schema_version": 1,
        "status": "option_review_queue",
        "summary": {"items": len(items)},
        "items": items,
        "notes": [
            "仅列出客观题选项数不是 2、3 或 4 的记录。",
            "应回看扫描原文恢复选项边界；不得根据答案字母猜测选项文本。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"queued={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
