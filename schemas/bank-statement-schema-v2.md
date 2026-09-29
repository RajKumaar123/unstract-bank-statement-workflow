# Canonical Bank Statement Extraction Schema V2

Schema V2 is a versioned extension of the historical V1 extraction contract. The document-level structure and all V1 fields remain unchanged. Each transaction contains the V1 fields plus:

| Field | Type | Semantics |
|---|---|---|
| `description` | string or null | Complete source-supported transaction narrative, including wrapped lines; do not silently mix classification into it. |
| `payment_type` | string or null | Explicit source-supported payment classification when separately presented; null when absent or ambiguous. |
| `reference` | string or null | Actual source-supported transaction reference; never a payment classification. |

Transaction field order is `date`, `description`, `payment_type`, `reference`, `credit`, `debit`, `amount`, `balance`. Existing date, monetary, null, source-order, deposit-account, and credit-card semantics remain unchanged. No values are inferred, calculated, or repaired.

## Compatibility

V1 remains the historical contract and its reports are immutable. V2 reports must identify the schema version and score the new field separately. Historical V1 ground truth is not automatically migrated; each document requires source-supported mapping review.
