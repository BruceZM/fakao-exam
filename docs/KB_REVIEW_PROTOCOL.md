# 法考知识库审校协议

本协议适用于 `fakao-exam` 下所有客观题、主观题、参考笔记和扫描资料。目标是让新增资料持续进入同一条可追溯的数据链路，而不是把 OCR 文本直接当作产品题库。

## 文件级归档

1. 新资料先放入 `docs_materials/objective/raw`、`docs_materials/objective/recalled`、`docs_materials/subjective` 或 `docs_materials/reference`。
2. 完成 OCR 后，移动或复制到 `docs_materials/review/scanned/<资料名>/`，目录必须保留原始文件、`ocr.txt` 和 `scan-report.txt`。
3. `material_ingestion_queue.json` 和 `scan_archive_report.json` 必须显示该文件为 `scanned_archive` 或明确的 `duplicate_of_scanned`；不得留下 `pending_scan`。

## 题目级处理

1. 题目进入 `data/questions/*draft.json` 后，先确认题干边界、题型、选项、答案和解析字段。
2. 清洗或补齐字段时保留 `answer_raw`、来源页、来源文件和修改血缘；自动补齐必须标记 `needs_human_review`。
3. 知识点和法条只作为候选关联，不能因为自动匹配就标记为法律正确。
4. 重复题通过规范化题干生成候选组和 canonical 映射；产品导出默认可按 canonical 题筛选。

## 产品准入

题目只有同时满足以下条件，才能进入产品题库：

- 来源审校通过，并明确授权状态；
- 题干、选项、答案和解析完成人工核验；
- 法条和法律版本已核对；
- 页码、来源文件和处理血缘可回溯；
- 质量审计无阻断性问题。

公开可见、个人整理、机构讲义或回忆版资料，均不能自动视为获得商业使用授权。当前准入状态以 `data/provenance/source_admission_report.json` 为准。

## 每次重建后的验收

运行：

```bash
python3 tools/rebuild_kb.py
```

并核对：

- `data/provenance/knowledge_base_integrity_report.json` 的 `status` 为 `validated`；
- `data/provenance/scan_archive_report.json` 的 `pending_scan` 为 0，且无缺失 OCR/扫描报告；
- `docs/KB_STATUS.md` 与各审校队列数量一致；
- 新增或修改文件均有备份和 `data/questions/lineage/` 记录。
