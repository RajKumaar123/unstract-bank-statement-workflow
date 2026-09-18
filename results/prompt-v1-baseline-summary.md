# Prompt V1 Baseline Summary

## Methodology

This benchmark covers five heterogeneous bank/credit-card statement documents with manually verified ground truth. The same Prompt V1 was used unchanged for all five documents. Results use strict field-level comparison and source-order transaction comparison; diagnostic normalization is reported separately. Raw documents, ground truth, raw outputs, and detailed evaluations remain private.

## Aggregate results

| Document | Ground-truth transactions | Predicted rows | Transaction field accuracy | Fully correct rows | Strict overall accuracy |
|---|---:|---:|---:|---:|---:|
| document-01 | 17 | 18 | 0.373016 | 0/17 | 0.431507 |
| document-02 | 33 | 33 | 0.969697 | 27/33 | 0.960159 |
| document-03 | 28 | 28 | 0.5153061 | 0/28 | 0.5370370 |
| document-04 | 9 | 9 | 1.0 | 9/9 | 0.9879518 |
| document-05 | 9 | 9 | 0.984127 | 8/9 | 0.951807 |

Dataset ground-truth transaction count: **96**
Total predicted rows: **97**

Document-01 includes one extra predicted non-transaction/carry-forward row. The official strict score remains based on source-order evaluation. A diagnostic alignment experiment was performed separately, but it does not replace the official strict baseline.

Document-03 mismatches are concentrated in systematic schema/date/representation differences rather than missing transaction rows.

All five baseline runs used the same unchanged Prompt V1. No Prompt V2 tuning has yet been performed.
