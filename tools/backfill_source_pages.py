"""Backfill missing source pages from archived OCR, conservatively."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def compact(s: str) -> str:
    return re.sub(r"\s+", "", s or "").replace("？", "?")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("sources", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in json.loads(args.sources.read_text(encoding="utf-8"))["sources"]}
    page_cache = {}
    located = 0
    for item in doc.get("items", []):
        if item.get("source_page") is not None:
            continue
        source = sources.get(item.get("source_id"), {})
        ocr = Path(source.get("archive_path", "")) / "ocr.txt"
        if not ocr.exists():
            continue
        key = str(ocr)
        if key not in page_cache:
            chunks = re.split(r"===== page-(\d+)\.png =====", ocr.read_text(encoding="utf-8", errors="replace"))
            page_cache[key] = {int(chunks[i]): compact(chunks[i + 1]) for i in range(1, len(chunks), 2)}
        compact_stem = compact(item.get("stem", ""))
        probes = [compact_stem[:28], compact_stem[:16], compact_stem[:12]]
        matches = []
        for probe in probes:
            candidate = [p for p, text in page_cache[key].items() if probe and probe in text]
            if len(candidate) == 1:
                matches = candidate
                break
        if len(matches) == 1:
            item["source_page"] = matches[0]
            item["source_page_status"] = "located_by_stem_backfill"
            located += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} located={located} output={args.output}")


if __name__ == "__main__":
    main()
