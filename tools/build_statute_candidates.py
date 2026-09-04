"""Build a deduplicated statute-citation candidate index from enriched drafts."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    refs: dict[str, dict] = defaultdict(lambda: {"question_ids": [], "source_ids": []})
    for path in args.inputs:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("items", []):
            for ref in item.get("statutes", []):
                entry = refs[ref]
                entry["question_ids"].append(item["question_id"])
                if item.get("source_id") not in entry["source_ids"]:
                    entry["source_ids"].append(item["source_id"])
    items = []
    for candidate, meta in sorted(refs.items()):
        if "第" in candidate and "条" in candidate:
            candidate_type = "law_article"
        elif any(word in candidate for word in ("解释", "规定", "意见", "批复", "答复")):
            candidate_type = "judicial_document"
        else:
            candidate_type = "reference_material"
        items.append({
            "candidate": candidate,
            "candidate_type": candidate_type,
            "question_ids": sorted(set(meta["question_ids"])),
            "source_ids": sorted(set(meta["source_ids"])),
            "normalization_status": "needs_legal_review",
            "law_version": None,
            "effective_date": None,
        })
    result = {"schema_version": 1, "status": "candidate_index", "items": items}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"candidates={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
