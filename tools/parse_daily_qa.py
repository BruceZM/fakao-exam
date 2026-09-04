"""Parse daily Q&A OCR pages into short-answer knowledge records."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--subject", default="民诉法")
    args = ap.parse_args()
    raw = args.input.read_text(encoding="utf-8", errors="replace")
    chunks = re.split(r"===== page-(\d+)\.png =====", raw)
    items = []
    for i in range(1, len(chunks), 2):
        page, content = int(chunks[i]), chunks[i + 1]
        content = re.sub(r"\s+", " ", content).strip()
        # 页眉中的日期、时间和作者水印不稳定，统一从 DAY 标记之后开始取题干。
        day = re.search(
            r"DAY\s*[A-Z0-9④ＴTＥ]*\s*(?:（[^）]*）|\([^)]*\))?",
            content,
            flags=re.IGNORECASE,
        )
        if day:
            content = content[day.end():].strip()
        # 答案区的提示语存在多种 OCR 结果；题干中通常不会出现“解析：”。
        cue = re.search(
            r"(?:今日答案来[咯啦]|快来对答案|今天的[^\n]{0,40}(?:Day|DAY)\s*\d+\s*(?:答案)?|Day\s*\d+\s*解析|解析\s*[:：])"
            r"\s*(?:(?:Day|DAY)\s*\d+\s*)?(?:解析\s*[:：]?)?",
            content,
            flags=re.IGNORECASE,
        )
        if cue:
            question = content[:cue.start()].strip(" @©")
            tail = content[cue.end():]
        else:
            question, tail = content, ""
        # 有些页只有选择答案，没有解析；保留原始答案以便后续人工核验。
        answer_raw = ""
        answer_match = re.search(r"答案\s*[:：]?\s*([A-DＡ-Ｄ]{1,4})\b", tail, flags=re.IGNORECASE)
        if answer_match:
            answer_raw = answer_match.group(1).translate(str.maketrans("ＡＢＣＤ", "ABCD"))
            tail = (tail[:answer_match.start()] + tail[answer_match.end():]).strip()
        # 清除页内账号水印和残留的“解析”字样。
        question = re.sub(r"[@©]\s*民[^ ]{0,8}", "", question)
        question = re.sub(r"每[@©]\s*民[^ ]{0,8}", "", question)
        question = re.sub(r"\s*(?:民诉|民源)韩[^ ]{0,6}$", "", question)
        question = re.sub(r"\s+每\s*$", "", question)
        tail = re.sub(r"^解析\s*[:：]?\s*", "", tail)
        explanation = tail.strip(" @©")
        if not question:
            continue
        items.append({
            "question_id": f"{args.source_id}-{len(items)+1:03d}",
            "stage": "objective_subjective_common",
            "subject": args.subject,
            "question_type": "short_answer",
            "stem": question,
            "options": [],
            "answer": answer_raw or None,
            "answer_raw": answer_raw,
            "explanation": explanation,
            "knowledge_points": [],
            "statutes": [],
            "source_id": args.source_id,
            "source_page": page,
            "source_page_status": "located_by_page",
            "license_status": "unknown",
            "content_status": "parsed",
            "review_status": "needs_human_review"
        })
    result = {"schema_version": 1, "status": "parsed_daily_qa", "items": items}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(items)} output={args.output}")


if __name__ == "__main__":
    main()
