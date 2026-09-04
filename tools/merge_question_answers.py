"""Merge answer/解析 records into a question-only draft by source order."""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("answers", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    qdoc = json.loads(args.questions.read_text(encoding="utf-8"))
    adoc = json.loads(args.answers.read_text(encoding="utf-8"))
    answers = adoc.get("items", [])
    def norm(value: str) -> str:
        return re.sub(r"[^\w\u4e00-\u9fff]", "", value.lower())

    question_items = qdoc.get("items", [])
    # Greedily assign the strongest global stem matches first, avoiding
    # early low-quality matches consuming an answer needed later.
    pairs = sorted(((SequenceMatcher(None, norm(q.get("stem", "")), norm(a.get("stem", ""))).ratio(), qi, ai)
                    for qi, q in enumerate(question_items) for ai, a in enumerate(answers)), reverse=True)
    assignments: dict[int, tuple[int, float]] = {}
    used: set[int] = set()
    for score, qi, ai in pairs:
        if score < 0.55 or qi in assignments or ai in used:
            continue
        assignments[qi] = (ai, score)
        used.add(ai)
    merged = []
    for index, item in enumerate(question_items):
        out = dict(item)
        answer_assignment = assignments.get(index)
        if answer_assignment is not None:
            answer_index, score = answer_assignment
            answer = answers[answer_index]
            used.add(answer_index)
            out["answer"] = answer.get("answer")
            out["answer_raw"] = answer.get("answer_raw", "")
            out["explanation"] = answer.get("explanation", "")
            out["answer_source_id"] = answer.get("source_id")
            out["answer_merge_status"] = "merged_by_stem_similarity"
            out["answer_merge_similarity"] = round(score, 4)
        else:
            out["answer_merge_status"] = "missing_answer_record"
            out["answer_merge_similarity"] = 0.0
        merged.append(out)
    result = {"schema_version": 1, "status": "merged_draft", "items": merged, "merge_report": {"questions": len(qdoc.get("items", [])), "answers": len(answers), "merged": len(used), "unmatched_answers": len(answers) - len(used)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"questions={len(qdoc.get('items', []))} answers={len(answers)} merged={len(used)} output={args.output}")


if __name__ == "__main__":
    main()
