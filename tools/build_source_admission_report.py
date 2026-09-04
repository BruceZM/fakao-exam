"""Build a source-level admission report for product use."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    sources = json.loads(args.sources.read_text(encoding="utf-8")).get("sources", [])
    items = []
    for source in sources:
        license_status = source.get("license_status", "unknown")
        review_status = source.get("review_status", "unknown")
        admission = license_status == "licensed" and review_status == "reviewed"
        items.append({
            "source_id": source["source_id"],
            "title": source["title"],
            "subject": source.get("subject"),
            "stage": source.get("stage"),
            "source_type": source.get("source_type"),
            "content_status": source.get("content_status"),
            "license_status": license_status,
            "review_status": review_status,
            "product_admission": "admitted" if admission else "blocked_pending_license_or_review",
        })
    result = {
        "schema_version": 1,
        "status": "source_admission_report",
        "summary": {
            "sources": len(items),
            "admitted": sum(x["product_admission"] == "admitted" for x in items),
            "blocked": sum(x["product_admission"] != "admitted" for x in items),
            "license_status": dict(Counter(x["license_status"] for x in items)),
            "content_status": dict(Counter(x["content_status"] for x in items)),
        },
        "items": items,
        "notes": [
            "公开可见或已扫描不等于获得商业使用授权。",
            "只有授权状态为 licensed 且来源已人工审校时，才允许进入产品准入层。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"sources={len(items)} admitted={result['summary']['admitted']} output={args.output}")


if __name__ == "__main__":
    main()
