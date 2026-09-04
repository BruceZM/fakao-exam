"""Create a reproducible manifest for the current KB snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.project_root.resolve()
    paths = [root / "data/fakao_knowledge_base.sqlite", *sorted((root / "data/provenance").glob("*.json")), *sorted((root / "data/exports").glob("*.jsonl")), root / "data/knowledge_points/taxonomy.json"]
    output_resolved = args.output.resolve()
    files = [{"path": str(p.relative_to(root)), "sha256": sha256(p), "bytes": p.stat().st_size} for p in paths if p.exists() and p.resolve() != output_resolved]
    result = {"schema_version": 1, "status": "snapshot_manifest", "scope": "entire_legal_exam_knowledge_base", "scope_description": "客观题、主观题、参考资料、法条、解析、评分点及来源审校的统一数据知识库", "generated_at": datetime.now(timezone.utc).isoformat(), "files": files}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"files={len(files)} output={args.output}")


if __name__ == "__main__":
    main()
