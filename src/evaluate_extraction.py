"""Evaluate one extraction result against canonical ground truth.

This module intentionally keeps strict comparison authoritative and exposes
normalized comparison only as a diagnostic view.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


NON_TRANSACTION_PATHS = [
    "document.statement_type",
    "document.institution_name",
    "document.account_holder",
    "document.account_number",
    "document.currency",
    "statement_period.statement_date",
    "statement_period.period_start",
    "statement_period.period_end",
    "account_summary.opening_balance",
    "account_summary.closing_balance",
    "account_summary.total_credits",
    "account_summary.total_debits",
    "credit_card_summary.previous_balance",
    "credit_card_summary.new_balance",
    "credit_card_summary.payments_credits",
    "credit_card_summary.purchases_advances",
    "credit_card_summary.minimum_payment_due",
    "credit_card_summary.payment_due_date",
    "credit_card_summary.credit_limit",
    "credit_card_summary.total_amount_due",
]
TRANSACTION_FIELDS = ["date", "description", "reference", "credit", "debit", "amount", "balance"]
MONEY_FIELDS = {
    "account_summary.opening_balance",
    "account_summary.closing_balance",
    "account_summary.total_credits",
    "account_summary.total_debits",
    "credit_card_summary.previous_balance",
    "credit_card_summary.new_balance",
    "credit_card_summary.payments_credits",
    "credit_card_summary.purchases_advances",
    "credit_card_summary.minimum_payment_due",
    "credit_card_summary.credit_limit",
    "credit_card_summary.total_amount_due",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_path(document: dict[str, Any], path: str) -> Any:
    value: Any = document
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def accuracy(correct: int, total: int) -> float:
    return correct / total if total else 0.0


def mismatch_category(expected: Any, actual: Any) -> str:
    if expected is None and actual is not None:
        return "expected_null_predicted_value"
    if expected is not None and actual is None:
        return "expected_value_predicted_null"
    return "exact_value_mismatch"


def strict_value(value: Any) -> Any:
    return value


def parse_money(value: str) -> Decimal | None:
    cleaned = value.strip()
    cleaned = re.sub(r"^[^0-9+\-.(]+", "", cleaned)
    cleaned = cleaned.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    if cleaned.endswith(("+", "-")):
        sign = cleaned[-1]
        cleaned = cleaned[:-1]
        if sign == "-":
            cleaned = "-" + cleaned
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def diagnostic_value(value: Any, path: str) -> Any:
    if not isinstance(value, str):
        return value
    trimmed = value.strip()
    if path in MONEY_FIELDS:
        parsed = parse_money(trimmed)
        return str(parsed) if parsed is not None else trimmed
    return trimmed


def compare_pair(path: str, expected: Any, actual: Any, normalized: bool = False) -> tuple[bool, dict[str, Any] | None]:
    left = diagnostic_value(expected, path) if normalized else strict_value(expected)
    right = diagnostic_value(actual, path) if normalized else strict_value(actual)
    if left == right:
        return True, None
    return False, {
        "path": path,
        "expected": expected,
        "actual": actual,
        "category": mismatch_category(expected, actual),
    }


def compare_view(ground_truth: dict[str, Any], prediction: dict[str, Any], normalized: bool) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    non_total = len(NON_TRANSACTION_PATHS)
    non_correct = 0
    null_counts = {
        "expected_null_predicted_null": 0,
        "expected_null_predicted_value": 0,
        "expected_value_predicted_null": 0,
    }

    for path in NON_TRANSACTION_PATHS:
        expected = get_path(ground_truth, path)
        actual = get_path(prediction, path)
        if expected is None and actual is None:
            null_counts["expected_null_predicted_null"] += 1
        elif expected is None and actual is not None:
            null_counts["expected_null_predicted_value"] += 1
        elif expected is not None and actual is None:
            null_counts["expected_value_predicted_null"] += 1
        correct, mismatch = compare_pair(path, expected, actual, normalized)
        if correct:
            non_correct += 1
        elif mismatch:
            mismatches.append(mismatch)

    expected_transactions = ground_truth.get("transactions", [])
    actual_transactions = prediction.get("transactions", [])
    aligned = min(len(expected_transactions), len(actual_transactions))
    transaction_total = aligned * len(TRANSACTION_FIELDS)
    transaction_correct = 0
    fully_correct_rows = 0

    for index in range(aligned):
        row_correct = True
        expected_row = expected_transactions[index]
        actual_row = actual_transactions[index]
        for field in TRANSACTION_FIELDS:
            path = f"transactions[{index}].{field}"
            expected = expected_row.get(field)
            actual = actual_row.get(field)
            if expected is None and actual is None:
                null_counts["expected_null_predicted_null"] += 1
            elif expected is None and actual is not None:
                null_counts["expected_null_predicted_value"] += 1
            elif expected is not None and actual is None:
                null_counts["expected_value_predicted_null"] += 1
            correct, mismatch = compare_pair(path, expected, actual, normalized)
            if correct:
                transaction_correct += 1
            else:
                row_correct = False
                if mismatch:
                    mismatches.append(mismatch)
        if row_correct:
            fully_correct_rows += 1

    missing_count = max(0, len(expected_transactions) - aligned)
    extra_count = max(0, len(actual_transactions) - aligned)
    if missing_count or extra_count:
        mismatches.append({
            "path": "transactions",
            "expected": len(expected_transactions),
            "actual": len(actual_transactions),
            "category": "transaction_count_mismatch",
        })

    missing_extra_fields = (missing_count + extra_count) * len(TRANSACTION_FIELDS)
    overall_total = non_total + transaction_total + missing_extra_fields
    overall_correct = non_correct + transaction_correct
    return {
        "non_transaction_fields": {
            "total": non_total,
            "correct": non_correct,
            "accuracy": accuracy(non_correct, non_total),
        },
        "transactions": {
            "ground_truth_transaction_count": len(expected_transactions),
            "predicted_transaction_count": len(actual_transactions),
            "transaction_count_match": len(expected_transactions) == len(actual_transactions),
            "aligned_transaction_rows": aligned,
            "missing_transaction_indices": list(range(aligned, len(expected_transactions))),
            "extra_transaction_indices": list(range(aligned, len(actual_transactions))),
            "fields_total": transaction_total + missing_extra_fields,
            "fields_correct": transaction_correct,
            "field_accuracy": accuracy(transaction_correct, transaction_total + missing_extra_fields),
            "fully_correct_rows": fully_correct_rows,
            "fully_correct_row_accuracy": accuracy(fully_correct_rows, aligned),
        },
        "overall": {
            "fields_total": overall_total,
            "fields_correct": overall_correct,
            "field_accuracy": accuracy(overall_correct, overall_total),
        },
        "null_behavior": null_counts,
        "mismatches": mismatches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--prediction", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--document-id", required=True)
    args = parser.parse_args()

    ground_truth = load_json(args.ground_truth)
    prediction = load_json(args.prediction)
    result = {
        "evaluation_metadata": {
            "document_id": args.document_id,
            "evaluation_type": "unstract_baseline",
            "ground_truth_file": str(args.ground_truth),
            "prediction_file": str(args.prediction),
            "ground_truth_sha256": sha256(args.ground_truth),
            "prediction_sha256": sha256(args.prediction),
        },
        "strict": compare_view(ground_truth, prediction, normalized=False),
        "diagnostic_normalized": compare_view(ground_truth, prediction, normalized=True),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
