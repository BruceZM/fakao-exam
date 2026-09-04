"""Parse a scanned multiple-choice OCR text file into a reviewable draft."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


YEAR_QUESTION_RE = re.compile(r"(?ms)^\s*(?:【|\[)(\d{4})(?:年|\s)[^】\]]*(?:】|\])\s*(.*?)(?=^\s*(?:【|\[)\d{4}(?:年|\s)|\Z)")
NUMBERED_QUESTION_RE = re.compile(r"(?ms)^\s*(\d{1,3})[\.、][ \t]*(.*?)(?=^\s*\d{1,3}[\.、][ \t]*|\Z)")
ID_QUESTION_RE = re.compile(r"(?ms)^\s*(\d{1,3})\.\s*【?([0-9]{6,})】?\s*(.*?)(?=^\s*\d{1,3}\.\s*【?[0-9]{6,}|\Z)")


def parse_options(value: str) -> list[dict[str, str]]:
    value = re.sub(r"\s+", " ", value.replace("•", " ")).strip()
    matches = list(re.finditer(r"([A-D])[\.、:：]?\s*([^A-D]+?)(?=(?:[A-D])[\.、:：]?\s*|$)", value))
    return [{"key": m.group(1), "text": re.sub(r"圆众台教育|众合教育|GYUAN.*$", "", m.group(2)).strip()} for m in matches]


def parse(path: Path, source_id: str, subject: str, allow_missing_answer: bool = False) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Remove repeated scan headers and watermarks before question blocks span pages.
    text = "\n".join(
        line for line in text.splitlines()
        if not any(token in line for token in ("===== page-", "FANGY", "GYUAN", "更多法考备考资料", "众合教育", "众合数意", "圆众台教育"))
    )
    # Normalize headings such as “行政法每日一题01” to numbered blocks.
    text = re.sub(r"(?m)^\s*[Vv]?[^\n]{0,12}每日一题\s*0*(\d+)\s*$", r"\1. ", text)
    records: list[dict] = []
    matches = list(YEAR_QUESTION_RE.finditer(text))
    year_mode = bool(matches)
    if not matches:
        id_matches = list(ID_QUESTION_RE.finditer(text))
        matches = id_matches if id_matches else list(NUMBERED_QUESTION_RE.finditer(text))
        id_mode = bool(id_matches)
    else:
        id_mode = False
    for ordinal, match in enumerate(matches, 1):
        year = int(match.group(1)) if year_mode else None
        block_group = 3 if id_mode else 2
        block = re.sub(r"\s+", " ", match.group(block_group).replace("•", " ")).strip()
        option_match = re.search(r"选项\s*[：；:]\s*(.*?)(?=(?:答案|答[案紫業])\s*[：:]?)", block)
        answer_match = re.search(r"(?:本题答案|参考答案|答案|答[案紫業])(?:】|\])?\s*[：:]?\s*(.*?)(?=解析(?:】|\])?\s*[：:]?|$)", block)
        if not answer_match and not allow_missing_answer:
            continue
        if not answer_match:
            answer_match = type("EmptyMatch", (), {"start": lambda self: len(block), "group": lambda self, n: ""})()
        stem_end = option_match.start() if option_match else None
        if not option_match:
            first_option = re.search(r"(?m)(?:^|\s)([A-D])[\.、:：]\s*", block)
            if first_option:
                stem_end = first_option.start()
                explanation_start = re.search(r"解析(?:】|\])?\s*[：:]?", block)
                option_end = explanation_start.start() if explanation_start else answer_match.start()
                options_text = block[first_option.start(): option_end]
            else:
                options_text = ""
        else:
            options_text = option_match.group(1)
        options = parse_options(options_text)
        if not options:
            continue
        stem = block[:stem_end].strip() if stem_end is not None else block
        answer = answer_match.group(1).strip(" 。；;\n【】[]")
        answer_key = re.match(r"[A-D]", answer)
        explanation_match = re.search(r"解析(?:】|\])?\s*[：:]?\s*(.*)$", block)
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        records.append({
            "question_id": f"{source_id}-{ordinal:03d}",
            "source_question_id": match.group(2) if id_mode else None,
            "year": year,
            "stage": "objective",
            "subject": subject,
            "question_type": "multiple_choice" if "多选" in block[:200] else "single_choice",
            "stem": stem,
            "options": options,
            "answer_raw": answer,
            "answer": answer_key.group(0) if answer_key else next((x["key"] for x in options if re.sub(r"[日天]$", "", x["text"]) in re.sub(r"[日天]$", "", answer)), None),
            "explanation": explanation,
            "knowledge_points": [],
            "statutes": [],
            "source_id": source_id,
            "source_page": None,
            "license_status": "unknown",
            "content_status": "parsed",
            "review_status": "needs_human_review",
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-id", default="menggui-2026-civil-common-sense")
    parser.add_argument("--subject", default="民法")
    parser.add_argument("--allow-missing-answer", action="store_true")
    args = parser.parse_args()
    records = parse(args.input, args.source_id, args.subject, args.allow_missing_answer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": 1, "items": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"parsed={len(records)} output={args.output}")


if __name__ == "__main__":
    main()
