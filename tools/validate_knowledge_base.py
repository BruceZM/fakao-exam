"""Validate relational and provenance integrity of the legal-exam KB snapshot."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    required = {"sources", "materials", "reference_documents", "questions", "options", "question_knowledge_points", "question_statutes", "questions_fts", "reference_documents_fts"}
    errors = []
    errors.extend(f"missing_table:{t}" for t in sorted(required - tables))
    missing_sources = con.execute("select count(*) from questions q left join sources s on s.source_id=q.source_id where s.source_id is null").fetchone()[0]
    orphan_options = con.execute("select count(*) from options o left join questions q on q.question_id=o.question_id where q.question_id is null").fetchone()[0]
    orphan_knowledge_links = con.execute("select count(*) from question_knowledge_points k left join questions q on q.question_id=k.question_id where q.question_id is null").fetchone()[0]
    orphan_statute_links = con.execute("select count(*) from question_statutes s left join questions q on q.question_id=s.question_id where q.question_id is null").fetchone()[0]
    duplicate_ids = con.execute("select count(*) from (select question_id from questions group by question_id having count(*)>1)").fetchone()[0]
    q_count = con.execute("select count(*) from questions").fetchone()[0]
    fts_count = con.execute("select count(*) from questions_fts").fetchone()[0]
    ref_count = con.execute("select count(*) from reference_documents").fetchone()[0]
    ref_fts_count = con.execute("select count(*) from reference_documents_fts").fetchone()[0]
    for name, value in [("missing_sources", missing_sources), ("orphan_options", orphan_options), ("orphan_knowledge_links", orphan_knowledge_links), ("orphan_statute_links", orphan_statute_links), ("duplicate_ids", duplicate_ids), ("fts_count_mismatch", int(q_count != fts_count))]:
        if value:
            errors.append(f"{name}:{value}")
    if ref_count != ref_fts_count:
        errors.append(f"reference_fts_count_mismatch:{ref_count}!={ref_fts_count}")
    missing_archives = []
    for path, in con.execute("select archive_path from sources"):
        if not (args.project_root / path).exists():
            missing_archives.append(path)
    if missing_archives:
        errors.append(f"missing_archive_paths:{len(missing_archives)}")
    result = {"schema_version": 1, "status": "validated" if not errors else "validation_failed", "errors": errors, "metrics": {"questions": q_count, "fts_rows": fts_count, "reference_documents": ref_count, "reference_documents_fts_rows": ref_fts_count, "sources": con.execute("select count(*) from sources").fetchone()[0], "materials": con.execute("select count(*) from materials").fetchone()[0], "orphan_options": orphan_options, "orphan_knowledge_links": orphan_knowledge_links, "orphan_statute_links": orphan_statute_links, "missing_archive_paths": len(missing_archives)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={result['status']} errors={len(errors)} output={args.output}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
