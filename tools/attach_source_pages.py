"""Attach the OCR page containing each question stem to a question draft."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("？", "?")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("ocr", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.questions.read_text(encoding="utf-8"))
    raw = args.ocr.read_text(encoding="utf-8", errors="replace")
    pages: dict[int, str] = {}
    chunks = re.split(r"===== page-(\d+)\.png =====", raw)
    for i in range(1, len(chunks), 2):
        pages[int(chunks[i])] = chunks[i + 1]
    located = 0
    for item in doc.get("items", []):
        stem = clean(item.get("stem", ""))
        probe = stem[:24]
        page = next((number for number, content in pages.items() if probe and probe in clean(content)), None)
        item["source_page"] = page
        item["source_page_status"] = "located_by_stem" if page else "not_located"
        located += bool(page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} located={located} output={args.output}")


if __name__ == "__main__":
    main()
