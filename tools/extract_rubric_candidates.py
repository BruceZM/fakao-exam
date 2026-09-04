"""Extract explicit score-point snippets from subjective answers."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


POINT_RE = re.compile(r"([^。；\n]{2,120}?)[（(]\s*(\d+)\s*分[）)]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    rows = con.execute(
        "select question_id,source_id,subject,question_type,answer from questions "
        "where stage in ('subjective','objective_subjective_common') and answer is not null and trim(answer)<>''"
    ).fetchall()
    items = []
    for qid, sid, subject, qtype, answer in rows:
        for idx, match in enumerate(POINT_RE.finditer(answer), 1):
            text = match.group(1).strip(" ：:，,；;\t")
            if not text:
                continue
            items.append({
                "rubric_id": f"{qid}-point-{idx:02d}",
                "question_id": qid,
                "source_id": sid,
                "subject": subject,
                "question_type": qtype,
                "point_text": text,
                "score": int(match.group(2)),
                "extraction_status": "explicit_from_answer",
                "review_status": "needs_legal_expert_review",
            })
    result = {
        "schema_version": 1,
        "status": "rubric_candidates",
        "items": items,
        "notes": [
            "评分点仅从答案中的显式分值标记抽取，不代表完整评分标准。",
            "正式主观题评分前仍需按题目、法律版本和官方评分口径人工审校。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"questions={len(rows)} rubric_points={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
