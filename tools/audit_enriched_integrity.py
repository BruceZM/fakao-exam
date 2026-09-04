"""Audit enriched question files before rebuilding the legal-exam knowledge base."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ALLOWED_TYPES = {"single_choice", "multiple_choice", "true_false", "short_answer", "case_analysis"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions_dir", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    files = sorted(args.questions_dir.glob("*.enriched.json"))
    errors: list[dict[str, str]] = []
    ids: list[tuple[str, str]] = []
    parsed = 0
    item_count = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            parsed += 1
        except Exception as exc:  # keep auditing other files
            errors.append({"file": str(path), "kind": "invalid_json", "detail": str(exc)})
            continue
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            errors.append({"file": str(path), "kind": "invalid_schema", "detail": "expected object with items list"})
            continue
        for item in data["items"]:
            item_count += 1
            qid = str(item.get("question_id") or "")
            ids.append((qid, str(path)))
            if not qid:
                errors.append({"file": str(path), "kind": "missing_question_id", "detail": ""})
            if not item.get("source_id"):
                errors.append({"file": str(path), "kind": "missing_source_id", "detail": qid})
            if item.get("question_type") not in ALLOWED_TYPES:
                errors.append({"file": str(path), "kind": "invalid_question_type", "detail": f"{qid}:{item.get('question_type')}"})

    counts = Counter(qid for qid, _ in ids if qid)
    duplicates = [
        {"question_id": qid, "count": count, "files": [path for found, path in ids if found == qid]}
        for qid, count in sorted(counts.items()) if count > 1
    ]
    report = {
        "schema_version": 1,
        "status": "validated" if not errors and not duplicates else "needs_review",
        "summary": {
            "files": len(files),
            "parsed_files": parsed,
            "items": item_count,
            "duplicate_question_ids": len(duplicates),
            "errors": len(errors),
        },
        "duplicates": duplicates,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    if report["status"] != "validated":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
