from __future__ import annotations
import argparse
import json
from pathlib import Path

def load(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provenance', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    p = args.provenance
    quality = load(p / 'question_quality_report.json').get('summary', {})
    ready = load(p / 'knowledge_base_readiness_report.json').get('totals', {})
    provenance = load(p / 'explanation_provenance_audit.json').get('summary', {})
    sections = [
        ('答案缺口', quality.get('missing_answer', 0), '核对扫描原文与答案版后补齐 answer，并保留 answer_raw。'),
        ('解析缺口', ready.get('questions', 0) - ready.get('explained', 0), '补齐 explanation，不能用自动推断替代原文核验。'),
        ('解析来源链', provenance.get('explained_missing_provenance', 0), '为已有 explanation 找到原始 OCR/解析页并补充来源字段。'),
        ('法条候选核验', len(load(p / 'statute_review_queue.json').get('items', [])), '核对法条名称、条号和适用法律版本。'),
        ('答案冲突', len(load(p / 'answer_conflict_queue.json').get('items', [])), '人工确认题型与答案，不覆盖原始答案字段。'),
        ('非答案型原始字段', quality.get('answer_raw_nonanswer_residue', 0), '清理宣传语或章节标题等误写入 answer_raw 的内容，保留原始备份。'),
        ('来源授权', load(p / 'source_admission_report.json').get('summary', {}).get('blocked', 0), '确认授权和来源审校后再进入产品层。'),
    ]
    lines = ['# 法考知识库审校清单', '', '本页由 `tools/rebuild_kb.py` 生成；数量来自当前 provenance 报告。所有自动候选都需要人工核验。', '']
    lines.extend(f'- **{name}：{count} 条**：{note}' for name, count, note in sections)
    lines += ['', f"当前题目总数：{ready.get('questions', 0)}；答案覆盖：{ready.get('answered', 0)}；解析覆盖：{ready.get('explained', 0)}；知识点覆盖：{ready.get('questions_with_knowledge', 0)}。", '', '优先顺序：来源授权与版本 → 答案冲突/缺口 → 解析 → 法条 → 产品准入。']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(args.output)

if __name__ == '__main__':
    main()
