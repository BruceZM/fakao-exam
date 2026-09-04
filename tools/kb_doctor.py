from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); a=ap.parse_args(); r=a.root.resolve(); p=r/'data/provenance'; errors=[]
 q=json.loads((p/'material_ingestion_queue.json').read_text());
 if q['summary'].get('pending_scan',0): errors.append('pending_scan_not_zero')
 integ=json.loads((p/'knowledge_base_integrity_report.json').read_text());
 if integ.get('status')!='validated' or integ.get('errors'): errors.append('integrity_not_validated')
 enriched=json.loads((p/'enriched_integrity_report.json').read_text())
 if enriched.get('status')!='validated' or enriched.get('summary',{}).get('errors') or enriched.get('summary',{}).get('duplicate_question_ids'): errors.append('enriched_integrity_not_validated')
 archive=json.loads((p/'archive_mapping_audit.json').read_text())
 if archive.get('status')!='validated' or archive.get('summary',{}).get('unmapped'): errors.append('archive_mapping_not_validated')
 con=sqlite3.connect(r/'data/fakao_knowledge_base.sqlite'); counts={t:con.execute(f'select count(*) from {t}').fetchone()[0] for t in ['questions','questions_fts','reference_documents','reference_documents_fts']}
 if counts['questions']!=counts['questions_fts'] or counts['reference_documents']!=counts['reference_documents_fts']: errors.append('fts_count_mismatch')
 ready=json.loads((p/'knowledge_base_readiness_report.json').read_text()); total=ready['totals']['questions']
 if ready['totals']['questions_with_knowledge']!=total: errors.append('knowledge_point_coverage_incomplete')
 adm=json.loads((p/'product_admission_snapshot.json').read_text());
 rubric_path=p/'rubric_audit.json'
 rubric=json.loads(rubric_path.read_text()) if rubric_path.exists() else {'ok':False,'summary':{}}
 if not rubric.get('ok'): errors.append('rubric_audit_failed')
 link_audit_path=p/'external_answer_link_audit.json'
 link_audit=json.loads(link_audit_path.read_text()) if link_audit_path.exists() else {'ok':False,'summary':{}}
 if not link_audit.get('ok'): errors.append('external_answer_link_audit_failed')
 provenance_path=p/'explanation_provenance_audit.json'
 provenance=json.loads(provenance_path.read_text()) if provenance_path.exists() else {'summary':{},'review_queue':[]}
 if not provenance_path.exists() or provenance.get('summary',{}).get('explained_missing_provenance') != len(provenance.get('review_queue',[])): errors.append('explanation_provenance_audit_mismatch')
 catalog=json.loads((p/'source_catalog.json').read_text())
 source_count=con.execute('select count(*) from sources').fetchone()[0]
 if len(catalog.get('sources',[])) != source_count: errors.append('source_catalog_count_mismatch')
 if sum(x.get('question_count',0) for x in catalog.get('sources',[])) != total: errors.append('source_catalog_question_count_mismatch')
 smoke={'status':'not_run'}
 smoke_path=p/'smoke_test_report.json'
 if smoke_path.exists():
  smoke=json.loads(smoke_path.read_text())
  if smoke.get('status')!='passed': errors.append('smoke_test_failed')
 else: errors.append('smoke_test_report_missing')
 manifest=json.loads((p/'missing_answer_manifest.json').read_text())
 manifest_ids=[x.get('question_id') for x in manifest.get('items',[])]
 db_missing=con.execute("select count(*) from questions where coalesce(trim(answer),'')=''").fetchone()[0]
 if manifest.get('count')!=db_missing or len(manifest_ids)!=len(set(manifest_ids)): errors.append('missing_answer_manifest_mismatch')
 snapshot_path=p/'kb_snapshot_manifest.json'
 if snapshot_path.exists():
  snapshot=json.loads(snapshot_path.read_text())
  if snapshot.get('scope')!='entire_legal_exam_knowledge_base': errors.append('snapshot_scope_mismatch')
 else: errors.append('snapshot_manifest_missing')
 out={'schema_version':1,'status':'kb_doctor','ok':not errors,'errors':errors,'counts':counts,'materials':q['summary'],'archive_mapping':archive['summary'],'enriched_integrity':enriched['summary'],'source_catalog':{'sources':len(catalog.get('sources',[])),'questions':sum(x.get('question_count',0) for x in catalog.get('sources',[]))},'smoke_test':smoke,'rubric_audit':rubric,'external_answer_link_audit':link_audit,'explanation_provenance_audit':provenance.get('summary',{}),'missing_answer_manifest':{'count':manifest.get('count'),'db_missing':db_missing},'questions':{'total':total,'knowledge_points':ready['totals']['questions_with_knowledge'],'answered':ready['totals']['answered'],'explained':ready['totals']['explained']},'product_admission':adm['summary']}
 print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
