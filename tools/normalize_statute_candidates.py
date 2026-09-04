"""Normalize obvious Chinese statute-name variants without asserting legal validity."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NAME_ALIASES = {
    "中华人民共和国刑法": "刑法",
    "中华人民共和国刑事诉讼法": "刑事诉讼法",
    "中华人民共和国民法典": "民法典",
}


def normalize(value: str) -> str:
    value = re.sub(r"\s+", "", value.strip())
    for old, new in NAME_ALIASES.items():
        value = value.replace(old, new)
    value = value.replace("（", "(").replace("）", ")")
    # Common OCR substitutions inside statute titles.  These are orthographic
    # fixes only; the resulting citation remains subject to legal review.
    value = value.replace("盜窃", "盗窃").replace("間题", "问题").replace("间题", "问题")
    # OCR occasionally duplicates the opening book-title bracket.  Collapse
    # only this unambiguous typographical artifact; legal names and article
    # references remain subject to human legal-version review.
    value = value.replace("《《", "《")
    return value


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = []
    by_normalized: dict[str, dict] = {}
    for item in source.get("items", []):
        if item.get("candidate_type") != "law_article":
            continue
        normalized = normalize(item["candidate"])
        row = by_normalized.get(normalized)
        if row is None:
            row = {"statute_id": f"candidate-{len(result)+1:04d}", "canonical_candidate": normalized, "raw_candidates": [], "question_ids": [], "source_ids": [], "normalization_status": "auto_normalized", "verification_status": "needs_legal_review", "law_version": None, "effective_date": None}
            by_normalized[normalized] = row
            result.append(row)
        if item["candidate"] not in row["raw_candidates"]:
            row["raw_candidates"].append(item["candidate"])
        for key in ("question_ids", "source_ids"):
            for value in item.get(key, []):
                if value not in row[key]:
                    row[key].append(value)
    output = {"schema_version": 1, "status": "normalized_candidates", "items": result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"normalized={len(result)} output={args.output}")


if __name__ == "__main__":
    main()
