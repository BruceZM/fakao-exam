# 法考智能练习

国家统一法律职业资格考试（法考）练习产品项目。

## 项目总目标

本目录持续建设的是**整个法考项目的数据知识库**。客观题、主观题、参考笔记、法条、解析、评分点和来源授权都属于同一条数据链路；扫描、OCR、清洗、结构化和审校工作，均以形成可追溯、可复用、可按版本维护的法考知识库为目标。客观题和主观题可以在产品界面中分开呈现，但底层共享来源、知识点、法条版本和审校记录。

后续法考相关的代码、题库、评分规则、文档和部署配置统一放在本目录；教资项目继续保留在相邻的 `kemu2-exam` 目录中。

- 全库审校协议：[`docs/KB_REVIEW_PROTOCOL.md`](docs/KB_REVIEW_PROTOCOL.md)
- 新增资料流程：[`docs/ADDING_MATERIALS.md`](docs/ADDING_MATERIALS.md)
- 下一批资料清单：[`docs/NEXT_MATERIALS_NEEDED.md`](docs/NEXT_MATERIALS_NEEDED.md)
- 审校清单：[`docs/REVIEW_BACKLOG.md`](docs/REVIEW_BACKLOG.md)
- 知识库状态：[`docs/KB_STATUS.md`](docs/KB_STATUS.md)
- 完整性审计：[`docs/KB_COMPLETENESS_AUDIT.md`](docs/KB_COMPLETENESS_AUDIT.md)
- 产品支撑评估：[`docs/PRODUCT_READINESS_ASSESSMENT.md`](docs/PRODUCT_READINESS_ASSESSMENT.md)
- 中国大陆云端存储架构：[`docs/CLOUD_STORAGE_ARCHITECTURE.md`](docs/CLOUD_STORAGE_ARCHITECTURE.md)
- 来源目录：[`docs/SOURCE_CATALOG.md`](docs/SOURCE_CATALOG.md)
- 知识点覆盖：[`data/provenance/knowledge_coverage_report.md`](data/provenance/knowledge_coverage_report.md)
- 参考资料科目目录：[`docs/REFERENCE_SUBJECT_CATALOG.md`](docs/REFERENCE_SUBJECT_CATALOG.md)
- 答案获取队列：[`docs/ANSWER_ACQUISITION_QUEUE.md`](docs/ANSWER_ACQUISITION_QUEUE.md)
- 解析获取队列：[`docs/EXPLANATION_ACQUISITION_QUEUE.md`](docs/EXPLANATION_ACQUISITION_QUEUE.md)
- 解析来源审计：`data/provenance/explanation_provenance_audit.json`
- 解析来源人工清单：[`docs/EXPLANATION_PROVENANCE_REVIEW.md`](docs/EXPLANATION_PROVENANCE_REVIEW.md)
- 解析来源自动回填工具：`tools/backfill_explanation_provenance.py`（仅接受 OCR 原文直接匹配）
- 解析 OCR 跨文件来源映射：`data/provenance/explanation_ocr_overrides.json`
- 答案审校批次：[`docs/ANSWER_REVIEW_BATCHES.md`](docs/ANSWER_REVIEW_BATCHES.md)
- 补齐优先级：[`docs/REVIEW_PRIORITY.md`](docs/REVIEW_PRIORITY.md)
- 选项结构审校：[`data/provenance/option_review_queue.json`](data/provenance/option_review_queue.json)
- 外部答案导入规范：[`docs/EXTERNAL_ANSWER_IMPORT_PROTOCOL.md`](docs/EXTERNAL_ANSWER_IMPORT_PROTOCOL.md)
- 外部答案链接候选：[`data/provenance/external_answer_link_candidates.json`](data/provenance/external_answer_link_candidates.json)；可用 `python3 tools/refresh_external_answer_links.py` 刷新（仅登记链接，不自动导入答案正文）。

- canonical 去重导出：`data/exports/canonical_objective_questions.jsonl`、`data/exports/canonical_subjective_questions.jsonl`
- 产品数据契约：[`docs/PRODUCT_DATA_CONTRACT.md`](docs/PRODUCT_DATA_CONTRACT.md)
- 来源授权审校：[`docs/LICENSE_REVIEW_QUEUE.md`](docs/LICENSE_REVIEW_QUEUE.md)
- 主观题评分点候选：`data/rubrics/candidates.json`
- 主观题评分点审校：[`docs/RUBRIC_REVIEW_QUEUE.md`](docs/RUBRIC_REVIEW_QUEUE.md)
- 一键体检：`python3 tools/kb_doctor.py --root .`
- 产品层冒烟检查：`python3 tools/smoke_test_kb.py --root .`
- 全量重建：`python3 tools/rebuild_kb.py --project-root .`
- 当前快照清单：[`data/provenance/kb_snapshot_manifest.json`](data/provenance/kb_snapshot_manifest.json)

## 第一阶段备考应用

当前已提供参照教资项目的无状态研究版应用：FastAPI 后端、静态前端和 1034 条 canonical 题目随版本发布；原始资料和本地审校备份不进入部署镜像。

本地运行：

```bash
pip install -r requirements.txt
python3 -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

浏览器访问 `http://127.0.0.1:8000`，默认访问口令为 `1234`；部署前请通过环境变量或 `deploy.txt` 修改。ModelScope 配置模板见 [`deploy.txt.example`](deploy.txt.example)，发布检查命令为：

```bash
python3 tools/deploy_ms.py --check
```

当前应用是研究/审校版，产品准入状态以 `data/provenance/product_admission_snapshot.json` 为准。
