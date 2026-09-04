"""Build a per-file scan/archive report for incremental material intake."""
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
    ap.add_argument("--materials", type=Path, required=True)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    archive_root = args.materials / "review" / "scanned"
    by_hash: dict[str, Path] = {}
    for original in sorted(archive_root.glob("*/original.*")):
        by_hash[sha(original)] = original.parent
    rows = []
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    for item in queue.get("items", []):
        source = args.materials / item["path"]
        archive = by_hash.get(item["sha256"])
        if item["status"] == "scanned_archive" and "review/scanned/" in item["path"]:
            archive = source.parent
        rows.append({
            "path": item["path"],
            "sha256": item["sha256"],
            "status": item["status"],
            "archive_dir": str(archive.relative_to(args.materials)) if archive else None,
            "original_present": bool(archive and any(archive.glob("original.*"))),
            "ocr_present": bool(archive and (archive / "ocr.txt").exists()),
            "scan_report_present": bool(archive and (archive / "scan-report.txt").exists()),
        })
    summary = {
        "files": len(rows),
        "scanned_archive": sum(r["status"] == "scanned_archive" for r in rows),
        "duplicate_of_scanned": sum(r["status"] == "duplicate_of_scanned" for r in rows),
        "pending_scan": sum(r["status"] == "pending_scan" for r in rows),
        "missing_ocr": sum(not r["ocr_present"] for r in rows if r["status"] != "pending_scan"),
        "missing_scan_report": sum(not r["scan_report_present"] for r in rows if r["status"] != "pending_scan"),
    }
    result = {"schema_version": 1, "status": "scan_archive_report", "summary": summary, "items": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"files={len(rows)} summary={summary} output={args.output}")


if __name__ == "__main__":
    main()
