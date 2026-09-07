# Bank Statement Dataset Field Assessment

The supplied test set contains heterogeneous bank-account and credit-card statement layouts. This assessment establishes the extraction contract before configuring Unstract Prompt Studio. Fields are classified as Core, Optional, Statement-Type-Specific, Derived, or Excluded. Missing fields must remain null/not-present rather than being invented.

## Classification Principles

1. Extract values explicitly supported by the source document.
2. Do not require fields that do not naturally exist across statement types.
3. Preserve differences between deposit-account and credit-card semantics.
4. Keep extraction separate from deterministic validation and normalization.
5. Missing source fields must not be fabricated.
6. The transaction representation must tolerate different source layouts, including:
   - separate credit/debit columns
   - signed amounts
   - amount-only credit-card transaction tables
   - optional running balances
   - optional references

## Candidate Extraction Fields

| Group | Field | Classification | Notes |
|---|---|---|---|
| Document | `statement_type` | Core | Identifies the broad statement type, such as a deposit account or credit card. |
| Document | `institution_name` | Core | Extract when explicitly present. |
| Document | `account_holder` | Core | Extract the named account or card holder when explicitly present. |
| Document | `account_number` | Core | Preserve the source value subject to later handling and access controls. |
| Document | `currency` | Optional | Extract when stated or unambiguous in the document. |
| Statement period | `statement_date` | Optional | The statement date when supplied. |
| Statement period | `period_start` | Optional | The beginning of the stated period when supplied. |
| Statement period | `period_end` | Optional | The end of the stated period when supplied. |
| Deposit/account summary | `opening_balance` | Statement-Type-Specific | Applicable where a deposit or other balance-based account provides an opening balance. |
| Deposit/account summary | `closing_balance` | Statement-Type-Specific | Applicable where the statement provides a closing balance. |
| Deposit/account summary | `total_credits` | Optional / Statement-Type-Specific | Applicable when the source provides a credit total for the statement type. |
| Deposit/account summary | `total_debits` | Optional / Statement-Type-Specific | Applicable when the source provides a debit total for the statement type. |
| Credit-card summary | `previous_balance` | Statement-Type-Specific | Applicable to credit-card statements that provide a previous balance. |
| Credit-card summary | `new_balance` | Statement-Type-Specific | Applicable to credit-card statements that provide a new balance. |
| Credit-card summary | `payments_credits` | Statement-Type-Specific | Applicable when the credit-card summary provides payments or credits. |
| Credit-card summary | `purchases_advances` | Statement-Type-Specific | Applicable when the credit-card summary provides purchases or advances. |
| Credit-card summary | `minimum_payment_due` | Statement-Type-Specific | Applicable when a minimum payment is stated. |
| Credit-card summary | `payment_due_date` | Statement-Type-Specific | Applicable when a payment due date is stated. |
| Credit-card summary | `credit_limit` | Statement-Type-Specific | Applicable when a credit limit is stated. |
| Credit-card summary | `total_amount_due` | Statement-Type-Specific | Applicable when the source provides a total amount due. |
| Transactions | `date` | Core | The transaction date when explicitly present. |
| Transactions | `description` | Core | The transaction description or payee text. |
| Transactions | `reference` | Optional | Preserve a transaction reference when supplied. |
| Transactions | `credit` | Optional | Use when the source represents credits in a separate column. |
| Transactions | `debit` | Optional | Use when the source represents debits in a separate column. |
| Transactions | `amount` | Optional | Use for amount-only transaction layouts, including applicable credit-card tables. |
| Transactions | `balance` | Optional | Preserve a running balance when supplied. |

The fields are intended to accommodate differences between statement layouts without inserting values that are absent from a source document. Applicability depends on the statement type and the fields actually provided by each document.

## Derived and Validation Fields

The following values should not initially be treated as authoritative LLM-extracted source fields:

- `transaction_direction`
- `normalized_amount`
- `balance_reconciliation_result`
- `summary_reconciliation_result`
- `validation_status`
- `validation_errors`
- `review_required`

These values should be produced later by deterministic normalization, validation, and workflow logic when sufficient source evidence exists. Algorithms are intentionally not defined at this stage.

## Deliberately Excluded Content

The extraction contract should avoid unrelated statement content unless later requirements establish a business need. Examples include:

- marketing text
- customer-service instructions
- generic legal/disclosure sections
- payment mailing instructions
- informational boilerplate
- handwritten annotations that are not part of the authoritative statement data

## Current Design Decision

The project will use:

common core
+ statement-type-specific optional summary fields
+ a flexible transaction structure

rather than one flat schema requiring every possible bank-statement field.

This decision is provisional until the canonical schema is reviewed in the next project step.

No Prompt Studio implementation should begin until the canonical extraction schema is approved.
