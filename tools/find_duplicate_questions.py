"""Find likely duplicate questions across structured sources by normalized stem."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def normalize(stem: str) -> str:
    value = re.sub(r"\s+", "", stem).lower()
    value = re.sub(r"[（）()【】\[\]，。！？、：:；;\"'“”‘’]", "", value)
    return value


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    groups: dict[str, list[dict]] = defaultdict(list)
    for path in args.inputs:
        for item in json.loads(path.read_text(encoding="utf-8")).get("items", []):
            key = normalize(item.get("stem", ""))
            if key:
                groups[key].append({"question_id": item["question_id"], "source_id": item["source_id"], "stem": item["stem"]})
    duplicates = [{"duplicate_group_id": f"dup-{i:04d}", "normalized_stem": key, "items": values, "review_status": "needs_human_review"} for i, (key, values) in enumerate(groups.items(), 1) if len(values) > 1]
    result = {"schema_version": 1, "status": "duplicate_candidates", "groups": duplicates}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"groups={len(duplicates)} duplicate_items={sum(len(x['items']) for x in duplicates)} output={args.output}")


if __name__ == "__main__":
    main()
