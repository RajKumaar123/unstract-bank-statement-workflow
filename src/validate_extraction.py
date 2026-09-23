"""Deterministic validation for canonical bank-statement extraction JSON."""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SECTIONS = {
    "document": ["statement_type", "institution_name", "account_holder", "account_number", "currency"],
    "statement_period": ["statement_date", "period_start", "period_end"],
    "account_summary": ["opening_balance", "closing_balance", "total_credits", "total_debits"],
    "credit_card_summary": ["previous_balance", "new_balance", "payments_credits", "purchases_advances", "minimum_payment_due", "payment_due_date", "credit_limit", "total_amount_due"],
}
TX_FIELDS = ["date", "description", "reference", "credit", "debit", "amount", "balance"]
MONEY_FIELDS = {
    "account_summary": ["opening_balance", "closing_balance", "total_credits", "total_debits"],
    "credit_card_summary": ["previous_balance", "new_balance", "payments_credits", "purchases_advances", "minimum_payment_due", "credit_limit", "total_amount_due"],
    "transaction": ["credit", "debit", "amount", "balance"],
}
DATE_FIELDS = {"statement_date", "period_start", "period_end", "payment_due_date", "date"}
SCALAR = (str, type(None))
SUMMARY_FIELDS = {
    "deposit_account": ("credit_card_summary", "account_summary"),
    "credit_card": ("account_summary", "credit_card_summary"),
}

def _issue(issues, rule_id, severity, path, message, review=True):
    issues.append({"rule_id": rule_id, "severity": severity, "path": path, "message": message, "review_required": review})

def _money(value: str, path: str, issues) -> Decimal | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    # The extraction contract permits the documented dollar symbol only.
    # Sign-before-symbol and symbol-before-sign are both accepted, with
    # optional whitespace between prefix components. The source string stays intact.
    prefix = re.match(r"^(?:(?:([+-])\s*(\$)?)|(?:(\$)\s*([+-])?)|())\s*", s)
    if not prefix:
        _issue(issues, "MONEY_INVALID_FORMAT", "error", path, "Monetary value has an unsupported prefix.")
        return None
    sign = prefix.group(1) or prefix.group(4)
    symbol = prefix.group(2) or prefix.group(3)
    numeric = s[prefix.end():]
    if not numeric or re.search(r"[+$]", numeric) or (sign and re.search(r"[+-]", numeric)):
        _issue(issues, "MONEY_INVALID_FORMAT", "error", path, "Monetary value has an unsupported prefix.")
        return None
    if not re.fullmatch(r"(?:\d+(?:\.\d+)?|\d{1,3}(?:,\d{2})+,\d{3}(?:\.\d+)?|\d{1,3}(?:,\d{3})+(?:\.\d+)?)", numeric):
        _issue(issues, "MONEY_INVALID_GROUPING" if "," in s else "MONEY_INVALID_FORMAT", "error", path, "Monetary value has an unsupported representation.")
        return None
    raw = numeric
    if "," in raw:
        groups = raw.split(".")[0].split(",")
        if len(groups) > 1 and len(groups[1]) in (2,):
            pass  # explicitly supported Indian grouping
        elif not all(len(g) == 3 for g in groups[1:]):
            _issue(issues, "MONEY_INVALID_GROUPING", "error", path, "Monetary grouping is not supported.")
            return None
    try:
        parsed = Decimal(("-" if sign == "-" else "") + numeric.replace(",", ""))
    except InvalidOperation:
        _issue(issues, "MONEY_INVALID_FORMAT", "error", path, "Monetary value has an unsupported representation.")
        return None
    if not parsed.is_finite():
        _issue(issues, "MONEY_NON_FINITE", "error", path, "Monetary value is not finite.")
        return None
    return parsed

def _valid_date(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and _try_date(value) is not None

def _try_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None

def validate_extraction(extraction: dict, *, document_id: str | None = None, expected_transaction_count: int | None = None) -> dict:
    """Return a JSON-serializable validation report without mutating *extraction*."""
    issues = []
    structural = False
    if not isinstance(extraction, dict):
        _issue(issues, "SCHEMA_INVALID_ROOT", "error", "$", "Extraction root must be an object.")
        return _report(document_id, expected_transaction_count, 0, issues, 0, 0, 0, 0)
    for section, keys in SECTIONS.items():
        if section not in extraction:
            _issue(issues, "SCHEMA_MISSING_KEY", "error", section, "Required section is missing."); structural = True; continue
        obj = extraction[section]
        if not isinstance(obj, dict):
            _issue(issues, "SCHEMA_INVALID_TYPE", "error", section, "Section must be an object."); structural = True; continue
        for key in keys:
            path = f"{section}.{key}"
            if key not in obj:
                _issue(issues, "SCHEMA_MISSING_KEY", "error", path, "Required key is missing."); structural = True
            elif not isinstance(obj[key], SCALAR):
                _issue(issues, "SCHEMA_INVALID_TYPE", "error", path, "Field must be a string or null."); structural = True
        for key in obj:
            if key not in keys:
                _issue(issues, "SCHEMA_UNEXPECTED_KEY", "error", f"{section}.{key}", "Unexpected key."); structural = True
    txs = extraction.get("transactions")
    if not isinstance(txs, list):
        _issue(issues, "SCHEMA_INVALID_TYPE", "error", "transactions", "Transactions must be an array."); structural = True; txs = []
    for i, tx in enumerate(txs):
        path = f"transactions[{i}]"
        if not isinstance(tx, dict):
            _issue(issues, "SCHEMA_INVALID_TYPE", "error", path, "Transaction must be an object."); structural = True; continue
        for key in TX_FIELDS:
            p = f"{path}.{key}"
            if key not in tx:
                _issue(issues, "SCHEMA_MISSING_KEY", "error", p, "Required key is missing."); structural = True
            elif not isinstance(tx[key], SCALAR):
                _issue(issues, "SCHEMA_INVALID_TYPE", "error", p, "Field must be a string or null."); structural = True
        for key in tx:
            if key not in TX_FIELDS:
                _issue(issues, "SCHEMA_UNEXPECTED_KEY", "error", f"{path}.{key}", "Unexpected key."); structural = True
    if structural:
        return _report(document_id, expected_transaction_count, len(txs), issues, 0, 0, 0, 0, structural=True)
    doc = extraction["document"]; period = extraction["statement_period"]; account = extraction["account_summary"]; card = extraction["credit_card_summary"]
    st = doc["statement_type"]
    if st is None: _issue(issues, "STATEMENT_TYPE_MISSING", "warning", "document.statement_type", "Statement type is missing.")
    elif st not in SUMMARY_FIELDS: _issue(issues, "STATEMENT_TYPE_UNSUPPORTED", "error", "document.statement_type", "Statement type is unsupported.")
    else:
        wrong, _ = SUMMARY_FIELDS[st]
        for key, value in extraction[wrong].items():
            if value is not None: _issue(issues, "SUMMARY_TYPE_CONFLICT", "warning", f"{wrong}.{key}", "Field is populated for the other statement type.")
    dates = [(f"statement_period.{k}", period[k]) for k in SECTIONS["statement_period"]] + [("credit_card_summary.payment_due_date", card["payment_due_date"])]
    for i, tx in enumerate(txs): dates.append((f"transactions[{i}].date", tx["date"]))
    for path, value in dates:
        if value is None:
            if path.startswith("transactions["): _issue(issues, "TRANSACTION_DATE_MISSING", "warning", path, "Transaction date is missing.")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value): _issue(issues, "DATE_INVALID_FORMAT", "warning", path, "Date is not in YYYY-MM-DD format.")
        elif _try_date(value) is None: _issue(issues, "DATE_INVALID_CALENDAR", "warning", path, "Date is not a valid calendar date.")
    if _valid_date(period["period_start"]) and _valid_date(period["period_end"]):
        if date.fromisoformat(period["period_start"]) > date.fromisoformat(period["period_end"]): _issue(issues, "PERIOD_ORDER_INVALID", "warning", "statement_period", "Statement period is reversed.")
        for i, tx in enumerate(txs):
            d = _try_date(tx["date"])
            if d and not (date.fromisoformat(period["period_start"]) <= d <= date.fromisoformat(period["period_end"])): _issue(issues, "TRANSACTION_OUTSIDE_PERIOD", "warning", f"transactions[{i}].date", "Transaction date falls outside the statement period.")
    parsed = {}
    for section, keys in MONEY_FIELDS.items():
        if section == "transaction": continue
        obj = extraction[section]
        for key in keys:
            if obj[key] is not None: parsed[f"{section}.{key}"] = _money(obj[key], f"{section}.{key}", issues)
    for i, tx in enumerate(txs):
        for key in MONEY_FIELDS["transaction"]:
            if tx[key] is not None: parsed[f"transactions[{i}].{key}"] = _money(tx[key], f"transactions[{i}].{key}", issues)
        populated = [k for k in ("credit", "debit", "amount") if tx[k] is not None]
        if len(populated) == 0: _issue(issues, "TRANSACTION_AMOUNT_MISSING", "warning", f"transactions[{i}]", "Transaction has no amount representation.")
        if tx["credit"] is not None and tx["debit"] is not None: _issue(issues, "TRANSACTION_AMOUNT_CONFLICT", "warning", f"transactions[{i}]", "Credit and debit are both populated.")
        if tx["amount"] is not None and (tx["credit"] is not None or tx["debit"] is not None): _issue(issues, "TRANSACTION_AMOUNT_CONFLICT", "warning", f"transactions[{i}]", "Generic amount conflicts with credit or debit.")
        signals = (tx["date"] is None, not populated, tx["balance"] is not None, isinstance(tx["description"], str) and bool(re.search(r"\b(balance|brought forward|carry forward|summary|total|opening|closing)\b", tx["description"], re.I)))
        if sum(signals) >= 3: _issue(issues, "POSSIBLE_NON_TRANSACTION_ROW", "warning", f"transactions[{i}]", "Row has multiple non-transaction structural signals.")
    if expected_transaction_count is not None and len(txs) != expected_transaction_count: _issue(issues, "TRANSACTION_COUNT_MISMATCH", "warning", "transactions", "Transaction count differs from the explicitly supplied expected count.")
    performed = passed = failed = skipped = 0
    if st == "deposit_account" and all(parsed.get(f"account_summary.{k}") is not None for k in MONEY_FIELDS["account_summary"]):
        performed += 1; lhs = parsed["account_summary.opening_balance"] + parsed["account_summary.total_credits"] - parsed["account_summary.total_debits"]
        if lhs == parsed["account_summary.closing_balance"]: passed += 1
        else: failed += 1; _issue(issues, "SUMMARY_RECONCILIATION_FAILED", "warning", "account_summary", "Deposit-account summary does not reconcile.")
    else: skipped += 1
    for i, tx in enumerate(txs):
        if tx["balance"] is None or (tx["credit"] is None and tx["debit"] is None) or (tx["credit"] is not None and tx["debit"] is not None): skipped += 1; continue
        if i == 0: skipped += 1; continue
        prev = parsed.get(f"transactions[{i-1}].balance"); bal = parsed.get(f"transactions[{i}].balance"); val = parsed.get(f"transactions[{i}].credit") if tx["credit"] is not None else parsed.get(f"transactions[{i}].debit")
        if prev is None or bal is None or val is None: skipped += 1; continue
        performed += 1; expected = prev + val if tx["credit"] is not None else prev - val
        if expected == bal: passed += 1
        else: failed += 1; _issue(issues, "RUNNING_BALANCE_RECONCILIATION_FAILED", "warning", f"transactions[{i}].balance", "Running balance does not reconcile.")
    return _report(document_id, expected_transaction_count, len(txs), issues, performed, passed, failed, skipped)

def _report(document_id, expected, count, issues, performed, passed, failed, skipped, structural=False):
    blocking = structural or any(i["severity"] == "error" for i in issues)
    review = any(i["review_required"] for i in issues)
    status = "invalid" if blocking else ("review_required" if review else "pass")
    return {"validator_version": VERSION, "document_id": document_id, "validation_status": status, "review_required": review or blocking, "issue_count": len(issues), "issues": issues, "metrics": {"transaction_count": count, "expected_transaction_count": expected, "reconciliation": {"performed": performed, "passed": passed, "failed": failed, "skipped": skipped}}}

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path); p.add_argument("--output", required=True, type=Path); p.add_argument("--document-id"); p.add_argument("--expected-transaction-count", type=int)
    args = p.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve(): raise ValueError("input and output must be different files")
        with args.input.open(encoding="utf-8") as f: extraction = json.load(f)
        report = validate_extraction(extraction, document_id=args.document_id, expected_transaction_count=args.expected_transaction_count)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"validation_status": report["validation_status"], "issue_count": report["issue_count"], "transaction_count": report["metrics"]["transaction_count"]}))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"validation execution error: {exc}", file=sys.stderr); return 2

if __name__ == "__main__": sys.exit(main())
