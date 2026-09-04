"""Build conservative year candidates from explicit years in question stems."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


YEAR_RE = re.compile(r"(?<!\d)(20(?:1[5-9]|2[0-9]))年")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    rows = con.execute("select question_id,source_id,subject,stage,stem from questions where year is null").fetchall()
    items = []
    for qid, sid, subject, stage, stem in rows:
        matches = list(YEAR_RE.finditer(stem))
        years = sorted({int(x.group(1)) for x in matches})
        if len(years) == 1:
            match = next(x for x in matches if int(x.group(1)) == years[0])
            start = max(0, match.start() - 36)
            end = min(len(stem), match.end() + 44)
            excerpt = stem[start:end].replace("\n", " ")
            nearby = stem[match.start():min(len(stem), match.end() + 8)]
            kind = "scenario_date" if re.match(r"20(?:1[5-9]|2[0-9])年\s*\d{1,2}月", nearby) else "explicit_year_in_stem"
            items.append({"question_id": qid, "source_id": sid, "subject": subject, "stage": stage, "year_candidate": years[0], "evidence": "single explicit year in stem", "evidence_excerpt": excerpt, "candidate_kind": kind, "status": "needs_manual_year_review"})
    result = {"schema_version": 1, "status": "year_candidates", "summary": {"questions_without_year": len(rows), "single_year_candidates": len(items)}, "items": items, "notes": ["候选年份来自题干中的唯一明确年份，不代表已确认考试年份。", "含多个年份或仅在来源标题出现年份的题目不在此清单中。"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"without_year={len(rows)} candidates={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
