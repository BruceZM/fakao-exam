"""Build a compact, evidence-backed readiness report for the legal-exam KB."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    totals={}
    for key,sql in {
        'sources':'select count(*) from sources','questions':'select count(*) from questions','options':'select count(*) from options','knowledge_links':'select count(*) from question_knowledge_points','statute_links':'select count(*) from question_statutes','fts_rows':'select count(*) from questions_fts',
        'answered':'select count(*) from questions where answer is not null and trim(answer)<>""','explained':'select count(*) from questions where explanation is not null and trim(explanation)<>""','needs_review':'select count(*) from questions where review_status<>"reviewed"','questions_with_knowledge':'select count(distinct question_id) from question_knowledge_points','questions_with_statute':'select count(distinct question_id) from question_statutes','missing_year':'select count(*) from questions where year is null','missing_source_page':'select count(*) from questions where source_page is null'}.items(): totals[key]=con.execute(sql).fetchone()[0]
    totals['materials'] = con.execute('select count(*) from materials').fetchone()[0]
    totals['reference_documents'] = con.execute('select count(*) from reference_documents').fetchone()[0]
    totals['reference_documents_fts_rows'] = con.execute('select count(*) from reference_documents_fts').fetchone()[0]
    for status, count in con.execute('select status,count(*) from materials group by status'):
        totals[f'materials_{status}'] = count
    subjects=[]
    for r in con.execute('select subject,count(*) n,sum(case when answer is not null and trim(answer)<>"" then 1 else 0 end) answered,sum(case when explanation is not null and trim(explanation)<>"" then 1 else 0 end) explained from questions group by subject order by n desc'):
        row=dict(r)
        row['answer_rate']=round(row['answered']/row['n'],4) if row['n'] else 0
        row['explanation_rate']=round(row['explained']/row['n'],4) if row['n'] else 0
        row['sources']=con.execute('select count(*) from sources where subject=?',(row['subject'],)).fetchone()[0]
        row['tagged_questions']=con.execute('select count(distinct q.question_id) from questions q join question_knowledge_points k on k.question_id=q.question_id where q.subject=?',(row['subject'],)).fetchone()[0]
        row['untagged_questions']=row['n']-row['tagged_questions']
        row['tag_rate']=round(row['tagged_questions']/row['n'],4) if row['n'] else 0
        subjects.append(row)
    stages=[dict(r) for r in con.execute('select stage,count(*) as n from questions group by stage order by n desc')]
    question_types=[dict(r) for r in con.execute('select question_type,count(*) as n from questions group by question_type order by n desc')]
    result={'schema_version':1,'status':'knowledge_base_readiness_report','totals':totals,'coverage':{'answer_rate':round(totals['answered']/totals['questions'],4) if totals['questions'] else 0,'explanation_rate':round(totals['explained']/totals['questions'],4) if totals['questions'] else 0,'knowledge_link_rate':round(totals['questions_with_knowledge']/totals['questions'],4) if totals['questions'] else 0,'statute_link_rate':round(totals['questions_with_statute']/totals['questions'],4) if totals['questions'] else 0},'subjects':subjects,'stages':stages,'question_types':question_types,'notes':['所有资料已完成文件级扫描归档；重复候选和 OCR/答案问题仍需人工复核。','参考笔记已登记为来源，不直接伪装成题目或标准答案。','覆盖率按当前结构化题目计算，不代表法律正确性或商业授权已确认。','objective_subjective_common 表示原资料同时包含客观与主观训练内容，组卷时应按 question_type 进一步筛选。']}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f"questions={totals['questions']} subjects={len(subjects)} output={args.output}")
if __name__=='__main__': main()
