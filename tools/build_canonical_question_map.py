"""Suggest canonical records for duplicate groups without deleting source records."""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path

def score(item):
    return (bool(item.get("answer")) * 4 + bool(item.get("explanation")) * 3 + (len(item.get("options", [])) in (2, 3, 4)) * 2 + len(item.get("stem", "")) / 100000)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("duplicates", type=Path); ap.add_argument("questions", nargs="+", type=Path); ap.add_argument("output", type=Path); args = ap.parse_args()
    by_id = {}
    for path in args.questions:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("items", []):
            by_id[item["question_id"]] = {"source_file": str(path), **item}
    dup = json.loads(args.duplicates.read_text(encoding="utf-8")); groups = []
    for group in dup.get("groups", []):
        candidates = [by_id[x["question_id"]] for x in group.get("items", []) if x["question_id"] in by_id]
        ranked = sorted(candidates, key=score, reverse=True)
        groups.append({"duplicate_group_id": group["duplicate_group_id"], "normalized_stem": group.get("normalized_stem", ""), "recommended_canonical_question_id": ranked[0]["question_id"] if ranked else None, "ranking": [{"question_id": x["question_id"], "source_id": x.get("source_id"), "score": round(score(x), 4), "has_answer": bool(x.get("answer")), "has_explanation": bool(x.get("explanation")), "option_count": len(x.get("options", []))} for x in ranked], "review_status": "needs_human_review"})
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps({"schema_version": 1, "status": "canonical_question_map_candidates", "groups": groups}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); print(f"groups={len(groups)} output={args.output}")

if __name__ == "__main__":
    main()
