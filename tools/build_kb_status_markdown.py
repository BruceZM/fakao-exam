# -*- coding: utf-8 -*-
"""Render a human-readable current knowledge-base status page."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--provenance", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    p=args.provenance
    root=p.parent.parent
    readiness=load(p/'knowledge_base_readiness_report.json'); ready=readiness['totals']; quality=load(p/'question_quality_report.json')['summary']; scan=load(p/'scan_archive_report.json')['summary']; adm=load(p/'product_admission_snapshot.json')['summary']; ava=load(p/'source_answer_availability.json')['items']; enriched=load(p/'enriched_integrity_report.json'); manifest=load(p/'kb_snapshot_manifest.json') if (p/'kb_snapshot_manifest.json').exists() else {}; rubric_path=root/'data/rubrics/candidates.json'; rubric_count=len(load(rubric_path).get('items',[])) if rubric_path.exists() else 0
    stage_counts={x['stage']:x['n'] for x in readiness.get('stages',[])}
    objective_count=stage_counts.get('objective',0)
    subjective_count=stage_counts.get('subjective',0)+stage_counts.get('objective_subjective_common',0)
    can_obj=sum(1 for _ in (root/'data/exports/canonical_objective_questions.jsonl').open()) if (root/'data/exports/canonical_objective_questions.jsonl').exists() else 0
    can_sub=sum(1 for _ in (root/'data/exports/canonical_subjective_questions.jsonl').open()) if (root/'data/exports/canonical_subjective_questions.jsonl').exists() else 0;
    answer_type_candidates=load(p/'answer_type_candidates.json').get('summary',{}).get('items',0) if (p/'answer_type_candidates.json').exists() else 0
    provenance_audit=load(p/'explanation_provenance_audit.json') if (p/'explanation_provenance_audit.json').exists() else {'summary':{}}
    queues={
      '知识点待标注': load(p/'knowledge_point_review_queue.json')['summary']['items'],
      '答案冲突': load(p/'answer_conflict_queue.json')['summary']['items'],
      '页码待回溯': load(p/'source_page_review_queue.json')['summary']['items'],
      '法条待核验': load(p/'statute_review_queue.json')['summary']['items'],
    }
    option_queue=load(p/'option_review_queue.json').get('summary',{}).get('items',0) if (p/'option_review_queue.json').exists() else 0
    lines=['# 法考知识库当前状态','',f'> 更新由 `python3 tools/rebuild_kb.py` 生成；本页只反映结构化和审校进度，不代表法律正确性或商业授权。',f'> 快照生成时间：{manifest.get("generated_at","未知")}', '', '## 已入库规模','',f'- 来源：{ready["sources"]} 个；资料文件：{ready["materials"]} 个（扫描归档 {scan["scanned_archive"]}，重复 {scan["duplicate_of_scanned"]}，待扫描 {scan["pending_scan"]}）。',f'- 题目：{ready["questions"]} 道；客观题导出 {objective_count} 道，主观/混合导出 {subjective_count} 道；canonical 去重导出 {can_obj + can_sub} 道。',f'- 选项：{ready["options"]} 条；知识点关联：{ready["knowledge_links"]} 条；法条候选关联：{ready["statute_links"]} 条。',f'- OCR 参考文档：{ready["reference_documents"]} 份，全文索引行数：{ready["reference_documents_fts_rows"]}。','', '## 覆盖率','',f'- 答案：{ready["answered"]}/{ready["questions"]}（{ready["answered"]/ready["questions"]:.2%}）；解析：{ready["explained"]}/{ready["questions"]}（{ready["explained"]/ready["questions"]:.2%}）。',f'- 知识点：{ready["questions_with_knowledge"]}/{ready["questions"]}（{ready["questions_with_knowledge"]/ready["questions"]:.2%}）；法条候选：{ready["questions_with_statute"]}/{ready["questions"]}（{ready["questions_with_statute"]/ready["questions"]:.2%}）。','', '## 待处理队列','']
    lines += [f'- {k}：{v} 条' for k,v in queues.items()]
    lines += [f'- 选项结构审校：{option_queue} 条']
    lines += ['', '## 质量与溯源缺口','',f'- 质量审计：{quality["issues"]} 条问题，涉及 {quality["items"] if "items" in quality else "见报告"} 条记录；缺失答案 {quality["missing_answer"]} 条，选项边界异常 {quality["option_count"]} 条，答案与题型不一致 {quality.get("answer_choice_mismatch",0)} 条，非答案型原始字段残留 {quality.get("answer_raw_nonanswer_residue",0)} 条。',f'- 题型候选：{answer_type_candidates} 条题目因原始答案含多个选项字母而建议复核为多选，暂不自动改写。',f'- enriched 完整性审计：{enriched["status"]}（{enriched["summary"]["files"]} 个文件，{enriched["summary"]["items"]} 道题，重复题号 {enriched["summary"]["duplicate_question_ids"]}）。',f'- 解析来源链：{provenance_audit.get("summary",{}).get("explained_missing_provenance",0)} 条已有解析待补原始来源。',f'- 主观题评分点候选：{rubric_count} 条（均需法律专家复核）。',f'- 缺少年份：{ready["missing_year"]} 道；缺少原始页码：{ready["missing_source_page"]} 道。', f'- 产品准入：{adm["admitted"]}/{adm["questions"]} 道；来源授权状态单独在 `source_admission_report.json` 中维护。',f'- 来源答案可用性：{sum(x["availability"]=="answer_markers_present" for x in ava)}/{len(ava)} 个来源的 OCR 含答案标记。','', '补充答案时参见 [`docs/ANSWER_ACQUISITION_QUEUE.md`](ANSWER_ACQUISITION_QUEUE.md)；按科目安排参见 [`docs/REVIEW_PRIORITY.md`](REVIEW_PRIORITY.md)，逐批处理参见 [`docs/ANSWER_REVIEW_BATCHES.md`](ANSWER_REVIEW_BATCHES.md)。', '']
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'output={args.output}')


if __name__=='__main__': main()
