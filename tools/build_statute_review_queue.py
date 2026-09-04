"""Prioritize normalized statute candidates for legal-version review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for item in source.get("items", []):
        candidate = item.get("canonical_candidate", "")
        flags = []
        if candidate.startswith("《《") or candidate.count("《") != candidate.count("》"):
            flags.append("malformed_brackets")
        if "第" not in candidate:
            flags.append("missing_article_number")
        rows.append({"statute_id": item.get("statute_id"), "canonical_candidate": candidate, "question_ids": item.get("question_ids", []), "source_ids": item.get("source_ids", []), "question_count": len(item.get("question_ids", [])), "flags": flags, "status": "needs_legal_review"})
    rows.sort(key=lambda x: (-x["question_count"], bool(x["flags"]), x["canonical_candidate"]))
    result = {"schema_version": 1, "status": "statute_review_queue", "summary": {"items": len(rows), "flagged": sum(bool(x["flags"]) for x in rows), "questions_referenced": len({q for x in rows for q in x["question_ids"]})}, "items": rows, "notes": ["候选法条仅来自资料中出现的引用；法律名称、条文和适用版本必须由法律专业人员核验。"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(rows)} flagged={result['summary']['flagged']} output={args.output}")


if __name__ == "__main__":
    main()
