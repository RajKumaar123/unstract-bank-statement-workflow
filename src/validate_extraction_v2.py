"""Validate Schema V2 JSON through an explicit V1 compatibility adapter."""
from __future__ import annotations
import argparse, copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from validate_extraction import validate_extraction

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--output',required=True,type=Path); p.add_argument('--document-id'); p.add_argument('--expected-transaction-count',type=int); a=p.parse_args()
    if a.input.resolve()==a.output.resolve(): raise SystemExit('input and output must differ')
    source=json.loads(a.input.read_text(encoding='utf-8')); work=copy.deepcopy(source); issues=[]
    txs=work.get('transactions',[]) if isinstance(work,dict) and isinstance(work.get('transactions'),list) else []
    for i,row in enumerate(txs):
        if not isinstance(row,dict): continue
        path=f'transactions[{i}].payment_type'
        if 'payment_type' not in row: issues.append({'rule_id':'SCHEMA_V2_MISSING_KEY','severity':'error','path':path,'message':'Schema V2 transaction key is missing.','review_required':True})
        elif row['payment_type'] is not None and not isinstance(row['payment_type'],str): issues.append({'rule_id':'SCHEMA_V2_INVALID_TYPE','severity':'error','path':path,'message':'Payment type must be a string or null.','review_required':True})
        if 'payment_type' in row:
            del row['payment_type']
    report=validate_extraction(work,document_id=a.document_id,expected_transaction_count=a.expected_transaction_count)
    report['validator_version']='2.0.0'; report['schema_version']='2'; report['issues']=issues+report['issues']; report['issue_count']=len(report['issues'])
    if issues: report['validation_status']='invalid'
    report['review_required']=bool(report['issues'])
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); return 0

if __name__=='__main__': raise SystemExit(main())
