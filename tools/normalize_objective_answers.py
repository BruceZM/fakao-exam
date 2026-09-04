"""Normalize unambiguous multi-choice answers from answer_raw."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("input", type=Path); ap.add_argument("output", type=Path); args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8")); changed=[]
    for item in doc.get("items", []):
        if item.get("question_type") != "multiple_choice": continue
        raw=(item.get("answer_raw") or "").strip().upper().translate(str.maketrans("ＡＢＣＤ", "ABCD"))
        letters="".join(re.findall("[A-D]", raw))
        residue=re.sub(r"[A-D\s,，、。．.;；:：()（）\[\]【】]+", "", raw)
        if len(letters)>=2 and not residue:
            normalized="".join(dict.fromkeys(letters))
            if item.get("answer") != normalized:
                item["answer"] = normalized
                item["answer_normalization_status"] = "normalized_from_clean_answer_raw"
                item["answer_review_status"] = "needs_human_review"
                changed.append(item["question_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"items={len(doc.get('items',[]))} normalized={len(changed)} output={args.output}")
    for qid in changed: print(qid)


if __name__ == "__main__": main()
