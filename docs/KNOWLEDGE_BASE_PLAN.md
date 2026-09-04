# 法考项目数据知识库规范

本项目的扫描、整理和题库建设，统一服务于长期法考数据知识库。扫描文本不是最终题库，必须经过结构化、核验和来源审校后才能进入产品数据。

## 数据链路

```text
原始资料
  -> 扫描归档与 OCR
  -> 文本清洗（页眉、页脚、水印、重复页）
  -> 题目切分
  -> 选项、答案、解析抽取
  -> 科目 / 章节 / 知识点 / 法条关联
  -> 人工核验与版本确认
  -> 产品题库或知识图谱
```

每个阶段都保留上游文件和状态，不覆盖原始 PDF 或 OCR 文本。

具体表结构和字段定义见 [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)。

## 题目最小字段

`question_id`、`stage`（客观/主观）、`subject`、`question_type`、`stem`、`options`、`answer`、`explanation`、`statutes`、`knowledge_points`、`source_id`、`source_page`、`source_type`、`license_status`、`content_status`、`review_status`、`law_version`。

## 状态含义

- `scanned`：已完成扫描和 OCR，尚未完成题目结构化。
- `parsed`：已切分为题目并抽取字段，仍需核验。
- `verified`：题干、答案、解析和法条已人工核验。
- `product_ready`：来源、授权、版本和质量均满足产品使用要求。

培训机构资料、每日一题、回忆版真题默认只能作为参考来源；公开可见不等于获得商业使用授权。
