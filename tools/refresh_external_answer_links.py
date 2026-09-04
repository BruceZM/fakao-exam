"""Refresh public answer-link candidates without importing answer content."""
from __future__ import annotations
import argparse, datetime, json, re
from pathlib import Path
from urllib.request import urlopen

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=Path('data/provenance/external_answer_link_candidates.json'))
    ap.add_argument('--timeout', type=int, default=20)
    args = ap.parse_args()
    pages = [
        ('qiepeng-en-company-law-daily', 'https://www.sina.cn/news/detail/5305405905046965.html'),
        ('qiepeng-en-partnership', 'https://www.sina.cn/media/2042198575'),
    ]
    items = []
    for source_id, url in pages:
        try:
            html = urlopen(url, timeout=args.timeout).read().decode('utf-8', 'ignore')
        except Exception as exc:
            print(f'fetch_failed source_id={source_id}: {exc}')
            continue
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)
        for match in re.finditer(r'答案\s*([0-9]{1,3})[^\n]{0,180}?(https?://t\.cn/[A-Za-z0-9]+)', text):
            items.append({
                'source_id': source_id,
                'question_no': int(match.group(1)),
                'url': match.group(2),
                'status': 'candidate_unverified',
                'authorization_status': 'unknown',
                'discovered_from': url,
            })
    unique = {(x['source_id'], x['question_no'], x['url']): x for x in items}
    result = {
        'schema_version': 1,
        'status': 'external_answer_link_candidates',
        'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'items': list(unique.values()),
        'notes': '仅记录公开汇总页中的题号与答案短链接；未读取或导入答案正文，需逐条核验。',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"links={len(result['items'])} output={args.output}")

if __name__ == '__main__':
    main()
