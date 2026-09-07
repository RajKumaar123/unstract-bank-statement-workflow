# Canonical Bank Statement Extraction Schema

## Purpose

This document defines the extraction contract between document/text extraction, Unstract Prompt Studio structured extraction, downstream normalization, validation, and HITL/workflow processing.

It is an extraction-boundary specification, not the final normalized database model. It is designed for heterogeneous bank-account and credit-card statements.

## Source Fidelity and Nullability

- Extract only information explicitly supported by the source document.
- Unsupported or missing fields must be `null`.
- Do not infer values solely because they would normally exist on a statement.
- Do not derive accounting results inside the extraction schema.
- Preserve source semantics.
- Dates may be normalized only when they are unambiguous.
- Account and card identifiers must preserve their textual representation as strings.
- Monetary values remain strings at this boundary.

`null` is semantically different from zero, an empty string, and an inferred or default value.

## Canonical Structure

```text
BankStatement
├── document
├── statement_period
├── account_summary
├── credit_card_summary
└── transactions[]
```

- `document` contains common identifying metadata.
- `statement_period` contains applicable statement and date information.
- `account_summary` contains bank/deposit-account summary fields.
- `credit_card_summary` contains credit-card-specific financial and payment fields.
- `transactions` contains transaction rows extracted from the source.

One summary object may be largely `null` or not applicable depending on the statement type. The schema does not force all summary fields to contain populated values.

## `document`

| Field | Type at Extraction Boundary | Required | Description |
|---|---|---|---|
| `statement_type` | string or null | yes as an extraction target, but null if classification cannot be supported | Classification such as `deposit_account` or `credit_card`; do not guess if document evidence is insufficient. |
| `institution_name` | string or null | no | Financial institution or statement issuer explicitly identified by the document. |
| `account_holder` | string or null | no | Account or card holder name when explicitly present. |
| `account_number` | string or null | no | Account or card identifier as printed; preserve as a string. |
| `currency` | string or null | no | Currency when explicitly supported by symbols, currency codes, or document context; do not guess merely from geography. |

`account_number` must never be numeric.

## `statement_period`

| Field | Type | Expected normalized format |
|---|---|---|
| `statement_date` | string or null | `YYYY-MM-DD` when unambiguous |
| `period_start` | string or null | `YYYY-MM-DD` when unambiguous |
| `period_end` | string or null | `YYYY-MM-DD` when unambiguous |

Some statements provide a statement date only, some provide an opening and closing date range, and some may expose both. None should be fabricated. If a date is ambiguous, retain `null` rather than guessing.

## `account_summary`

| Field | Type at Extraction Boundary | Description |
|---|---|---|
| `opening_balance` | string or null | Opening balance when explicitly provided, primarily for deposit/current-account style statements. |
| `closing_balance` | string or null | Closing balance when explicitly provided, primarily for deposit/current-account style statements. |
| `total_credits` | string or null | Credit total when explicitly provided by the source. |
| `total_debits` | string or null | Debit total when explicitly provided by the source. |

These values apply primarily to deposit/current-account style statements. They preserve source semantics, and not every deposit statement will contain explicit summary totals. Monetary values remain strings until deterministic normalization.

## `credit_card_summary`

| Field | Type at Extraction Boundary | Description |
|---|---|---|
| `previous_balance` | string or null | Previous balance when explicitly provided by a credit-card statement. |
| `new_balance` | string or null | New balance when explicitly provided by a credit-card statement. |
| `payments_credits` | string or null | Payments and credits when explicitly summarized by the source. |
| `purchases_advances` | string or null | Purchases and advances when explicitly summarized by the source. |
| `minimum_payment_due` | string or null | Minimum payment due when explicitly stated. |
| `payment_due_date` | string or null | Payment due date; expected as `YYYY-MM-DD` only when unambiguous. |
| `credit_limit` | string or null | Credit limit when explicitly stated. |
| `total_amount_due` | string or null | Total amount due when explicitly provided. |

All fields except `payment_due_date` are monetary fields and remain `string or null` at the extraction boundary. These fields preserve credit-card statement terminology rather than being automatically mapped into deposit-account balance concepts.

## `transactions`

`transactions` is an ordered array following source-document transaction order where reliably recoverable.

Each transaction may contain:

| Field | Type | Description |
|---|---|---|
| `date` | string or null | Transaction date; expected as `YYYY-MM-DD` where unambiguous. |
| `description` | string or null | Meaningful transaction description or payee text. |
| `reference` | string or null | Explicit transaction reference, when supplied. |
| `credit` | string or null | Credit amount when the source explicitly distinguishes a credit column. |
| `debit` | string or null | Debit amount when the source explicitly distinguishes a debit column. |
| `amount` | string or null | Generic or signed amount when supplied by the source. |
| `balance` | string or null | Transaction-level or running balance when supplied. |

- `credit` and `debit` are used when source columns explicitly distinguish them.
- `amount` is used when the source provides a generic or signed amount.
- The schema does not force all three of `credit`, `debit`, and `amount` to be populated.
- `balance` is populated only when the source provides a transaction-level or running balance.
- `reference` remains `null` when no explicit transaction reference exists.
- `description` should preserve meaningful transaction text without unrelated page boilerplate.

`transaction_direction` is not part of the extraction schema.

## Extraction-Boundary Data Types

- **Identifiers:** `string or null`
- **Dates:** `string or null`, normalized to `YYYY-MM-DD` only when confidently unambiguous
- **Money:** `string or null`
- **Arrays:** `transactions` is an array; an empty array is appropriate when the document explicitly contains no transaction rows or none can reliably be extracted

Monetary values must not use floating-point types at the extraction boundary. A later normalization layer can parse validated money strings into decimal values.

## Deliberately Outside the Extraction Contract

The following belong to deterministic processing, workflow metadata, or downstream storage rather than source extraction:

- `normalized_amount`
- `transaction_direction`
- reconciliation status
- `balance_reconciliation_result`
- `summary_reconciliation_result`
- `validation_status`
- `validation_errors`
- `review_required`
- extraction confidence used as a workflow decision
- database-specific identifiers
- downstream processing timestamps

## Content Not Targeted for Extraction

The baseline extraction does not target unrelated content such as:

- generic marketing material
- legal boilerplate
- customer-service instructions
- payment mailing instructions
- generic informational sections
- handwritten annotations that are not authoritative account or transaction data

These exclusions may be revisited only if a real business requirement requires them.

## Downstream Normalization Boundary

Downstream deterministic code will later handle, conceptually:

- currency-symbol stripping
- grouping separator normalization
- negative number conventions
- decimal parsing
- normalized transaction direction where determinable
- date validation
- accounting reconciliation
- validation errors
- review and HITL decisions

AI extraction does not equal complete workflow automation.

## Prompt Studio Contract

When Prompt Studio is configured later:

- the prompt must follow this schema
- missing information must return `null`
- no values should be fabricated
- source semantics should be preserved
- the model should not perform accounting validation
- all transaction rows should be extracted when reliably represented in the source
- schema changes must be versioned and evaluated against ground truth

The actual Prompt Studio prompt is not defined in this document.

## Status

Canonical extraction schema specification: proposed for implementation.

Executable JSON schema, Prompt Studio configuration, ground truth, and validation logic have not yet been created.
