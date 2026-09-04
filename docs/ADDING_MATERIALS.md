# 新增法考资料操作流程

所有新增资料必须放在：

`/Users/RroundRiser/Documents/Exam Programs/fakao-exam/docs_materials`

## 放置位置

- 客观题原始资料：`objective/raw/`
- 客观题回忆版：`objective/recalled/`
- 主观题资料：`subjective/`
- 法条、笔记、课程资料：`reference/`

不要直接修改 `docs_materials/review/scanned/`。该目录只存已经完成扫描归档的资料。

## 扫描归档

新增文件后，先运行：

```bash
cd "/Users/RroundRiser/Documents/Exam Programs/fakao-exam"
python3 tools/build_material_queue.py docs_materials data/provenance/material_ingestion_queue.json
```

查看 `pending_scan` 清单。完成 OCR 后，每份资料建立：

`docs_materials/review/scanned/<资料名>/`

目录中保留原始文件、`ocr.txt` 和 `scan-report.txt`。如果文件与已有归档的 SHA-256 相同，标记为重复，不再重复切题。

扫描完成后，把该资料从待扫描清单对应的位置归档到 `review/scanned/`，再重新生成队列确认：

```bash
python3 tools/build_material_queue.py docs_materials data/provenance/material_ingestion_queue.json
```

队列应满足 `pending_scan=0`；重复文件保留 `duplicate_of_scanned` 记录，不删除原始资料。

## 结构化与验收

将题目解析结果放入 `data/questions/`，保留 `source_id`、`source_page`、`source_type`、`license_status` 和 `review_status`。然后运行：

```bash
python3 tools/rebuild_kb.py
python3 tools/kb_doctor.py --root .
```

如需补充已有解析的来源链，可使用 `tools/backfill_explanation_provenance.py`；该工具只处理能在归档 OCR 中直接匹配的文本，并自动生成备份和血缘记录。

`rebuild_kb.py` 会同步更新扫描归档报告、来源目录、知识点覆盖、答案/解析审校队列、法条候选、授权审校、快照清单和 `docs/KB_STATUS.md`。如需单独核对完整性，再运行：

```bash
python3 tools/smoke_test_kb.py
python3 tools/build_snapshot_manifest.py --root . --output data/provenance/kb_snapshot_manifest.json
```

任何清洗、补答案或补解析都必须保留原字段，并在 `data/questions/backups/` 与 `data/questions/lineage/` 留下可追溯记录；无法从原文确认的内容只进入审校队列，不得猜填。

验收以下文件：

- `data/provenance/scan_archive_report.json`
- `data/provenance/knowledge_base_integrity_report.json`
- `data/provenance/knowledge_base_readiness_report.json`
- `data/provenance/product_admission_snapshot.json`
- `docs/KB_STATUS.md`

只有来源授权明确、内容人工核验通过、法律版本和法条已确认的题目，才能从 blocked 状态进入产品层。新增资料默认只进入研究和审校层。
