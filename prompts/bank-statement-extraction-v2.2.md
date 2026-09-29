# Bank Statement Extraction Prompt — V2.2 / Schema V2

Extract the statement into the exact Schema V2 JSON structure. Return only JSON, with no Markdown or explanation. Use only source-supported information. Never guess, calculate, derive, repair, or fabricate values.

```json
{
  "document": {"statement_type": null, "institution_name": null, "account_holder": null, "account_number": null, "currency": null},
  "statement_period": {"statement_date": null, "period_start": null, "period_end": null},
  "account_summary": {"opening_balance": null, "closing_balance": null, "total_credits": null, "total_debits": null},
  "credit_card_summary": {"previous_balance": null, "new_balance": null, "payments_credits": null, "purchases_advances": null, "minimum_payment_due": null, "payment_due_date": null, "credit_limit": null, "total_amount_due": null},
  "transactions": [{"date": null, "description": null, "payment_type": null, "reference": null, "credit": null, "debit": null, "amount": null, "balance": null}]
}
```

Return all keys, using null for absent, unsupported, or ambiguous values. Extract statement type and metadata only from authoritative source evidence; preserve identifiers as strings; do not infer currency, dates, balances, totals, or direction.

For transactions, preserve source order and extract each actual transaction once. Keep complete wrapped narrative text in `description`. Populate `payment_type` only when the source explicitly presents a separate payment classification. Populate `reference` only for an actual source reference; never use a payment classification as a reference. If the relationship between source columns is ambiguous, preserve only unambiguous fields and use null otherwise.

When Credit and Debit columns are explicit, populate only the corresponding field and leave `amount` null. When a single generic or signed Amount column is provided and direction cannot be mapped reliably, populate only `amount`. Never duplicate a source value across `amount`, `credit`, and `debit`, and never calculate a missing value. Preserve `balance` separately when explicitly provided.

Exclude opening, brought-forward, carried-forward, closing, header, footer, subtotal, total, instruction, and summary rows. Use structure and context rather than keywords alone; do not exclude a genuine transaction merely because its text contains “balance” or “payment”.

Normalize dates to `YYYY-MM-DD` only when document-wide evidence supports the interpretation and the calendar date is valid. Do not assume a universal day/month order, substitute a statement date, or force transaction dates into an inconsistent statement period. Return null when ambiguity remains.

This prompt performs extraction only. Deterministic validation, reconciliation, comparison, and human review are separate downstream responsibilities. Do not add confidence, evidence, validation, or review fields.
