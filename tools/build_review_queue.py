"""Turn question-quality findings into an explicit human-review queue."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audit", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    report = json.loads(args.audit.read_text(encoding="utf-8"))
    queue = []
    for index, item in enumerate(report.get("items", []), 1):
        queue.append({
            "review_id": f"review-{index:04d}",
            "question_id": item["question_id"],
            "source_file": item["source_file"],
            "issues": item["issues"],
            "checks": ["stem", "options", "answer", "explanation", "knowledge_points", "statutes", "source_page", "license_status"],
            "review_status": "queued",
            "reviewer": None,
            "review_notes": "",
        })
    result = {"schema_version": 1, "status": "open_review_queue", "items": queue}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"queued={len(queue)} output={args.output}")


if __name__ == "__main__":
    main()
