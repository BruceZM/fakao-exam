# 法考知识库答案获取队列

本页由 `tools/build_answer_acquisition_queue.py` 生成。只统计当前没有结构化 `answer` 的题目；补充答案时必须保留原始答案文件和 `answer_raw`，并按 `docs/KB_REVIEW_PROTOCOL.md` 复核。

当前缺少答案：**76 条**，涉及 **3 个来源**。

| 优先级 | 来源 | 缺少答案 | OCR 答案标记 | 外部答案候选 | 已归档资料 | 建议动作 |
|---:|---|---:|---:|---:|---|---|
| 1 | 郄鹏恩-公司法每日一题（完结） (`qiepeng-en-company-law-daily`) | 61 | 0（题号 1-61） | 15 | `docs_materials/review/scanned/郄鹏恩-公司法每日一题-完结` | 先核验外部链接可读性，再补充授权答案版 |
| 2 | 郄鹏恩-2026法考合伙企业法个独外商法每日一题 (`qiepeng-en-partnership`) | 11 | 1（题号 1-12） | 7 | `docs_materials/review/scanned/郄鹏恩-合伙企业法个独外商法每日一题` | 核对 OCR 答案标记后按题号回填 |
| 3 | 孟献贵-2026民商法每日一题（1-160） (`menggui-2026-civil-commercial-daily`) | 4 | 323（题号 1-160） | 0 | `docs_materials/review/scanned/孟献贵-2026民商法每日一题-1至160` | 核对 OCR 答案标记后按题号回填 |

## 合并规则

1. 先核对题号与题干，禁止仅按文件顺序盲目覆盖。
2. 原始答案写入 `answer_raw`，规范化答案写入 `answer`；多选题保留多字母顺序。
3. 每批修改都要生成备份与 lineage，并运行 `python3 tools/rebuild_kb.py --project-root .`。
