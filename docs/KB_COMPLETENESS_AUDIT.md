# 法考项目知识库完整性审计

> 本审计面向整个法考项目知识库，客观题、主观题、参考资料和来源链统一检查。数据由当前工作区报告汇总，不代表法律正确性或商业授权已完成。
>
> 生成时间：2026-09-03

## 验收结论

当前知识库已经具备持续接入和追溯能力，但尚未达到产品准入完成状态。扫描归档链完整；结构化题目、知识点和去重快照可用；答案、解析来源、法条核验和授权仍有待补齐。

## 分项结果

| 检查项 | 当前结果 | 判定 | 依据 |
|---|---:|---|---|
| 资料接入 | 80 个文件；待扫描 0 | 通过 | `data/provenance/material_ingestion_queue.json` |
| 扫描归档 | 52 个已扫描、28 个重复；38/38 个归档目录完成映射 | 通过 | `scan_archive_report.json`、`archive_mapping_audit.json` |
| 结构化题目 | 1117 道；20 个 enriched 文件；重复题号 0 | 通过 | `enriched_integrity_report.json` |
| 客观/主观导出 | 客观 1019；主观/混合 98；canonical 1034 | 通过（导出层） | `data/exports/`、`canonical_question_map.json` |
| 答案 | 1041/1117（93.20%）；缺 76 | 待补 | `missing_answer_manifest.json` |
| 解析 | 984/1117（88.09%）；缺 133 | 待补 | `explanation_acquisition_queue.json` |
| 解析来源链 | 已有解析中 777 条缺原始来源字段 | 待补 | `explanation_provenance_audit.json` |
| 知识点 | 1117/1117（100%）已关联 | 通过（待人工复核） | `knowledge_coverage_report.json` |
| 法条 | 197/1117 已有链接；246 条候选待核验 | 待核验 | `statute_review_queue.json` |
| 主观评分点 | 25 条候选，审计错误 0 | 待专家复核 | `rubric_audit.json` |
| 答案冲突 | 171 条待人工复核 | 待复核 | `answer_conflict_queue.json` |
| 来源授权 | 37 个来源均未完成授权准入 | 待确认 | `source_admission_report.json` |
| 产品准入 | 0/1117；1117 条 blocked | 未通过 | `product_admission_snapshot.json` |

## 后续验收顺序

1. 新资料进入 `docs_materials` 后，先完成扫描、OCR、哈希去重和归档。
2. 对缺答案批次补充可核验的答案版或解析版，并保留 `answer_raw` 与处理血缘。
3. 对缺解析记录补充原始解析来源；无法定位来源的内容继续留在研究/审校层。
4. 人工核验答案冲突、题型、知识点、法条版本和主观评分点。
5. 完成来源授权与审校后，重新计算产品准入，不直接绕过 blocked 状态。

每次批次处理后运行：

```bash
python3 tools/rebuild_kb.py --project-root .
python3 tools/kb_doctor.py --root .
```

只有完整性审计、扫描归档、质量审计和来源准入同时满足要求，数据才可进入产品层。
