"""Compare Schema V1 or V2 extraction JSON without changing historical reports."""
from __future__ import annotations
import argparse, json
from pathlib import Path

V1_FIELDS = ["date", "description", "reference", "credit", "debit", "amount", "balance"]
V2_FIELDS = ["date", "description", "payment_type", "reference", "credit", "debit", "amount", "balance"]
NON_TX = ["document.statement_type", "document.institution_name", "document.account_holder", "document.account_number", "document.currency", "statement_period.statement_date", "statement_period.period_start", "statement_period.period_end", "account_summary.opening_balance", "account_summary.closing_balance", "account_summary.total_credits", "account_summary.total_debits", "credit_card_summary.previous_balance", "credit_card_summary.new_balance", "credit_card_summary.payments_credits", "credit_card_summary.purchases_advances", "credit_card_summary.minimum_payment_due", "credit_card_summary.payment_due_date", "credit_card_summary.credit_limit", "credit_card_summary.total_amount_due"]
def get(d,p):
    x=d
    for k in p.split('.'): x=x.get(k) if isinstance(x,dict) else None
    return x
def compare(gt,pred,fields):
    mismatches=[]; nc=0
    for p in NON_TX:
        if get(gt,p)==get(pred,p): nc+=1
        else: mismatches.append({"path":p,"category":"value_mismatch"})
    rows=min(len(gt.get('transactions',[])),len(pred.get('transactions',[]))); correct=0; full=0
    for i in range(rows):
        good=True
        for f in fields:
            if gt['transactions'][i].get(f)==pred['transactions'][i].get(f): correct+=1
            else: good=False; mismatches.append({"path":f"transactions[{i}].{f}","category":"value_mismatch"})
        if good: full+=1
    extra=abs(len(gt.get('transactions',[]))-len(pred.get('transactions',[])))
    total=len(NON_TX)+rows*len(fields)+extra*len(fields)
    return {"non_transaction_fields":{"correct":nc,"total":len(NON_TX)},"transactions":{"ground_truth_count":len(gt.get('transactions',[])),"predicted_count":len(pred.get('transactions',[])),"fields_correct":correct,"fields_total":rows*len(fields)+extra*len(fields),"fully_correct_rows":full,"fully_correct_row_total":rows},"overall":{"fields_correct":nc+correct,"fields_total":total},"mismatches":mismatches}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ground-truth',required=True,type=Path); p.add_argument('--prediction',required=True,type=Path); p.add_argument('--output',required=True,type=Path); p.add_argument('--document-id',required=True); p.add_argument('--schema-version',choices=['1','2'],default='2'); a=p.parse_args()
    gt=json.loads(a.ground_truth.read_text()); pred=json.loads(a.prediction.read_text()); fields=V2_FIELDS if a.schema_version=='2' else V1_FIELDS
    report={"evaluator_version":"2.0.0","schema_version":a.schema_version,"document_id":a.document_id,"legacy_compatible":compare(gt,pred,V1_FIELDS),"schema_v2":compare(gt,pred,V2_FIELDS)}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__': main()
