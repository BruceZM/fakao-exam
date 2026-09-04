"""Query the legal-exam knowledge-base snapshot for product prototyping."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--keyword")
    ap.add_argument("--subject")
    ap.add_argument("--stage", choices=["objective", "subjective"])
    ap.add_argument("--question-type")
    ap.add_argument("--documents", action="store_true", help="search archived OCR documents instead of questions")
    ap.add_argument("--canonical-only", action="store_true", help="exclude non-canonical duplicate candidates")
    ap.add_argument("--canonical-map", type=Path, default=Path("data/provenance/canonical_question_map.json"))
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    if args.limit < 1 or args.limit > 200:
        ap.error("--limit must be between 1 and 200")
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    if args.documents:
        if not args.keyword:
            ap.error("--documents requires --keyword")
        rows = con.execute("SELECT path,title,substr(ocr_text,1,500) AS preview FROM reference_documents_fts WHERE reference_documents_fts MATCH ? LIMIT ?", (args.keyword, args.limit)).fetchall()
        print(json.dumps({"count": len(rows), "items": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
        return
    clauses, params = [], []
    if args.canonical_only:
        if not args.canonical_map.exists():
            ap.error(f"canonical map not found: {args.canonical_map}")
        mapping = json.loads(args.canonical_map.read_text(encoding="utf-8"))
        canonical_ids = [x["question_id"] for x in mapping.get("items", []) if x.get("is_canonical")]
        if canonical_ids:
            clauses.append("q.question_id IN (" + ",".join("?" for _ in canonical_ids) + ")")
            params.extend(canonical_ids)
    if args.keyword:
        # FTS5 默认 tokenizer 对部分中文短词切分不稳定；先走 FTS，查询无结果时由 LIKE 回退。
        fts_ids = [r[0] for r in con.execute("SELECT question_id FROM questions_fts WHERE questions_fts MATCH ?", (args.keyword,)).fetchall()]
        if fts_ids:
            clauses.append("q.question_id IN (" + ",".join("?" for _ in fts_ids) + ")")
            params.extend(fts_ids)
        else:
            clauses.append("(q.stem LIKE ? OR q.explanation LIKE ?)")
            params.extend([f"%{args.keyword}%", f"%{args.keyword}%"])
    if args.subject:
        clauses.append("q.subject = ?"); params.append(args.subject)
    if args.stage == "objective":
        clauses.append("q.stage = 'objective'")
    elif args.stage == "subjective":
        clauses.append("q.stage IN ('subjective','objective_subjective_common')")
    if args.question_type:
        clauses.append("q.question_type = ?"); params.append(args.question_type)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = con.execute(f"SELECT q.*, s.title source_title, s.license_status source_license_status, s.review_status source_review_status FROM questions q JOIN sources s ON s.source_id=q.source_id{where} ORDER BY q.question_id LIMIT ?", (*params, args.limit)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        qid = item["question_id"]
        item["options"] = [{"key": k, "text": t} for k, t in con.execute("SELECT option_key,option_text FROM options WHERE question_id=? ORDER BY option_key", (qid,))]
        item["knowledge_points"] = [x[0] for x in con.execute("SELECT knowledge_point FROM question_knowledge_points WHERE question_id=? ORDER BY knowledge_point", (qid,))]
        item["statutes"] = [x[0] for x in con.execute("SELECT statute_candidate FROM question_statutes WHERE question_id=? ORDER BY statute_candidate", (qid,))]
        result.append(item)
    print(json.dumps({"count": len(result), "items": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
