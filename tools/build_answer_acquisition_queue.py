"""Build a source-oriented queue for acquiring missing answer keys."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
import re


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--external-links", type=Path)
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    rows = db.execute(
        """SELECT q.source_id, s.title, s.archive_path, COUNT(*)
           FROM questions q LEFT JOIN sources s ON s.source_id=q.source_id
           WHERE COALESCE(TRIM(q.answer),'')=''
           GROUP BY q.source_id, s.title, s.archive_path ORDER BY COUNT(*) DESC, q.source_id"""
    ).fetchall()
    total = sum(r[3] for r in rows)
    link_counts = {}
    if args.external_links and args.external_links.exists():
        data = __import__("json").loads(args.external_links.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            link_counts[item.get("source_id")] = link_counts.get(item.get("source_id"), 0) + 1
    lines = [
        "# 法考知识库答案获取队列",
        "",
        "本页由 `tools/build_answer_acquisition_queue.py` 生成。只统计当前没有结构化 `answer` 的题目；补充答案时必须保留原始答案文件和 `answer_raw`，并按 `docs/KB_REVIEW_PROTOCOL.md` 复核。",
        "",
        f"当前缺少答案：**{total} 条**，涉及 **{len(rows)} 个来源**。",
        "",
        "| 优先级 | 来源 | 缺少答案 | OCR 答案标记 | 外部答案候选 | 已归档资料 | 建议动作 |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for i, (source_id, title, archive, count) in enumerate(rows, 1):
        label = title or source_id
        archive = archive or "（未登记归档路径）"
        ocr_text = ""
        if archive != "（未登记归档路径）":
            apath = Path(archive)
            for op in apath.glob("ocr.txt"):
                ocr_text += op.read_text(encoding="utf-8", errors="ignore")
        markers = ocr_text.count("答案") + ocr_text.count("答業")
        nums=[int(m.group(1)) for m in re.finditer(r'(?m)^\s*(\d{1,3})[\.、．]',ocr_text) if int(m.group(1)) > 0]
        ocr_range=(min(nums),max(nums)) if nums else None
        ext = link_counts.get(source_id, 0)
        if markers:
            action = "核对 OCR 答案标记后按题号回填"
        elif ext:
            action = "先核验外部链接可读性，再补充授权答案版"
        else:
            action = "补充该来源的答案版或解析版后再回填"
        scope = f"{ocr_range[0]}-{ocr_range[1]}" if ocr_range else "未知"
        lines.append(f"| {i} | {label} (`{source_id}`) | {count} | {markers}（题号 {scope}） | {ext} | `{archive}` | {action} |")
    lines += [
        "",
        "## 合并规则",
        "",
        "1. 先核对题号与题干，禁止仅按文件顺序盲目覆盖。",
        "2. 原始答案写入 `answer_raw`，规范化答案写入 `answer`；多选题保留多字母顺序。",
        "3. 每批修改都要生成备份与 lineage，并运行 `python3 tools/rebuild_kb.py --project-root .`。",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"sources={len(rows)} missing_answers={total} output={args.output}")


if __name__ == "__main__":
    main()
