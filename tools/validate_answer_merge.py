"""Validate an order-based question/answer merge using normalized stems."""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def norm(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", value.lower())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("answers", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    qs = json.loads(args.questions.read_text(encoding="utf-8")).get("items", [])
    ans = json.loads(args.answers.read_text(encoding="utf-8")).get("items", [])
    checks = []
    for i, (q, a) in enumerate(zip(qs, ans), 1):
        qn, an = norm(q.get("stem", "")), norm(a.get("stem", ""))
        score = SequenceMatcher(None, qn, an).ratio() if qn and an else 0.0
        checks.append({"ordinal": i, "question_id": q["question_id"], "similarity": round(score, 4), "status": "match" if score >= 0.65 else "mismatch"})
    result = {"schema_version": 1, "status": "answer_merge_validation", "question_count": len(qs), "answer_count": len(ans), "checks": checks, "summary": {"matched": sum(x["status"] == "match" for x in checks), "mismatched": sum(x["status"] == "mismatch" for x in checks), "unmatched_questions": max(0, len(qs) - len(ans))}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"matched={result['summary']['matched']} mismatched={result['summary']['mismatched']} unmatched_questions={result['summary']['unmatched_questions']} output={args.output}")


if __name__ == "__main__":
    main()
