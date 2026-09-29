import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from evaluate_extraction_v2 import compare, V1_FIELDS, V2_FIELDS

def doc():
    return {"document":{"statement_type":"deposit_account","institution_name":None,"account_holder":None,"account_number":None,"currency":None},"statement_period":{"statement_date":None,"period_start":None,"period_end":None},"account_summary":{"opening_balance":None,"closing_balance":None,"total_credits":None,"total_debits":None},"credit_card_summary":{"previous_balance":None,"new_balance":None,"payments_credits":None,"purchases_advances":None,"minimum_payment_due":None,"payment_due_date":None,"credit_limit":None,"total_amount_due":None},"transactions":[{"date":"2024-01-01","description":"Narrative","payment_type":"Transfer","reference":"REF-1","credit":"10.00","debit":None,"amount":None,"balance":"10.00"}]}

class SchemaV2Tests(unittest.TestCase):
    def test_v2_field_and_legacy_views(self):
        x=doc(); r=compare(x,x,V2_FIELDS); self.assertEqual(r['transactions']['fields_correct'],8); self.assertEqual(r['transactions']['fully_correct_rows'],1); self.assertEqual(compare(x,x,V1_FIELDS)['transactions']['fields_correct'],7); json.dumps(r)
    def test_missing_payment_type_is_not_correct(self):
        x=doc(); del x['transactions'][0]['payment_type']; r=compare(doc(),x,V2_FIELDS); self.assertEqual(r['transactions']['fields_correct'],7); self.assertTrue(any(m['path'].endswith('.payment_type') for m in r['mismatches']))
    def test_input_shape_is_unchanged(self):
        x=doc(); before=copy.deepcopy(x); compare(x,x,V2_FIELDS); self.assertEqual(x,before)

    def test_v2_accepts_populated_and_null_payment_type_shapes(self):
        for value in ("Transfer", None):
            x=doc(); x["transactions"][0]["payment_type"]=value; self.assertIn(value, ("Transfer", None))

    def test_v1_contract_remains_seven_fields(self):
        self.assertEqual(V1_FIELDS,["date","description","reference","credit","debit","amount","balance"])

    def test_v2_adds_only_payment_type(self):
        self.assertEqual(set(V2_FIELDS)-set(V1_FIELDS),{"payment_type"})

    def run_validator(self, value):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"; out=Path(d)/"report.json"; src.write_text(json.dumps(value))
            result=subprocess.run([sys.executable,"src/validate_extraction_v2.py","--input",str(src),"--output",str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0); return json.loads(out.read_text())

    def test_v2_validator_accepts_string_and_explicit_null(self):
        for value in ("Transfer",None):
            x=doc(); x["transactions"][0]["payment_type"]=value; self.assertNotEqual(self.run_validator(x)["validation_status"],"invalid")

    def test_v2_validator_rejects_missing_invalid_type_and_unexpected_key(self):
        x=doc(); del x["transactions"][0]["payment_type"]; self.assertIn("SCHEMA_V2_MISSING_KEY",{i["rule_id"] for i in self.run_validator(x)["issues"]})
        x=doc(); x["transactions"][0]["payment_type"]=7; self.assertIn("SCHEMA_V2_INVALID_TYPE",{i["rule_id"] for i in self.run_validator(x)["issues"]})
        x=doc(); x["transactions"][0]["unexpected"]=None; self.assertIn("SCHEMA_UNEXPECTED_KEY",{i["rule_id"] for i in self.run_validator(x)["issues"]})

if __name__=='__main__': unittest.main()
