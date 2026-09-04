"""Verify every scanned archive directory is represented by a source or reference document."""
from __future__ import annotations

import argparse, json, sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--db', type=Path, required=True); ap.add_argument('--output', type=Path, required=True); a=ap.parse_args()
    dirs=sorted(p for p in (a.root/'docs_materials/review/scanned').iterdir() if p.is_dir())
    db=sqlite3.connect(a.db)
    source_paths={r[0] for r in db.execute('select archive_path from sources where archive_path is not null')}
    ref_paths={r[0] for r in db.execute('select path from reference_documents')}
    missing=[]
    for d in dirs:
        rel=str(d.relative_to(a.root))
        mapped=any(rel==p or rel.startswith(p+'/') for p in source_paths) or any(rel==p or rel.startswith(p+'/') or p.startswith(rel+'/') for p in ref_paths)
        if not mapped: missing.append(rel)
    report={'schema_version':1,'status':'validated' if not missing else 'needs_review','summary':{'scanned_archive_directories':len(dirs),'mapped':len(dirs)-len(missing),'unmapped':len(missing)},'unmapped':missing}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(report['summary'])
    if missing: raise SystemExit(1)

if __name__=='__main__': main()
