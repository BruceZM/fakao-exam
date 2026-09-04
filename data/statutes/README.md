# 法条候选层

`citation_candidates.json` 汇总题目 OCR 和解析中自动提取的引用候选，并按 `law_article`、`judicial_document`、`reference_material` 初步分类。

`normalized_candidates.json` 对明显的法律名称别名和空白进行了统一，作为后续建立正式法条主键的中间层。它仍保留 `needs_legal_review` 状态，不能直接用于答题判分。

这里包含书名、论文名等误识别候选是有意保留的，便于回溯 OCR 误差。只有经过法律名称、条文号、生效日期和适用版本核验后，才可以建立正式法条记录并供题库使用。

当前候选索引包含 469 条原始引用、247 条去重后的名称候选；其中仅有 197 道题识别出至少一个引用。候选层已从全部结构化题目重新生成，仍全部标记为 `needs_legal_review`，不能直接作为判分依据。
