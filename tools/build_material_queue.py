"""Inventory material files and mark their ingestion status from archive paths."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("materials", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    archive_root = args.materials / "review" / "scanned"
    archived_hashes = set()
    if archive_root.exists():
        for pattern in ("original.pdf", "original.docx", "original.doc"):
            archived_hashes.update(sha(p) for p in archive_root.rglob(pattern))
    items = []
    for path in sorted(args.materials.rglob("*")):
        if not path.is_file() or path.name in {".DS_Store", "SCAN_MANIFEST.md", "README.md"} or path.suffix.lower() not in {".pdf", ".docx", ".doc"}:
            continue
        digest = sha(path)
        relative = str(path.relative_to(args.materials))
        if "review/scanned/" in relative:
            status = "scanned_archive"
        elif digest in archived_hashes:
            status = "duplicate_of_scanned"
        else:
            status = "pending_scan"
        items.append({"path": relative, "extension": path.suffix.lower(), "sha256": digest, "status": status})
    result = {"schema_version": 1, "status": "material_ingestion_queue", "items": items, "summary": {s: sum(x["status"] == s for x in items) for s in ("pending_scan", "scanned_archive", "duplicate_of_scanned")}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"files={len(items)} summary={result['summary']} output={args.output}")


if __name__ == "__main__":
    main()
