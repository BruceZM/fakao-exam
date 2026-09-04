"""Build subject/knowledge-point coverage report against the local taxonomy."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--db", type=Path, required=True); ap.add_argument("--taxonomy", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    taxonomy = json.loads(args.taxonomy.read_text(encoding="utf-8"))["subjects"]
    db = sqlite3.connect(args.db)
    rows = db.execute("SELECT q.subject, k.knowledge_point, COUNT(DISTINCT q.question_id) FROM questions q JOIN question_knowledge_points k ON k.question_id=q.question_id GROUP BY q.subject,k.knowledge_point").fetchall()
    actual: dict[str, dict[str, int]] = {}
    for subject, point, count in rows: actual.setdefault(subject, {})[point] = count
    subjects = {}
    for subject, planned in taxonomy.items():
        counts = actual.get(subject, {})
        subjects[subject] = {"question_count": db.execute("SELECT COUNT(*) FROM questions WHERE subject=?", (subject,)).fetchone()[0], "planned_points": len(planned), "covered_points": sum(1 for p in planned if counts.get(p, 0) > 0), "uncovered_points": [p for p in planned if counts.get(p, 0) == 0], "point_counts": {p: counts.get(p, 0) for p in planned if counts.get(p, 0) > 0}}
    report = {"schema_version": 1, "status": "coverage_snapshot", "subjects": subjects}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 法考知识点覆盖报告", "", "本页由 `tools/build_knowledge_coverage_report.py` 生成。覆盖指当前题库至少有一道题关联该候选知识点，不等同于完整覆盖官方大纲。", "", "| 科目 | 题量 | 规划知识点 | 已覆盖 | 未覆盖 |", "|---|---:|---:|---:|---|"]
    for subject, info in subjects.items(): lines.append(f"| {subject} | {info['question_count']} | {info['planned_points']} | {info['covered_points']} | {', '.join(info['uncovered_points']) or '无'} |")
    md = args.output.with_suffix('.md'); md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"subjects={len(subjects)} output={args.output}")


if __name__ == "__main__": main()
