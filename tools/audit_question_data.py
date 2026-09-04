"""Audit parsed question drafts for structural and OCR-quality issues."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# These markers are publisher/page artifacts. “二维码” can occur legitimately
# inside a fact pattern or cited case and is therefore not an OCR error marker.
BAD_TOKENS = ("GYUAN", "FANGY", "众合教育", "更多法考备考资料")
NON_ANSWER_RAW_TOKENS = ("成功的路上从不", "法条填空题", "获取全年课程更新")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    report = []
    totals = {"items": 0, "issues": 0, "missing_answer": 0, "option_count": 0, "ocr_residue": 0, "answer_text_residue": 0}
    by_issue = {}
    by_source = {}
    for path in args.inputs:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("items", []):
            totals["items"] += 1
            issues: list[str] = []
            options = item.get("options", [])
            if not item.get("stem", "").strip():
                issues.append("empty_stem")
            if item.get("answer") is None:
                issues.append("missing_answer")
                totals["missing_answer"] += 1
            if item.get("question_type") in ("single_choice", "multiple_choice") and len(options) not in (2, 3, 4):
                issues.append(f"option_count_{len(options)}")
                totals["option_count"] += 1
            answer = (item.get("answer") or "").strip().upper()
            if answer and item.get("question_type") == "single_choice" and (len(answer) != 1 or answer not in "ABCD"):
                issues.append("answer_choice_mismatch")
                totals.setdefault("answer_choice_mismatch", 0)
                totals["answer_choice_mismatch"] += 1
            if answer and item.get("question_type") == "multiple_choice" and (not 1 <= len(answer) <= 4 or any(ch not in "ABCD" for ch in answer) or len(set(answer)) != len(answer)):
                issues.append("answer_choice_mismatch")
                totals.setdefault("answer_choice_mismatch", 0)
                totals["answer_choice_mismatch"] += 1
            searchable = json.dumps(item, ensure_ascii=False)
            if any(token in searchable for token in BAD_TOKENS):
                issues.append("ocr_residue")
                totals["ocr_residue"] += 1
            if not answer and any(token in (item.get("answer_raw") or "") for token in NON_ANSWER_RAW_TOKENS):
                issues.append("answer_raw_nonanswer_residue")
                totals.setdefault("answer_raw_nonanswer_residue", 0)
                totals["answer_raw_nonanswer_residue"] += 1
            if item.get("question_type") in ("short_answer", "case_analysis") and (len(answer) > 500 or "===== page-" in answer):
                issues.append("answer_text_residue")
                totals["answer_text_residue"] += 1
            if issues:
                totals["issues"] += len(issues)
                for issue in issues:
                    by_issue[issue] = by_issue.get(issue, 0) + 1
                source = item.get("source_id") or "unknown"
                by_source.setdefault(source, {"issue_items": 0, "issues": 0})
                by_source[source]["issue_items"] += 1
                by_source[source]["issues"] += len(issues)
                report.append({"question_id": item["question_id"], "source_file": str(path), "issues": issues, "review_status": item.get("review_status")})
    result = {"schema_version": 1, "summary": totals, "by_issue": dict(sorted(by_issue.items())), "by_source": dict(sorted(by_source.items(), key=lambda kv: (-kv[1]["issues"], kv[0]))), "items": report}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={totals['items']} issue_items={len(report)} issues={totals['issues']} output={args.output}")


if __name__ == "__main__":
    main()
