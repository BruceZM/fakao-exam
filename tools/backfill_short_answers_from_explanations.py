"""Use existing model explanations as provisional answers for short answers.

Only fills blank short-answer records with non-trivial explanation text. The
result remains explicitly marked as requiring human review.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean(text: str) -> str:
    text = text.split("===== page-", 1)[0].strip()
    # Remove casual preamble before an explicit explanation label when present.
    m = re.search(r"(?:解析|参考答案)\s*[:：]\s*", text)
    if m and m.start() < 40:
        text = text[m.end():].strip()
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    changed = []
    for item in doc.get("items", []):
        if item.get("question_type") != "short_answer" or (item.get("answer") or "").strip():
            continue
        explanation = clean(item.get("explanation") or "")
        if len(explanation) < 20:
            continue
        item["answer"] = explanation
        item["answer_raw"] = explanation
        item["answer_source"] = "explanation_model_answer"
        item["answer_review_status"] = "needs_human_review"
        changed.append(item["question_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} backfilled={len(changed)} output={args.output}")
    for qid in changed:
        print(qid)


if __name__ == "__main__":
    main()
