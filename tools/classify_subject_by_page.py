"""Infer subject labels for mixed-source questions from OCR page headings."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SUBJECTS = ("行政法", "刑法", "理论法", "刑诉法", "民法", "民诉法", "商经知", "三国法")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("ocr", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.questions.read_text(encoding="utf-8"))
    raw = args.ocr.read_text(encoding="utf-8", errors="replace")
    page_subject: dict[int, str] = {}
    chunks = re.split(r"===== page-(\d+)\.png =====", raw)
    for i in range(1, len(chunks), 2):
        page = int(chunks[i])
        content = chunks[i + 1]
        page_subject[page] = next((subject for subject in SUBJECTS if re.search(rf"(?m)^\s*{re.escape(subject)}\s*$", content)), "")
    changed = 0
    for item in doc.get("items", []):
        page = item.get("source_page")
        subject = page_subject.get(page, "")
        if subject and item.get("subject") in ("法考", "综合客观题"):
            item["subject"] = subject
            item["subject_status"] = "inferred_from_page_heading"
            changed += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} classified={changed} output={args.output}")


if __name__ == "__main__":
    main()
