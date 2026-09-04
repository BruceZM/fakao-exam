"""Export the KB into objective and subjective JSONL datasets."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def export(con: sqlite3.Connection, stage: str, output: Path, canonical_map: dict[str, dict]) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as fh:
        for row in con.execute("select q.*, s.title as source_title, s.license_status as source_license_status, s.review_status as source_review_status from questions q join sources s on s.source_id=q.source_id where q.stage=? or (?='subjective' and q.stage='objective_subjective_common') order by q.question_id", (stage, stage)):
            names = [d[1] for d in con.execute("pragma table_info(questions)")] + ["source_title", "source_license_status", "source_review_status"]
            item = dict(zip(names, row))
            item["product_admission"] = "admitted" if item["source_license_status"] == "licensed" and item["source_review_status"] == "reviewed" else "blocked_pending_license_or_review"
            item.update(canonical_map.get(item["question_id"], {"canonical_question_id": item["question_id"], "is_canonical_candidate": True, "duplicate_group_id": None}))
            item["options"] = [dict(zip(("key", "text"), x)) for x in con.execute("select option_key,option_text from options where question_id=? order by option_key", (item["question_id"],))]
            item["knowledge_points"] = [x[0] for x in con.execute("select knowledge_point from question_knowledge_points where question_id=? order by knowledge_point", (item["question_id"],))]
            item["statutes"] = [x[0] for x in con.execute("select statute_candidate from question_statutes where question_id=? order by statute_candidate", (item["question_id"],))]
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--canonical-map", type=Path)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    canonical_map = {}
    if args.canonical_map and args.canonical_map.exists():
        canonical_map = {x["question_id"]: {"canonical_question_id": x["canonical_question_id"], "is_canonical_candidate": x["is_canonical"], "duplicate_group_id": x["duplicate_group_id"]} for x in json.loads(args.canonical_map.read_text(encoding="utf-8")).get("items", [])}
    objective = export(con, "objective", args.output_dir / "objective_questions.jsonl", canonical_map)
    subjective = export(con, "subjective", args.output_dir / "subjective_questions.jsonl", canonical_map)
    print(f"objective={objective} subjective={subjective} output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
