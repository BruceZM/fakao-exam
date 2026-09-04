"""Extract statute citation candidates from question stems and explanations."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = [
    re.compile(r"《[^》]{1,60}》(?:第[一二三四五六七八九十百千万0-9]+条(?:第[一二三四五六七八九十百千万0-9]+款)?(?:第[一二三四五六七八九十百千万0-9]+项)?)?"),
    re.compile(r"(?:最高人民法院|最高人民检察院)[^，。；\n]{0,80}(?:解释|规定|意见|批复)")
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    for item in doc.get("items", []):
        text = " ".join((item.get("stem", ""), item.get("explanation", "")))
        refs: list[str] = []
        for pattern in PATTERNS:
            refs.extend(m.group(0).strip() for m in pattern.finditer(text))
        item["statutes"] = list(dict.fromkeys(refs))
        item["statute_link_status"] = "auto_extracted" if refs else "none_found"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    linked = sum(bool(x.get("statutes")) for x in doc.get("items", []))
    print(f"items={len(doc.get('items', []))} linked={linked} output={args.output}")


if __name__ == "__main__":
    main()
