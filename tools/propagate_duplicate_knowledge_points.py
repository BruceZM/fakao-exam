"""Propagate reviewed-candidate tags across duplicate question records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", type=Path, required=True)
    ap.add_argument("--questions", type=Path, nargs="+", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    docs = {}
    items = {}
    for path in args.questions:
        doc = json.loads(path.read_text(encoding="utf-8")); docs[path] = doc
        for item in doc.get("items", []): items[item["question_id"]] = item
    changed = []
    for group in json.loads(args.map.read_text(encoding="utf-8")).get("groups", []):
        members = [r["question_id"] for r in group.get("ranking", [])]
        tags = []
        for qid in members:
            for tag in items.get(qid, {}).get("knowledge_points", []) or []:
                name = tag.get("name") if isinstance(tag, dict) else tag
                if name and name not in [x["name"] for x in tags]:
                    tags.append({"name": name, "source": "duplicate_group_inheritance", "review_status": "needs_human_review", "inherited_from": qid})
        if not tags:
            continue
        for qid in members:
            item = items.get(qid)
            if not item or item.get("knowledge_points"):
                continue
            item["knowledge_points"] = tags
            item["tagging_status"] = "inherited_from_duplicate_group"
            item["tag_inheritance_group"] = group.get("duplicate_group_id")
            changed.append(qid)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path, doc in docs.items():
        out = args.output_dir / path.name
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"changed={len(changed)} files={len(docs)} output_dir={args.output_dir}")
    for qid in changed:
        print(qid)


if __name__ == "__main__":
    main()
