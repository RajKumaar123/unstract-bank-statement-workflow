import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from validate_extraction import validate_extraction


def fixture(kind="deposit_account"):
    return {
        "document": {"statement_type": kind, "institution_name": None, "account_holder": None, "account_number": None, "currency": None},
        "statement_period": {"statement_date": "2024-01-01", "period_start": "2024-01-01", "period_end": "2024-01-31"},
        "account_summary": {"opening_balance": "100.00", "closing_balance": "110.00", "total_credits": "20.00", "total_debits": "10.00"},
        "credit_card_summary": {"previous_balance": None, "new_balance": None, "payments_credits": None, "purchases_advances": None, "minimum_payment_due": None, "payment_due_date": None, "credit_limit": None, "total_amount_due": None},
        "transactions": [{"date": "2024-01-02", "description": None, "reference": None, "credit": "20.00", "debit": None, "amount": None, "balance": "120.00"}, {"date": "2024-01-03", "description": None, "reference": None, "credit": None, "debit": "10.00", "amount": None, "balance": "110.00"}],
    }


class ValidatorTests(unittest.TestCase):
    def test_valid_deposit_and_reconciliation(self):
        r = validate_extraction(fixture()); self.assertEqual(r["validation_status"], "pass"); self.assertEqual(r["metrics"]["reconciliation"]["passed"], 2)

    def test_valid_credit_card(self):
        x = fixture("credit_card"); x["account_summary"] = {k: None for k in x["account_summary"]}; x["credit_card_summary"]["new_balance"] = "100.00"; self.assertEqual(validate_extraction(x)["validation_status"], "pass")

    def test_schema_missing_nested_unexpected_and_type(self):
        x = fixture(); del x["document"]["currency"]; x["transactions"][0]["extra"] = None; x["transactions"][1]["amount"] = 1
        r = validate_extraction(x); ids = {i["rule_id"] for i in r["issues"]}; self.assertEqual(r["validation_status"], "invalid"); self.assertTrue({"SCHEMA_MISSING_KEY", "SCHEMA_UNEXPECTED_KEY", "SCHEMA_INVALID_TYPE"} <= ids)

    def test_root_invalid_and_statement_type(self):
        self.assertEqual(validate_extraction(None)["validation_status"], "invalid")
        x = fixture(); x["document"]["statement_type"] = "other"; self.assertEqual(validate_extraction(x)["validation_status"], "invalid")
        x["document"]["statement_type"] = None; self.assertEqual(validate_extraction(x)["validation_status"], "review_required")

    def test_summary_conflict(self):
        x = fixture(); x["credit_card_summary"]["new_balance"] = "1.00"; self.assertEqual(validate_extraction(x)["validation_status"], "review_required")

    def test_dates(self):
        x = fixture(); x["transactions"][0]["date"] = "01/02/2024"; x["transactions"][1]["date"] = "2024-02-30"; x["statement_period"]["period_start"] = "2024-02-01"; x["statement_period"]["period_end"] = "2024-01-01"
        ids = {i["rule_id"] for i in validate_extraction(x)["issues"]}; self.assertTrue({"DATE_INVALID_FORMAT", "DATE_INVALID_CALENDAR", "PERIOD_ORDER_INVALID"} <= ids)
        x["transactions"][0]["date"] = None; self.assertIn("TRANSACTION_DATE_MISSING", {i["rule_id"] for i in validate_extraction(x)["issues"]})

    def test_money_grouping_and_nonfinite(self):
        x = fixture(); x["account_summary"]["opening_balance"] = "3,90,000.00"; self.assertFalse(any(i["rule_id"] == "MONEY_INVALID_GROUPING" for i in validate_extraction(x)["issues"]))
        x["account_summary"]["opening_balance"] = "12,34,56"; self.assertIn("MONEY_INVALID_GROUPING", {i["rule_id"] for i in validate_extraction(x)["issues"]})
        x["account_summary"]["opening_balance"] = "NaN"; self.assertIn("MONEY_INVALID_FORMAT", {i["rule_id"] for i in validate_extraction(x)["issues"]})

    def test_currency_prefix_regressions(self):
        x = fixture("credit_card"); x["account_summary"] = {k: None for k in x["account_summary"]}
        card = x["credit_card_summary"]
        for key, value in {"previous_balance": "$1,234.56", "new_balance": "$1234.56", "payments_credits": "-$1,234.56", "purchases_advances": "$3,90,000.00", "minimum_payment_due": "$10.00", "credit_limit": "$5,000"}.items(): card[key] = value
        before = copy.deepcopy(x); report = validate_extraction(x); ids = {i["rule_id"] for i in report["issues"]}
        self.assertNotIn("MONEY_INVALID_FORMAT", ids); self.assertNotIn("MONEY_INVALID_GROUPING", ids); self.assertEqual(x, before); json.dumps(report)
        for value in ("$ -1.00", "- $1.00"):
            card["new_balance"] = value; self.assertNotIn("MONEY_INVALID_FORMAT", {i["rule_id"] for i in validate_extraction(x)["issues"]})

    def test_currency_prefix_rejections(self):
        x = fixture("credit_card"); x["account_summary"] = {k: None for k in x["account_summary"]}; card = x["credit_card_summary"]
        for value, rule in (("$1,23.45", "MONEY_INVALID_GROUPING"), ("USD1.00", "MONEY_INVALID_FORMAT"), ("€1.00", "MONEY_INVALID_FORMAT"), ("$$1.00", "MONEY_INVALID_FORMAT"), ("--$1.00", "MONEY_INVALID_FORMAT"), ("$1,234,56", "MONEY_INVALID_GROUPING"), ("$NaN", "MONEY_INVALID_FORMAT")):
            card["new_balance"] = value; self.assertIn(rule, {i["rule_id"] for i in validate_extraction(x)["issues"]})

    def test_credit_card_summary_does_not_reconcile_deposit_summary(self):
        x = fixture("credit_card"); x["account_summary"] = {k: None for k in x["account_summary"]}; x["transactions"] = []; x["credit_card_summary"]["new_balance"] = "$1.00"
        r = validate_extraction(x); self.assertEqual(r["metrics"]["reconciliation"]["performed"], 0); self.assertEqual(r["metrics"]["reconciliation"]["skipped"], 1)

    def test_amount_semantics_missing_conflict_and_count(self):
        x = fixture(); x["transactions"][0]["debit"] = "1"; x["transactions"][0]["amount"] = "2"; x["transactions"][1]["credit"] = "1"; x["transactions"][1]["debit"] = "2"; x["transactions"].append({k: None for k in ["date", "description", "reference", "credit", "debit", "amount", "balance"]})
        ids = {i["rule_id"] for i in validate_extraction(x, expected_transaction_count=2)["issues"]}; self.assertIn("TRANSACTION_AMOUNT_CONFLICT", ids); self.assertIn("TRANSACTION_AMOUNT_MISSING", ids); self.assertIn("TRANSACTION_COUNT_MISMATCH", ids)

    def test_nontransaction_and_period(self):
        x = fixture(); x["transactions"][0].update({"date": None, "credit": None, "debit": None, "amount": None, "balance": "1", "description": "Balance brought forward"}); self.assertIn("POSSIBLE_NON_TRANSACTION_ROW", {i["rule_id"] for i in validate_extraction(x)["issues"]})

    def test_failed_reconciliation_and_ambiguous_skip(self):
        x = fixture(); x["account_summary"]["closing_balance"] = "999"; r = validate_extraction(x); self.assertIn("SUMMARY_RECONCILIATION_FAILED", {i["rule_id"] for i in r["issues"]})
        x = fixture(); x["transactions"][0]["amount"] = "20"; x["transactions"][0]["credit"] = None; r = validate_extraction(x); self.assertGreater(r["metrics"]["reconciliation"]["skipped"], 0)

    def test_immutability_serialization_and_messages(self):
        x = fixture(); before = copy.deepcopy(x); r = validate_extraction(x); self.assertEqual(x, before); json.dumps(r); self.assertTrue(all("100.00" not in i["message"] for i in r["issues"]))

    def test_cli_errors_and_smoke(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "input.json"; out = Path(d) / "out.json"; p.write_text(json.dumps(fixture()))
            cmd = [sys.executable, "src/validate_extraction.py", "--input", str(p), "--output", str(out), "--document-id", "synthetic"]
            self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 0); self.assertEqual(json.loads(out.read_text())["validation_status"], "pass")
            self.assertNotEqual(subprocess.run([*cmd[:-2], str(p), "--document-id", "synthetic"], capture_output=True).returncode, 0)
            bad = Path(d) / "bad.json"; bad.write_text("{"); self.assertNotEqual(subprocess.run([sys.executable, "src/validate_extraction.py", "--input", str(bad), "--output", str(out)], capture_output=True).returncode, 0)

if __name__ == "__main__": unittest.main()
