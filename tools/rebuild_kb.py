"""Rebuild all derived legal-exam knowledge-base artifacts in one command."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, default=Path("."))
    args = ap.parse_args()
    root = args.project_root.resolve()
    py = sys.executable
    qdir = root / "data/questions"
    enriched = sorted(str(p) for p in qdir.glob("*.enriched.json"))
    if not enriched:
        ap.error("no data/questions/*.enriched.json files found")
    tools = root / "tools"
    data = root / "data"
    prov = data / "provenance"
    run([py, str(tools / "audit_enriched_integrity.py"), str(qdir), str(prov / "enriched_integrity_report.json")])
    run([py, str(tools / "build_material_queue.py"), str(root / "docs_materials"), str(prov / "material_ingestion_queue.json")])
    run([py, str(tools / "build_scan_archive_report.py"), "--materials", str(root / "docs_materials"), "--queue", str(prov / "material_ingestion_queue.json"), "--output", str(prov / "scan_archive_report.json")])
    run([py, str(tools / "build_knowledge_db.py"), "--questions", *enriched, "--sources", str(prov / "sources.json"), "--materials", str(prov / "material_ingestion_queue.json"), "--scanned-root", str(root / "docs_materials/review/scanned"), "--output", str(data / "fakao_knowledge_base.sqlite")])
    run([py, str(tools / "audit_archive_mappings.py"), "--root", str(root), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "archive_mapping_audit.json")])
    run([py, str(tools / "audit_question_data.py"), *enriched, "--output", str(prov / "question_quality_report.json")])
    run([py, str(tools / "build_review_queue.py"), str(prov / "question_quality_report.json"), str(prov / "review_queue.json")])
    run([py, str(tools / "build_kb_status_report.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "knowledge_base_readiness_report.json")])
    run([py, str(tools / "build_review_priority.py"), "--readiness", str(prov / "knowledge_base_readiness_report.json"), "--output", str(root / "docs/REVIEW_PRIORITY.md")])
    run([py, str(tools / "build_source_catalog.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(root / "docs/SOURCE_CATALOG.md"), "--json-output", str(prov / "source_catalog.json")])
    run([py, str(tools / "build_reference_subject_catalog.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "reference_subject_catalog.json"), "--markdown", str(root / "docs/REFERENCE_SUBJECT_CATALOG.md")])
    run([py, str(tools / "build_knowledge_point_review_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "knowledge_point_review_queue.json")])
    run([py, str(tools / "build_knowledge_coverage_report.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--taxonomy", str(data / "knowledge_points/taxonomy.json"), "--output", str(prov / "knowledge_coverage_report.json")])
    run([py, str(tools / "build_answer_gap_report.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "answer_explanation_gap_report.json")])
    run([py, str(tools / "audit_explanation_provenance.py"), "--questions-dir", str(qdir), "--sources", str(prov / "sources.json"), "--output", str(prov / "explanation_provenance_audit.json")])
    run([py, str(tools / "build_explanation_provenance_review.py"), "--audit", str(prov / "explanation_provenance_audit.json"), "--output", str(root / "docs/EXPLANATION_PROVENANCE_REVIEW.md")])
    run([py, str(tools / "build_explanation_acquisition_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--root", str(root), "--output", str(prov / "explanation_acquisition_queue.json")])
    run([py, str(tools / "build_answer_acquisition_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(root / "docs/ANSWER_ACQUISITION_QUEUE.md"), "--external-links", str(prov / "external_answer_link_candidates.json")])
    run([py, str(tools / "build_missing_answer_manifest.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "missing_answer_manifest.json")])
    run([py, str(tools / "export_review_batch.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--limit", "50", "--output", str(prov / "review_batch_missing_answer_001.json")])
    run([py, str(tools / "export_review_batch.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--limit", "50", "--offset", "50", "--output", str(prov / "review_batch_missing_answer_002.json")])
    for number, offset in ((3, 100), (4, 150), (5, 200)):
        run([py, str(tools / "export_review_batch.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--limit", "50", "--offset", str(offset), "--output", str(prov / f"review_batch_missing_answer_{number:03d}.json")])
    run([py, str(tools / "build_answer_review_batches_markdown.py"), "--provenance", str(prov), "--output", str(root / "docs/ANSWER_REVIEW_BATCHES.md")])
    run([py, str(tools / "build_answer_conflict_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "answer_conflict_queue.json")])
    run([py, str(tools / "build_option_review_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--quality", str(prov / "question_quality_report.json"), "--output", str(prov / "option_review_queue.json")])
    run([py, str(tools / "build_source_page_review_queue.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "source_page_review_queue.json")])
    run([py, str(tools / "build_year_candidates.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "year_candidates.json")])
    run([py, str(tools / "build_source_admission_report.py"), "--sources", str(prov / "sources.json"), "--output", str(prov / "source_admission_report.json")])
    run([py, str(tools / "build_license_review_markdown.py"), "--input", str(prov / "source_admission_report.json"), "--output", str(root / "docs/LICENSE_REVIEW_QUEUE.md")])
    run([py, str(tools / "build_statute_candidates.py"), *enriched, "--output", str(data / "statutes/citation_candidates.json")])
    run([py, str(tools / "normalize_statute_candidates.py"), str(data / "statutes/citation_candidates.json"), str(data / "statutes/normalized_candidates.json")])
    run([py, str(tools / "build_statute_review_queue.py"), str(data / "statutes/normalized_candidates.json"), str(prov / "statute_review_queue.json")])
    run([py, str(tools / "find_duplicate_questions.py"), *enriched, "--output", str(prov / "duplicate_question_candidates.json")])
    run([py, str(tools / "build_canonical_question_map.py"), str(prov / "duplicate_question_candidates.json"), *enriched, str(prov / "canonical_question_map_candidates.json")])
    run([py, str(tools / "flatten_canonical_question_map.py"), str(prov / "canonical_question_map_candidates.json"), str(prov / "canonical_question_map.json")])
    run([py, str(tools / "extract_rubric_candidates.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(data / "rubrics/candidates.json")])
    run([py, str(tools / "audit_rubrics.py"), "--rubrics", str(data / "rubrics/candidates.json"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "rubric_audit.json")])
    run([py, str(tools / "build_rubric_review_markdown.py"), "--input", str(data / "rubrics/candidates.json"), "--output", str(root / "docs/RUBRIC_REVIEW_QUEUE.md")])
    run([py, str(tools / "validate_knowledge_base.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--project-root", str(root), "--output", str(prov / "knowledge_base_integrity_report.json")])
    run([py, str(tools / "export_question_stages.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--canonical-map", str(prov / "canonical_question_map.json"), "--output-dir", str(data / "exports")])
    run([py, str(tools / "export_canonical_questions.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--canonical-map", str(prov / "canonical_question_map.json"), "--output-dir", str(data / "exports")])
    run([py, str(tools / "build_field_coverage_report.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "field_coverage_report.json")])
    run([py, str(tools / "build_source_answer_availability.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--scanned-root", str(root / "docs_materials/review/scanned"), "--output", str(prov / "source_answer_availability.json")])
    run([py, str(tools / "build_answer_type_candidates.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "answer_type_candidates.json")])
    run([py, str(tools / "build_product_admission_snapshot.py"), "--db", str(data / "fakao_knowledge_base.sqlite"), "--output", str(prov / "product_admission_snapshot.json")])
    run([py, str(tools / "smoke_test_kb.py"), "--root", str(root)])
    run([py, str(tools / "build_app_bundle.py"), "--exports-dir", str(data / "exports"), "--output", str(root / "app/data/questions.json")])
    run([py, str(tools / "build_snapshot_manifest.py"), "--project-root", str(root), "--output", str(prov / "kb_snapshot_manifest.json")])
    run([py, str(tools / "build_review_backlog_markdown.py"), "--provenance", str(prov), "--output", str(root / "docs/REVIEW_BACKLOG.md")])
    run([py, str(tools / "build_kb_status_markdown.py"), "--provenance", str(prov), "--output", str(root / "docs/KB_STATUS.md")])
    print("rebuild_status=ok")


if __name__ == "__main__":
    main()
