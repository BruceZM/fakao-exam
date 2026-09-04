"""Extract short-answer and case-analysis candidates from mock OCR."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def split_records(section, kind, source, limit=None):
    marks = list(re.finditer(r"(?m)(?<![\d])([0-9]{1,2})[\.、]\s*", section))
    out = []
    seen = set()
    for i, mark in enumerate(marks):
        number = int(mark.group(1))
        if kind == "case_analysis" and number > 4:
            continue
        if limit and len(out) >= limit:
            break
        if kind == "case_analysis" and number in seen:
            continue
        end = marks[i + 1].start() if i + 1 < len(marks) else len(section)
        text = re.sub(r"\s+", " ", section[mark.end():end]).strip()
        text = re.sub(r"成功的路上.*$", "", text).strip()
        if text:
            seen.add(number)
            out.append({"question_id": f"{source}-{kind}-{number}", "stage": "subjective", "subject": "民法", "question_type": kind, "stem": text, "options": [], "answer": None, "answer_raw": "", "explanation": "", "knowledge_points": [], "statutes": [], "source_id": source, "source_page": None, "source_page_status": "needs_page_mapping", "license_status": "unknown", "content_status": "parsed", "review_status": "needs_human_review"})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input", type=Path); ap.add_argument("output", type=Path); ap.add_argument("--source-id", required=True); args = ap.parse_args()
    raw = re.sub(r"\s+", " ", args.input.read_text(encoding="utf-8", errors="replace"))
    q_start = raw.find("四、问答题")
    c_start = raw.find("五、案例分析题", q_start)
    q = raw[q_start:c_start] if q_start >= 0 and c_start > q_start else ""
    next_q = raw.find("四、问答题", c_start + 1)
    c = raw[c_start:next_q if next_q > c_start else len(raw)] if c_start >= 0 else ""
    items = (split_records(q, "short_answer", args.source_id, 10) if q else []) + (split_records(c, "case_analysis", args.source_id, 4) if c else [])
    # 答案版位于文档后半部分。必须按第二次“四/五”标题定位，不能用
    # 混合 alternatives 的 findall，否则会把案例答案错配到问答题。
    four_positions = [m.start() for m in re.finditer("四、问答题", raw)]
    five_positions = [m.start() for m in re.finditer("五、案例分析题", raw)]
    answer_short = raw[four_positions[1]:five_positions[1]] if len(four_positions) > 1 and len(five_positions) > 1 and four_positions[1] < five_positions[1] else ""
    answer_case = raw[five_positions[1]:] if len(five_positions) > 1 else ""
    for kind, section in (("short_answer", answer_short), ("case_analysis", answer_case)):
        answers = {}
        for m in re.finditer(r"(?:^|\s)(\d+)\.\s*共[^。]*。\s*答：?\s*(.*?)(?=\s+\d+\.\s*共|\s+五、案例分析题|\s+温馨提示|$)", section):
            answers[int(m.group(1))] = m.group(2).strip()
        for item in items:
            if f"-{kind}-" in item["question_id"]:
                n = int(item["question_id"].rsplit("-", 1)[-1])
                if n in answers:
                    item["answer"] = answers[n]
                    item["answer_raw"] = answers[n]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": 1, "status": "parsed_mock_subjective", "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(items)} output={args.output}")

if __name__ == "__main__":
    main()
