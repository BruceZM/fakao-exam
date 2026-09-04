"""Backfill only explicitly stated answers found in existing explanations.

This is intentionally conservative: it never infers an answer from reasoning or
option text, and it never overwrites a non-empty answer.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ANSWER_RE = re.compile(r"(?:本题|该题|此题)?答案(?:为|是)\s*[:：]?\s*([A-DＡ-Ｄ]{1,4})", re.I)
TEXT_ANSWER_RE = re.compile(r"(?:^|\s)答案\s*[:：]\s*([^。；\n]{1,80})")
FULLWIDTH = str.maketrans("ＡＢＣＤ", "ABCD")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    changed = []
    for item in doc.get("items", []):
        if (item.get("answer") or "").strip():
            continue
        explanation = item.get("explanation") or ""
        matches = ANSWER_RE.findall(explanation)
        if matches:
            answer = matches[-1].translate(FULLWIDTH).upper()
            if any(ch not in "ABCD" for ch in answer):
                continue
        else:
            text_matches = TEXT_ANSWER_RE.findall(explanation)
            if not text_matches:
                continue
            answer = text_matches[-1].strip()
            if not answer or len(answer) > 80:
                continue
        item["answer"] = answer
        item["answer_raw"] = answer
        item["answer_source"] = "explanation_explicit"
        item["answer_review_status"] = "needs_human_review"
        changed.append(item["question_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} backfilled={len(changed)} output={args.output}")
    for question_id in changed:
        print(question_id)


if __name__ == "__main__":
    main()
