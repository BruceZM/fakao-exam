# 法考知识库数据字典

SQLite 快照位于 `data/fakao_knowledge_base.sqlite`。所有题目和资料都保留来源及复核状态，产品模块不得绕过这些状态字段直接使用内容。

## 核心表

| 表 | 用途 |
| --- | --- |
| `questions` | 题目主记录，含科目、阶段、题型、题干、答案、解析、页码和复核状态 |
| `options` | 客观题选项，按 `question_id + option_key` 唯一 |
| `question_knowledge_points` | 题目与候选知识点的关联 |
| `question_statutes` | 题目与法条引用候选的关联 |
| `sources` | 资料来源、归档路径、授权状态和来源审校状态 |
| `materials` | 扫描资料文件的 SHA-256、扩展名和归档状态 |
| `reference_documents` | 归档 OCR 全文，覆盖尚未结构化的笔记、答案版和题目版 |

## 题目关键字段

- `stage`：`objective`、`subjective` 或 `objective_subjective_common`
- `subject`：民法、刑法、民诉法、刑诉法、行政法、理论法、商经知等
- `question_type`：`single_choice`、`multiple_choice`、`true_false`、`short_answer`、`case_analysis`
- `answer`：原文或抽取答案；空值表示缺失，不得自动猜测
- `content_status`：当前主要为 `parsed`
- `review_status`：当前题目默认 `needs_human_review`
- `source_page_status`：如 `located_by_stem`、`located_by_stem_backfill`，或 `not_located`

## 补充溯源字段

- `answer_raw`：答案原始文本，清洗或规范化时必须保留
- `explanation_source`：解析来源类型，如 `source_ocr`、`scanned_ocr_explanation_section`、`cross_source_exact_stem_duplicate`
- `explanation_source_ref`：解析对应的 OCR、解析版或来源记录路径
- `explanation_review_status`：解析是否仍需人工复核；自动提取内容默认 `needs_human_review`
- `question_type_source`：题型来源；`explicit_stem_label` 表示来自原资料题干中的“（单）/（多）”标签
- `answer_structuring_status`：答案字段拆分或规范化说明，便于追溯从“结论+理由”到 `answer`/`explanation` 的变更

## 产品准入

只有来源 `license_status = licensed` 且 `review_status = reviewed` 时，来源才可进入产品准入层。当前资料均未满足这一条件；现阶段数据用于内部检索、结构化和人工审校。

新增或修改结构化资料后，在项目根目录运行 `python3 tools/rebuild_kb.py`，再查看 `data/provenance/knowledge_base_integrity_report.json` 确认快照完整性。
