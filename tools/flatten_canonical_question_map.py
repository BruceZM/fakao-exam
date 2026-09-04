"""Flatten duplicate-group recommendations for product queries and assembly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    groups = json.loads(args.input.read_text(encoding="utf-8")).get("groups", [])
    items = []
    for group in groups:
        canonical = group.get("recommended_canonical_question_id")
        for rank, row in enumerate(group.get("ranking", []), 1):
            qid = row["question_id"]
            items.append({
                "question_id": qid,
                "canonical_question_id": canonical,
                "duplicate_group_id": group.get("duplicate_group_id"),
                "is_canonical": qid == canonical,
                "rank": rank,
                "review_status": group.get("review_status", "needs_human_review"),
            })
    result = {"schema_version": 1, "status": "canonical_question_map", "summary": {"groups": len(groups), "mapped_questions": len(items), "duplicate_questions": sum(not x["is_canonical"] for x in items)}, "items": items, "notes": ["主记录是自动排序建议，需人工确认后才能用于正式组卷。"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"groups={len(groups)} mapped_questions={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
