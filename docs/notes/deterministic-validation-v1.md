# Deterministic Validation Layer V1

## Purpose and scope

This layer validates already parsed canonical extraction JSON. It does not extract text, repair values, call an LLM, require ground truth, or replace the strict benchmark evaluator. It returns structured issues and conservative review signals.

## Interface and CLI

The public function is:

```python
validate_extraction(extraction: dict, *, document_id: str | None = None, expected_transaction_count: int | None = None) -> dict
```

The input dictionary is never mutated. The optional expected count is accepted only when explicitly supplied by an authorized caller; it is never inferred.

```powershell
python src/validate_extraction.py --input INPUT.json --output REPORT.json --document-id document-04 --expected-transaction-count 9
```

The CLI prints only status, issue count, and transaction count. It returns 0 for a successfully executed validation, including `review_required` or `invalid` findings, and 2 for malformed JSON, identical input/output paths, or other execution errors.

## Report and status semantics

Reports contain `validator_version`, `document_id`, `validation_status`, `review_required`, `issue_count`, `issues`, and metrics. Status precedence is: structural/schema errors or other error-severity findings produce `invalid`; otherwise any review-required issue produces `review_required`; otherwise status is `pass`. A blocking invalid result always sets `review_required` to true.

Each issue contains a stable `rule_id`, severity, field path, privacy-safe message, and `review_required` flag. Messages never include source values.

## Rule groups

- Schema: `SCHEMA_INVALID_ROOT`, `SCHEMA_MISSING_KEY`, `SCHEMA_UNEXPECTED_KEY`, `SCHEMA_INVALID_TYPE`.
- Statement semantics: `STATEMENT_TYPE_MISSING`, `STATEMENT_TYPE_UNSUPPORTED`, `SUMMARY_TYPE_CONFLICT`.
- Dates: `DATE_INVALID_FORMAT`, `DATE_INVALID_CALENDAR`, `TRANSACTION_DATE_MISSING`, `PERIOD_ORDER_INVALID`, `TRANSACTION_OUTSIDE_PERIOD`.
- Money: `MONEY_INVALID_FORMAT`, `MONEY_INVALID_GROUPING`, `MONEY_NON_FINITE`.
- Transactions: `TRANSACTION_AMOUNT_CONFLICT`, `TRANSACTION_AMOUNT_MISSING`.
- Row detection: `POSSIBLE_NON_TRANSACTION_ROW`, `TRANSACTION_COUNT_MISMATCH`.
- Reconciliation: `SUMMARY_RECONCILIATION_FAILED`, `RUNNING_BALANCE_RECONCILIATION_FAILED`.

## Dates and money

Non-null dates must use exact `YYYY-MM-DD` syntax and pass strict calendar parsing. Null transaction dates are review candidates; null statement-level dates remain allowed. Period order is checked when both endpoints are valid, and valid transaction dates outside a valid period are warnings. The validator does not decide whether an ambiguous date was semantically interpreted correctly.

Money is parsed with `decimal.Decimal`, never binary floating point. The dollar symbol (`$`) is the only accepted currency symbol in V1. It may appear before or after an optional sign, with optional whitespace between prefix components; examples include sign-before-symbol and symbol-before-sign forms. Western grouping and explicitly validated Indian-style grouping such as `3,90,000.00` are accepted. Ungrouped decimals are accepted. Malformed grouping, arbitrary alphabetic prefixes, unsupported currency markers, multiple signs or symbols, ambiguous decimal separators, unexpected characters, and non-finite values are rejected. Original extraction strings are never rewritten. The validator does not infer decimal separators, calculate missing values, or expose parsed values in reports. Format validation does not prove that a value is source-supported or semantically correct.

## Reconciliation

Deposit-account summary reconciliation runs only when all four summary values are present and valid: opening plus credits minus debits must equal closing. Running-balance reconciliation runs only for non-first rows with an explicit previous balance, explicit balance, and unambiguous credit or debit representation. Generic amount rows and ambiguous direction are skipped. Metrics report performed, passed, failed, and skipped checks.

## Non-transaction rows and HITL

Rows are never removed or reordered. A row is flagged only when multiple structural signals co-occur, such as a missing date, missing amount representation, populated balance, and generic carry-forward or summary vocabulary. A keyword alone is insufficient. These findings, date ambiguity, count mismatches, semantic conflicts, and reconciliation failures are intended inputs to future HITL routing; HITL itself is not implemented here.

## Limitations and future work

The validator sees structured JSON only and cannot prove whether a populated field appeared in the original PDF. It cannot infer currency, identifiers, dates, totals, or transaction direction. Future work may add source-evidence interfaces, richer layout-aware checks, explicit sign-convention metadata, and workflow routing. This implementation does not claim improved extraction accuracy or completed Unstract integration.
