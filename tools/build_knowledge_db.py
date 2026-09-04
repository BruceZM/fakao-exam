"""Build a queryable SQLite knowledge-base snapshot from enriched question JSON."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE questions (
  question_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  source_question_id TEXT,
  year INTEGER,
  stage TEXT NOT NULL,
  subject TEXT NOT NULL,
  question_type TEXT NOT NULL,
  stem TEXT NOT NULL,
  answer TEXT,
  answer_raw TEXT,
  explanation TEXT,
  source_page INTEGER,
  source_page_status TEXT,
  content_status TEXT NOT NULL,
  review_status TEXT NOT NULL
);
CREATE TABLE options (
  question_id TEXT NOT NULL REFERENCES questions(question_id),
  option_key TEXT NOT NULL,
  option_text TEXT NOT NULL,
  PRIMARY KEY(question_id, option_key)
);
CREATE TABLE question_knowledge_points (
  question_id TEXT NOT NULL REFERENCES questions(question_id),
  knowledge_point TEXT NOT NULL,
  source TEXT NOT NULL,
  review_status TEXT NOT NULL,
  PRIMARY KEY(question_id, knowledge_point)
);
CREATE TABLE question_statutes (
  question_id TEXT NOT NULL REFERENCES questions(question_id),
  statute_candidate TEXT NOT NULL,
  link_status TEXT NOT NULL,
  PRIMARY KEY(question_id, statute_candidate)
);
CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  subject TEXT NOT NULL,
  stage TEXT NOT NULL,
  source_type TEXT NOT NULL,
  archive_path TEXT NOT NULL,
  license_status TEXT NOT NULL,
  review_status TEXT NOT NULL
);
CREATE TABLE materials (
  path TEXT PRIMARY KEY,
  extension TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE TABLE reference_documents (
  path TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  ocr_text TEXT NOT NULL,
  document_status TEXT NOT NULL
);
CREATE INDEX idx_questions_source ON questions(source_id);
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_stage ON questions(stage);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_qkp_point ON question_knowledge_points(knowledge_point);
CREATE INDEX idx_qstatute_candidate ON question_statutes(statute_candidate);
CREATE INDEX idx_materials_status ON materials(status);
CREATE VIRTUAL TABLE questions_fts USING fts5(
  question_id UNINDEXED,
  subject,
  stem,
  explanation,
  content='questions',
  content_rowid='rowid'
);
CREATE VIRTUAL TABLE reference_documents_fts USING fts5(
  path UNINDEXED,
  title,
  ocr_text,
  content='reference_documents',
  content_rowid='rowid'
);
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", nargs="+", type=Path, required=True)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--materials", type=Path, help="material_ingestion_queue.json")
    ap.add_argument("--scanned-root", type=Path, help="docs_materials/review/scanned")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(args.output)
    db.executescript("DROP TABLE IF EXISTS reference_documents_fts; DROP TABLE IF EXISTS questions_fts; DROP TABLE IF EXISTS question_statutes; DROP TABLE IF EXISTS question_knowledge_points; DROP TABLE IF EXISTS options; DROP TABLE IF EXISTS questions; DROP TABLE IF EXISTS reference_documents; DROP TABLE IF EXISTS materials; DROP TABLE IF EXISTS sources;" + SCHEMA)
    source_doc = json.loads(args.sources.read_text(encoding="utf-8"))
    db.executemany("INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (s["source_id"], s["title"], s["subject"], s["stage"], s["source_type"], s["archive_path"], s["license_status"], s["review_status"])
        for s in source_doc["sources"]
    ])
    if args.materials:
        material_doc = json.loads(args.materials.read_text(encoding="utf-8"))
        db.executemany("INSERT INTO materials VALUES (?, ?, ?, ?)", [
            (m["path"], m.get("extension", ""), m["sha256"], m["status"])
            for m in material_doc.get("items", [])
        ])
    if args.scanned_root and args.scanned_root.exists():
        docs = []
        for ocr_path in sorted(args.scanned_root.glob("*/ocr.txt")):
            docs.append((str(ocr_path.relative_to(args.scanned_root.parent.parent.parent)), ocr_path.parent.name, ocr_path.read_text(encoding="utf-8", errors="replace"), "ocr_archive"))
        db.executemany("INSERT INTO reference_documents VALUES (?, ?, ?, ?)", docs)
    qcount = 0
    for path in args.questions:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("items", []):
            db.execute("INSERT OR REPLACE INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                item["question_id"], item["source_id"], item.get("source_question_id"), item.get("year"), item["stage"], item["subject"], item["question_type"], item["stem"], item.get("answer"), item.get("answer_raw"), item.get("explanation", ""), item.get("source_page"), item.get("source_page_status", "unknown"), item.get("content_status", "parsed"), item.get("review_status", "needs_human_review")))
            db.executemany("INSERT OR REPLACE INTO options VALUES (?, ?, ?)", [(item["question_id"], x["key"], x["text"]) for x in item.get("options", [])])
            db.executemany("INSERT OR REPLACE INTO question_knowledge_points VALUES (?, ?, ?, ?)", [(item["question_id"], x["name"], x.get("source", "unknown"), x.get("review_status", "needs_human_review")) for x in item.get("knowledge_points", [])])
            db.executemany("INSERT OR REPLACE INTO question_statutes VALUES (?, ?, ?)", [(item["question_id"], x, item.get("statute_link_status", "unknown")) for x in item.get("statutes", [])])
            qcount += 1
    db.commit()
    db.execute("INSERT INTO questions_fts(rowid, question_id, subject, stem, explanation) SELECT rowid, question_id, subject, stem, explanation FROM questions")
    db.commit()
    db.execute("INSERT INTO reference_documents_fts(rowid, path, title, ocr_text) SELECT rowid, path, title, ocr_text FROM reference_documents")
    db.commit()
    counts = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("sources", "materials", "reference_documents", "questions", "options", "question_knowledge_points", "question_statutes", "questions_fts")}
    db.close()
    print(f"questions_loaded={qcount} counts={counts} output={args.output}")


if __name__ == "__main__":
    main()
