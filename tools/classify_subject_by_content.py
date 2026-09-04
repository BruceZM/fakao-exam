"""Infer subject candidates for mixed mock questions from conservative keywords."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "民法": "民法|合同|夫妻|动物侵权|代位权|抵押|担保|继承|物权|人格权",
    "民诉法": "民事诉讼|仲裁|管辖|诉讼中止|诉讼请求|举证",
    "刑法": "刑法|犯罪|盗窃罪|抢劫罪|故意伤害|受贿罪|贪污罪|刑罚",
    "刑诉法": "刑事诉讼|侦查|值班律师|取保候审|逮捕|羁押|刑事辩护",
    "行政法": "行政法|行政许可|行政复议|行政处罚|行政诉讼|行政机关",
    "理论法": "法治|宪法|法律职业|法官|检察官|律师|公证|法律规则",
    "商经知": "公司法|商法|破产|票据|证券|知识产权|合伙",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    counts = {}
    for item in doc.get("items", []):
        text = item.get("stem", "") + item.get("explanation", "")
        matches = [(subject, len(re.findall(pattern, text))) for subject, pattern in PATTERNS.items()]
        subject, score = max(matches, key=lambda pair: pair[1])
        if score:
            item["subject"] = subject
            item["subject_status"] = "inferred_from_content"
            counts[subject] = counts.get(subject, 0) + 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items={len(doc.get('items', []))} classified={sum(counts.values())} counts={counts} output={args.output}")


if __name__ == "__main__":
    main()
