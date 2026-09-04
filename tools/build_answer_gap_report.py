"""Build an actionable answer/explanation gap report from the KB snapshot."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT q.source_id, s.title, q.subject, q.stage, q.question_type,
               COUNT(*) AS total,
               SUM(CASE WHEN q.answer IS NULL OR trim(q.answer) = '' THEN 1 ELSE 0 END) AS missing_answer,
               SUM(CASE WHEN q.explanation IS NULL OR trim(q.explanation) = '' THEN 1 ELSE 0 END) AS missing_explanation
        FROM questions q JOIN sources s ON s.source_id = q.source_id
        GROUP BY q.source_id, s.title, q.subject, q.stage, q.question_type
        ORDER BY missing_answer DESC, missing_explanation DESC, total DESC
        """
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["answer_rate"] = round((item["total"] - item["missing_answer"]) / item["total"], 4)
        item["explanation_rate"] = round((item["total"] - item["missing_explanation"]) / item["total"], 4)
        if item["missing_answer"]:
            item["priority"] = "P0" if item["missing_explanation"] else "P1"
        elif item["missing_explanation"]:
            item["priority"] = "P2"
        else:
            item["priority"] = "complete_candidate"
        items.append(item)
    result = {
        "schema_version": 1,
        "status": "answer_explanation_gap_report",
        "items": items,
        "notes": [
            "优先级只反映字段缺口，不代表答案正确性。",
            "P0/P1 记录应先核对原始扫描页和授权状态，再写入正式产品数据。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"groups={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
