# 法考知识库数据层

这里存放从 `docs_materials` 归档资料中经过结构化处理的数据，不存放未核验的 OCR 原文。

建议分层：

- `questions/`：题目、选项、答案、解析
- `knowledge_points/`：科目、章节、知识点和标签
- `statutes/`：法条正文、版本和生效信息
- `rubrics/`：主观题评分点与可接受论证路径
- `provenance/`：来源、页码、授权状态和审校记录
- `exports/`：供产品开发读取的客观题、主观题 JSONL 分层导出；每条记录带来源授权状态和 `product_admission` 准入标记

`fakao_knowledge_base.sqlite` 是由结构化题目和资料队列生成的可查询快照，包含 `sources`、`materials`、`reference_documents`、`questions`、`options`、`question_knowledge_points` 和 `question_statutes` 表。当前快照登记 80 个资料文件、38 份归档 OCR 文档、1117 道题；`questions` 表保留 `source_page`，并保留题目来源和复核状态。它是开发和审校用数据，不代表所有内容已经通过法律专家核验。

新增或修改结构化资料后，可在项目根目录运行 `python3 tools/rebuild_kb.py` 一次性刷新队列、数据库、质量报告、法条候选、评分点候选和产品导出。

数据库另含 `questions_fts` 和 `reference_documents_fts` 全文检索表，可分别查询题干/解析与归档 OCR 文档。

归档文档检索示例：`python3 tools/query_knowledge_base.py --db data/fakao_knowledge_base.sqlite --documents --keyword 民法 --limit 10`。

去重检索示例：`python3 tools/query_knowledge_base.py --db data/fakao_knowledge_base.sqlite --canonical-only --subject 刑法 --limit 20`。该模式只排除重复组中的非主记录，不删除原始题目。

阶段统计和题型统计见 `provenance/knowledge_base_readiness_report.json`。其中 `objective_subjective_common` 是原资料的混合训练标记，产品组卷应同时按 `question_type` 和 `stage` 筛选。

```sql
SELECT question_id, stem FROM questions_fts
WHERE questions_fts MATCH '罪刑法定';
```
