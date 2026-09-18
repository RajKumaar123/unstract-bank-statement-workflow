# Benchmark Summary

## Scope

- Documents: 5
- Manually verified documents: 5
- Verified transaction rows: 96
- Statement families: deposit/current account and credit card
- Page structures: single-page and multi-page
- Ground truth status: locked before extraction evaluation

## Coverage

| Document ID | Statement Family | Pages Supplied | Transactions | Key Challenge |
|---|---|---:|---:|---|
| document-01 | Deposit account | 1 | 17 | Separate inflow/outflow columns; source date inconsistency |
| document-02 | Credit card | 2 | 33 | Handwritten noise; incomplete printed pagination |
| document-03 | Deposit account | 4 | 28 | Multi-page transactions; signed amounts; wrapped descriptions |
| document-04 | Current/deposit account | 1 | 9 | Visual table alignment differs from flattened text |
| document-05 | Credit card | 1 | 9 | Mixed date representations; unusual number grouping |

**Total: 96 transactions**

## Evaluation Principles

- Use source-supported values only.
- Require human visual verification.
- Preserve source anomalies.
- Do not modify the benchmark after observing extraction outputs.
- Evaluate deterministic normalization and validation separately.

## Privacy Boundary

Private source documents, ground-truth files, and raw extraction outputs remain local-only. Only sanitized aggregate results may be published.
