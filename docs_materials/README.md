# 法考资料目录

## 当前归类

- `objective/raw/`：客观题练习资料与历年重难题
- `objective/recalled/`：回忆版客观题，需单独标注来源
- `reference/daily/`：每日一题、专题练习和机构讲义，作为参考素材
- `reference/notes/`：三色笔记等知识点参考资料
- `review/candidate-subjective/`：可能包含主观题或综合模考，等待内容核验
- `review/duplicates/`：经 SHA-1 校验确认的重复文件，暂不删除
- `official/`：待放入官方公告、大纲和官方样题
- `subjective/`：待放入已确认可用于主观题训练的材料

## 使用边界

本目录中的培训机构资料、每日一题和回忆版题目目前均视为“参考资料”，不等同于已获商业授权的题库。正式导入产品前，需要逐题提取、核验答案和法条版本，并记录来源、授权状态与审校状态。

## 增量扫描入口

每次补充资料后，在项目根目录 `/Users/RroundRiser/Documents/Exam Programs/fakao-exam` 运行 `python3 tools/rebuild_kb.py --project-root .`。逐文件扫描、重复和归档完整性见 [`data/provenance/scan_archive_report.json`](../data/provenance/scan_archive_report.json)；新文件会显示为 `pending_scan`，完成 OCR 后再进入 `review/scanned/<资料名>/`。

来源与题目映射可查 [`docs/SOURCE_CATALOG.md`](../docs/SOURCE_CATALOG.md)；缺失答案的来源和题号见 [`docs/ANSWER_ACQUISITION_QUEUE.md`](../docs/ANSWER_ACQUISITION_QUEUE.md)，缺失解析及 OCR 线索见 [`docs/EXPLANATION_ACQUISITION_QUEUE.md`](../docs/EXPLANATION_ACQUISITION_QUEUE.md)。完整字段、备份和审校规则见 [`docs/ADDING_MATERIALS.md`](../docs/ADDING_MATERIALS.md) 与 [`docs/KB_REVIEW_PROTOCOL.md`](../docs/KB_REVIEW_PROTOCOL.md)。

当前最需要补充的资料见 [`docs/NEXT_MATERIALS_NEEDED.md`](../docs/NEXT_MATERIALS_NEEDED.md)。

全库逐项验收见 [`docs/KB_COMPLETENESS_AUDIT.md`](../docs/KB_COMPLETENESS_AUDIT.md)。
