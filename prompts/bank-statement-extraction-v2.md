# Bank Statement Extraction Prompt — V2

Extract the bank or credit-card statement into the exact canonical JSON structure below.

Return only JSON. Do not wrap the result in Markdown or add explanatory text. Return only information supported by the source document. Do not guess, calculate, derive, repair, or fabricate values.

```json
{
  "document": {"statement_type": null, "institution_name": null, "account_holder": null, "account_number": null, "currency": null},
  "statement_period": {"statement_date": null, "period_start": null, "period_end": null},
  "account_summary": {"opening_balance": null, "closing_balance": null, "total_credits": null, "total_debits": null},
  "credit_card_summary": {"previous_balance": null, "new_balance": null, "payments_credits": null, "purchases_advances": null, "minimum_payment_due": null, "payment_due_date": null, "credit_limit": null, "total_amount_due": null},
  "transactions": [{"date": null, "description": null, "reference": null, "credit": null, "debit": null, "amount": null, "balance": null}]
}
```

## 1. Output and source-fidelity rules

1. Return every key shown above, even when its value is null. Do not add keys, metadata, confidence scores, evidence snippets, review flags, validation results, or normalized fields.
2. Use `deposit_account` or `credit_card` for `document.statement_type` only when supported by the document. Otherwise return null.
3. Preserve identifiers such as account numbers and references as strings exactly as printed. Never infer an account or card number from another identifier.
4. Preserve monetary values as source-supported strings. Do not calculate missing totals, balances, or transaction values.
5. Use null for absent, unsupported, ambiguous, or inapplicable fields. Do not use external banking knowledge to fill gaps.
6. Do not infer currency from an institution, address, country, number format, or general knowledge. Populate it only when explicitly supported by the document.
7. Exclude handwritten annotations and user-added markings unless they are clearly part of the original authoritative statement.

## 2. Statement semantics

1. Keep deposit-account summary fields and credit-card summary fields separate. Do not map `new_balance` to `closing_balance`, or `closing_balance` to `new_balance`.
2. Do not infer a statement date from a period end, and do not fabricate opening or closing balances.
3. Populate only summary fields explicitly supported by the source. A field may remain null even when a similar field exists elsewhere in the document.

## 3. Date interpretation

1. Return dates only as `YYYY-MM-DD` when the interpretation is supported by unambiguous source evidence. Validate that the resulting date is a real calendar date.
2. Use document-wide evidence before interpreting an ambiguous date: examine explicit headers, labels, unambiguous dates, statement-period context, ordering, and consistent formatting within the same document.
3. Distinguish `DD/MM/YYYY` from `MM/DD/YYYY` using source evidence. Never apply a universal day-first or month-first assumption across documents.
4. Use statement-period context to preserve the correct year only when that context supports the interpretation. Do not force a date into the period merely to satisfy the schema.
5. If date interpretation remains genuinely ambiguous, return null. Do not silently convert ambiguous dates, substitute the statement date for a missing transaction date, or invent a date.
6. Statement-level and transaction-level date representations may differ. Resolve each using available document evidence.

## 4. Transaction extraction and order

1. Extract every actual transaction exactly once and preserve source order.
2. Use the visual/table structure and nearby source context when available. Do not rely on flattened text order when it separates columns or wrapped rows.
3. Combine wrapped or multiline text belonging to one transaction into one description. Do not split one transaction into multiple rows or merge adjacent transactions.
4. Do not insert balance, amount, reference, header, or page text into a description. Preserve source-supported description text without rewriting it into an inferred merchant or category.

## 5. Transaction amount semantics

1. When the source has explicit Credit and Debit columns, place the corresponding source value in `credit` or `debit` and leave `amount` null.
2. When the source has one generic or signed Amount column and its direction cannot be reliably mapped to explicit credit/debit semantics, place the source value in `amount` and leave `credit` and `debit` null.
3. Do not duplicate one source value across `amount`, `credit`, and `debit`. For each transaction, populate at most one of these three fields according to the source-supported representation. If the source layout is ambiguous, preserve only the unambiguously supported value; otherwise use null. Never calculate or infer a missing amount.
4. Never infer transaction direction solely from a description, merchant name, sign convention assumed from another document, or general banking knowledge.
5. Preserve `balance` separately and populate it only when a running/resulting transaction balance is explicitly provided. Do not use it as an amount or calculate it.
6. Preserve the source monetary string; do not change grouping, signs, currency markers, or precision at extraction time.

## 6. Excluding non-transaction rows

Do not extract opening-balance rows, balance-brought-forward or carried-forward rows, closing-balance rows, section headers, subtotals, totals, payment instructions, statement summary rows, page headers, or page footers as transactions.

Make this decision from multiple structural signals and source context, not a keyword alone. A genuine transaction must not be excluded merely because its description contains words such as “balance” or “payment”. Do not invent a transaction or add a row to match an expected count.

## 7. Responsibilities and limitations

This prompt performs source-faithful extraction only. Do not claim that deterministic validation has passed, do not add validation results to the JSON, and do not claim reconciliation unless the source explicitly provides the relevant values and the extraction merely preserves them. Structural validation, consistency checks, and review routing are performed by separate downstream components. Unresolved ambiguity remains null for later review.
