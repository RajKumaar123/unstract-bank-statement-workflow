# Bank Statement Extraction Prompt — V1 Baseline

Extract the bank or credit-card statement into the following canonical JSON structure.

Return only source-supported information. Do not guess, calculate, derive, or fabricate missing values.

```json
{
  "document": {"statement_type": null, "institution_name": null, "account_holder": null, "account_number": null, "currency": null},
  "statement_period": {"statement_date": null, "period_start": null, "period_end": null},
  "account_summary": {"opening_balance": null, "closing_balance": null, "total_credits": null, "total_debits": null},
  "credit_card_summary": {"previous_balance": null, "new_balance": null, "payments_credits": null, "purchases_advances": null, "minimum_payment_due": null, "payment_due_date": null, "credit_limit": null, "total_amount_due": null},
  "transactions": [{"date": null, "description": null, "reference": null, "credit": null, "debit": null, "amount": null, "balance": null}]
}
```

## Rules

1. Use `deposit_account` for a bank/deposit/current/checking account statement and `credit_card` for a credit-card statement only when supported by the document.
2. Extract identifiers such as account numbers and references as strings exactly as represented in the source.
3. Preserve monetary values as strings at this extraction stage. Do not calculate missing totals or balances.
4. Use null whenever a field is missing, unsupported, ambiguous, or not applicable. Never invent a value.
5. Keep deposit-account summary semantics separate from credit-card summary semantics. Do not map a credit-card “new balance” to `closing_balance`, or a deposit-account closing balance to `new_balance`.
6. For dates, return `YYYY-MM-DD` only when the date can be interpreted unambiguously from the document itself. Use consistent document-wide evidence when available. If the date interpretation cannot be resolved reliably, return null. Do not guess.
7. Extract every actual transaction exactly once and preserve transaction order from the source.
8. Keep multi-line or wrapped transaction descriptions together as one transaction description.
9. When the source explicitly provides separate Credit and Debit columns, populate `credit` or `debit` as appropriate and leave `amount` null.
10. When the source instead provides one generic or signed Amount column, populate `amount` and leave `credit` and `debit` null unless the source explicitly separates them.
11. Populate transaction `balance` only when a running/resulting balance is explicitly provided for that transaction.
12. Populate `reference` only when an explicit transaction reference exists.
13. Do not treat totals, daily balance summaries, account summaries, headers, footers, instructions, legal text, advertisements, or other non-transaction sections as transactions.
14. Handwritten annotations, user-added notes, markings, and inferred categories are not authoritative statement data and must not be extracted unless they are clearly part of the original printed statement.
15. Do not infer currency from institution name, address, country, or general knowledge. Populate currency only when a currency symbol or code is explicitly supported by the statement.
16. Return all keys in the specified structure even when their values are null.

This prompt was intentionally kept unchanged across the five baseline documents to provide a comparable benchmark. No Prompt V2 tuning has been performed.
