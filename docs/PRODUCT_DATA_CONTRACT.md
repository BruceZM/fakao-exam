# 法考产品数据契约

本契约定义产品原型读取法考知识库时的边界。研究数据、审校数据和产品数据必须按状态区分。

## 推荐读取入口

- 去重客观题：`data/exports/canonical_objective_questions.jsonl`
- 去重主观/混合题：`data/exports/canonical_subjective_questions.jsonl`
- 全量审校数据：`data/exports/objective_questions.jsonl`、`data/exports/subjective_questions.jsonl`
- 结构化查询：`data/fakao_knowledge_base.sqlite` 配合 `tools/query_knowledge_base.py`

canonical 导出包含所有唯一题目，并在重复题组中只保留一条 canonical 记录。需要追溯重复来源时，读取 `data/provenance/canonical_question_map.json`。

## 字段约定

产品读取时应保留 `question_id`、`stage`、`subject`、`question_type`、`stem`、`options`、`answer`、`explanation`、`knowledge_points`、`source_id`、`source_page`、`product_admission`。`answer_raw` 用于审校追溯，不应直接展示给考生。

`manual_candidate`、`needs_human_review`、`blocked_pending_license_or_review` 都表示该记录尚未达到正式产品发布条件。产品层不得把这些状态渲染为“官方答案”或“已核验解析”。

## 准入条件

只有来源授权为 `licensed`、来源审校为 `reviewed`，且题目内容和法律版本完成人工核验时，`product_admission` 才能为 `admitted`。当前准入结果以 `data/provenance/product_admission_snapshot.json` 为准。

## 更新与验收

新增资料或题目字段后，运行 `python3 tools/rebuild_kb.py`，再核对完整性报告、字段覆盖率、答案冲突队列和产品准入快照。任何缺失、冲突或授权未知的记录都留在研究/审校层。
