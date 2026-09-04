# 来源与质量审校

- `sources.json`：资料来源、归档路径、授权和总体状态。
- `question_quality_report.json`：结构化题目质量审计结果。
- `duplicate_question_candidates.json`：按题干归一化发现的重复候选组。
- `canonical_question_map_candidates.json`：每个重复候选组的主记录建议及排序依据，仍需人工确认。
- `canonical_question_map.json`：供产品检索和组卷使用的扁平题目映射；主记录仍需人工确认。
- `material_ingestion_queue.json`：资料文件的待扫描、已归档和重复状态。
- `scan_archive_report.json`：逐文件记录扫描归档目录、原件、OCR 和扫描报告是否齐全，供后续增量补资料时复核。
- `knowledge_base_readiness_report.json`：知识库当前题量、答案/解析覆盖率、知识点/法条关联和待复核基线，可在每批资料入库后重建。
- `knowledge_point_review_queue.json`：没有知识点关联的题目清单，按科目汇总，供人工或精细规则补标。
- `answer_explanation_gap_report.json`：按来源、科目、阶段和题型拆分答案/解析缺口，并给出字段缺口优先级。
- `answer_type_candidates.json`：根据原始答案字母序列生成的疑似多选题型候选，不自动改题型。
- `answer_conflict_queue.json`：客观题答案字段与题型、原始答案格式冲突的复核队列。
- `knowledge_base_integrity_report.json`：校验题目来源、资料归档路径、重复 ID、孤立选项和全文索引一致性。
- `field_coverage_report.json`：题目核心字段、选项、知识点和法条关联覆盖率。
- `product_admission_snapshot.json`：按授权与来源审校状态生成的产品准入快照，防止研究资料被误导出为产品内容。
- `source_admission_report.json`：来源级产品准入报告，区分内容已整理与授权/审校已通过。
- `source_page_review_queue.json`：尚未定位原始页码的题目清单，按来源附带归档 OCR 路径。
- `year_candidates.json`：从题干唯一明确年份生成的待确认候选，不直接写入考试年份。
- `statute_review_queue.json`：按引用频次和格式异常排序的法条候选复核队列。
- `kb_snapshot_manifest.json`：当前数据库、导出和质量报告的 SHA-256 快照清单，用于重建后的版本比对。
- `explanation_provenance_audit.json`：已有解析的来源字段审计；`docs/EXPLANATION_PROVENANCE_REVIEW.md` 为逐题人工清单。
- `explanation_ocr_overrides.json`：已核实的答案版/解析版 OCR 跨文件来源映射。

当前全库基线（由最近一次 `python3 tools/rebuild_kb.py --project-root .` 生成）：来源 37 个、资料 80 个、扫描归档 52 个、重复 28 个；结构化题目 1117 道，答案 1041 道（93.20%），解析 984 道（88.09%），知识点覆盖 1117 道（100%），法条候选关联 197 道（17.64%）。

当前队列：缺失答案 76 条；缺失解析 133 条；解析来源缺口 25 条；答案冲突 171 条；法条候选待核验 246 条；主观题评分点候选 25 条；来源授权审校 37 条。产品准入当前为 0/1117，所有记录仍需来源授权和人工审校。

解析来源字段的自动回填只接受归档 OCR 中的直接文本匹配，并保留 `data/questions/backups/` 和 `data/questions/lineage/`；剩余记录见 `docs/EXPLANATION_PROVENANCE_REVIEW.md`。

重复候选、年份候选和法条候选均为审校队列，不代表自动合并或法律结论。新增或修改资料后，必须重新运行 `tools/rebuild_kb.py`、`tools/kb_doctor.py` 和 `tools/smoke_test_kb.py`。
