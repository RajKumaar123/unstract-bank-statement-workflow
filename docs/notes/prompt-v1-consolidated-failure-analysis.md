# Prompt V1 Consolidated Failure Analysis

## 1. Objective and methodology

This report consolidates the five existing Prompt V1 baseline evaluations. It identifies recurring failure patterns and separates confirmed evaluation observations from engineering hypotheses. No source document, ground truth, prediction, evaluation, prompt, schema, evaluator, or Unstract configuration was modified.

The official benchmark is strict, field-level, and source-order based. Each evaluation compares aligned transaction rows by index, preserves count mismatches, and includes missing or extra rows in the evaluator's stated overall denominator. Diagnostic normalization is reported separately and does not replace the strict score.

## 2. Dataset and baseline summary

The dataset contains five heterogeneous bank/credit-card documents and 96 expected transaction rows. Baseline predictions contain 97 rows: one extra row in document-01 and no missing rows. The same Prompt V1 was used unchanged across all five documents.

| Document | Expected rows | Predicted rows | Strict transaction accuracy | Strict overall accuracy |
|---|---:|---:|---:|---:|
| document-01 | 17 | 18 | 0.373016 | 0.431507 |
| document-02 | 33 | 33 | 0.969697 | 0.960159 |
| document-03 | 28 | 28 | 0.515306 | 0.537037 |
| document-04 | 9 | 9 | 1.000000 | 0.987952 |
| document-05 | 9 | 9 | 0.984127 | 0.951807 |

## 3. Pooled benchmark metrics

| Metric | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Strict non-transaction fields | 84 | 100 | 0.840000 |
| Strict transaction fields | 497 | 679 | 0.731959 |
| Strict overall fields | 581 | 779 | 0.745828 |
| Diagnostic-normalized overall fields | 583 | 779 | 0.748395 |
| Fully correct transaction rows | 44 | 96 | 0.458333 |

The evaluator compares 96 aligned expected rows (672 transaction fields) and adds seven fields for the one extra transaction row to the pooled overall denominator, yielding 679 transaction fields and 779 total fields. This preserves the evaluator's definition; no alternative row denominator was invented.

Definitions:

- **Strict source-order evaluation:** exact values are compared at the same transaction index. Count mismatches are retained and can create alignment penalties.
- **Diagnostic normalized evaluation:** the evaluator applies its existing non-authoritative normalization, primarily trimming strings and parsing configured monetary fields. It is diagnostic only.
- **Transaction count accuracy:** whether predicted and expected row counts match; it is not a field accuracy measure.
- **Fully correct transaction-row accuracy:** the proportion of aligned rows for which all seven canonical transaction fields match exactly.

## 4. Field-level mismatch analysis

The following counts are pooled across the five strict evaluations. Transaction paths are grouped by canonical field name. Null categories use the evaluator's mismatch categories. “Resolved” means the strict mismatch disappeared in the diagnostic-normalized evaluation.

| Category | Strict mismatches | Affected documents | Null-related split | Resolved by normalization | Likely failure class |
|---|---:|---|---|---:|---|
| transactions.date | 46 | document-01, document-03, document-05 | 1 expected-value/predicted-null; 45 exact | 0 | Date interpretation/normalization; source/layout inference where confirmed only as a hypothesis |
| transactions.debit | 43 | document-01, document-03 | 3 expected-value/predicted-null; 28 expected-null/predicted-value; 12 exact | 0 | Schema semantic mapping and source-column interpretation |
| transactions.description | 33 | document-01, document-02, document-03 | 33 exact | 0 | Description preservation and layout/text segmentation |
| transactions.amount | 29 | document-02, document-03 | 29 expected-value/predicted-null | 0 | Amount-versus-credit/debit representation mapping |
| transactions.balance | 17 | document-01 | 17 exact | 0 | Row alignment/date interpretation interaction; not independently isolated by the strict benchmark |
| transactions.credit | 7 | document-01, document-02, document-03 | 2 expected-value/predicted-null; 5 expected-null/predicted-value | 0 | Credit/debit semantic mapping |
| document.institution_name | 4 | document-01, document-02, document-03, document-05 | 4 exact | 0 | Unsupported or inconsistent metadata extraction; source evidence requires review |
| document.currency | 2 | document-02, document-03 | 2 expected-value/predicted-null | 0 | Unsupported-field handling or missed explicit currency evidence |
| statement_period.statement_date | 2 | document-01, document-04 | 1 exact; 1 expected-null/predicted-value | 0 | Date interpretation and unsupported-field handling |
| account_summary.opening_balance | 1 | document-03 | 1 exact | 1 | Monetary formatting/representation |
| account_summary.closing_balance | 1 | document-03 | 1 exact | 1 | Monetary formatting/representation |
| account_summary.total_credits | 1 | document-03 | 1 exact | 0 | Summary-field representation or extraction |
| credit_card_summary.purchases_advances | 1 | document-02 | 1 exact | 0 | Credit-card summary semantic mapping |
| credit_card_summary.new_balance | 1 | document-05 | 1 expected-null/predicted-value | 0 | Unsupported or semantically mis-mapped field |
| document.account_number | 1 | document-05 | 1 expected-null/predicted-value | 0 | Identifier extraction/unsupported-value handling |
| statement_period.period_start | 1 | document-01 | 1 exact | 0 | Unsupported period-field handling |
| statement_period.period_end | 1 | document-01 | 1 exact | 0 | Unsupported period-field handling |
| transactions (count) | 1 | document-01 | count mismatch | 0 | Non-transaction row inclusion |

The largest recurring problems are transaction dates, debit/credit semantics, descriptions, and amount representation. Normalization materially resolved only two document-03 summary monetary mismatches. It resolved none of the transaction-field mismatches.

## 5. Document-specific findings

### document-01

There are 17 expected rows and 18 predicted rows, with one extra predicted row and no missing rows. The official strict source-order score is 43.15% overall. A separate in-memory alignment experiment removing the extra predicted row at its best position produced 85/119 transaction-field matches (71.43%), with dates and descriptions still mismatching for all 17 aligned rows while the other five transaction fields matched.

This demonstrates both an alignment penalty and genuine field failures. The diagnostic alignment is useful for understanding the failure, but it does not alter the official strict result or authorize removal of the row from evidence.

### document-02

The 33-row extraction has 10 strict mismatches overall. The affected categories are institution metadata, currency, one credit-card summary field, one transaction credit field, one transaction amount field, and five transaction descriptions. The row count matches, and 27 of 33 transaction rows are fully correct. The pattern is localized rather than a broad transaction-row failure.

### document-03

The 28-row extraction preserves the transaction count, so the principal issue is representation and field interpretation rather than missing rows. Strict transaction mismatches are concentrated in dates, descriptions, debit/credit/amount representation, and a small number of summary fields. The strict overall score is 53.70%; diagnostic normalization raises it only to 54.63% by resolving two summary monetary formatting differences.

The evidence supports a systematic schema/date/representation problem. It does not by itself prove whether a particular discrepancy originated in OCR, layout flattening, or model interpretation.

### document-04

All nine transaction rows and all 63 transaction fields match strictly, and all nine rows are fully correct. The single mismatch is an unsupported or inconsistent statement-date field, producing a 98.80% strict overall score.

### document-05

The nine-row extraction has four strict mismatches: institution metadata, account-number handling, one credit-card summary field, and the first transaction date. Transaction rows otherwise perform strongly: eight of nine rows are fully correct and transaction-field accuracy is 98.41%. The discrepancies should not be resolved by changing ground truth to match the prediction.

## 6. Root-cause classification

### Confirmed observations

- **C. Schema semantic-mapping issues:** debit/credit/amount mismatches recur across document-01, document-02, and document-03; credit-card and deposit-account summary categories also differ in isolated cases.
- **D. Date interpretation and normalization issues:** transaction-date mismatches recur across three documents, and statement-date mismatches occur in two documents.
- **E. Unsupported or hallucinated field values:** several expected-null/predicted-value mismatches occur in metadata, summary, and transaction fields.
- **F. Non-transaction row inclusion:** document-01 has one extra predicted row classified diagnostically as a balance/carry-forward row.
- **G. Transaction description preservation:** description mismatches affect three documents and are especially prominent in document-01 and document-03.
- **I. Genuine source ambiguity requiring human review:** source-inconsistent dates and unsupported fields should remain review candidates rather than being guessed.

### Plausible hypotheses, not proven causes

- **A. Source extraction/OCR/layout issues:** description and column-semantic errors may be consistent with flattened or visually complex layouts, but the evaluations alone do not prove OCR failure.
- **B. LLM extraction instruction issues:** recurring semantic and date patterns indicate that clearer instructions could help, but the benchmark does not isolate prompt quality from source complexity.
- **H. Deterministic reconciliation failures:** balance and total consistency checks are appropriate engineering controls, but the current evaluation evidence does not establish that reconciliation was attempted or failed upstream.

## 7. Prompt V2 / deterministic validation / HITL decision matrix

| Failure class | Evidence | Prompt V2 | Deterministic validation | HITL | Rationale |
|---|---|---|---|---|---|
| Date ambiguity and inconsistent date representations | 46 transaction-date mismatches across three documents; statement-date mismatches in two | Add document-wide evidence rules and explicit ambiguity-to-null behavior; do not impose one format blindly | Validate syntax and calendar dates; detect inconsistent document-wide patterns | Review unresolved or conflicting dates | Prompt can constrain interpretation; code can detect, not invent |
| Credit/debit/amount semantics | 43 debit, 29 amount, and 7 credit mismatches | Reinforce source-column mapping and mutually exclusive population rules | Check mutually exclusive fields and signed-value conventions | Review ambiguous column layouts | Use schema semantics without calculating unsupported fields |
| Description preservation | 33 mismatches across three documents | Require wrapped/multiline descriptions to remain one source-order transaction | Check row continuity and unexpected truncation where structurally detectable | Review uncertain segmentation | Prompt helps preservation; visual ambiguity needs review |
| Extra non-transaction rows | One extra row in document-01 | Explicitly exclude totals, carry-forward, header, and balance rows | Flag rows with non-transaction structure and count anomalies | Review flagged extra/missing rows | Deterministic checks can flag; review decides ambiguous cases |
| Unsupported metadata and summaries | Institution mismatches in four documents; isolated currency, identifier, and summary mismatches | Repeat source-supported-only and null-on-unsupported rules; keep account and card summaries distinct | Validate field presence, types, and schema-specific applicability | Review source-supported but disputed values | Prevent hallucination while preserving evidence |
| Monetary formatting | Two summary mismatches resolved diagnostically | Preserve source strings; do not calculate totals in the prompt | Compare with Decimal after explicit normalization and reconcile totals/balances when source supports it | Review unreconcilable differences | Decimal avoids binary floating-point errors |
| Source ambiguity | Mixed date and metadata behavior across documents | Instruct null for unresolved ambiguity | Route consistency violations to an exception queue | Required when no unambiguous evidence exists | Human review is safer than inference |

## 8. Proposed implementation order

1. Preserve the current strict benchmark and evaluation artifacts as the immutable baseline.
2. Add deterministic structural validation around the existing output: schema shape, required keys, row counts, mutually exclusive amount fields, date syntax/calendar validity, and Decimal-based monetary parsing.
3. Add transaction-order and non-transaction-row checks, including anomaly flags for likely carry-forward or summary rows.
4. Test a separately versioned Prompt V2 focused on date evidence, semantic column mapping, description continuity, and null behavior; do not alter Prompt V1.
5. Re-run the same five-document benchmark and compare strict, diagnostic, and review-routing outcomes separately.
6. Add HITL routing for unresolved dates, count anomalies, semantic conflicts, and reconciliation failures.
7. Only after repeatable validation should downstream workflow integration proceed.

## 9. Limitations and unresolved questions

- The evaluator is source-order based and does not perform general transaction matching; document-01's alignment experiment is separate and diagnostic.
- Pooled transaction totals include the evaluator's seven-field accounting for the one extra row. This is faithful to the existing definition, not a new accuracy definition.
- The evaluation JSONs expose mismatch paths and categories, but not causal provenance. OCR, layout, model reasoning, and prompt effects cannot be isolated from these artifacts alone.
- Diagnostic normalization is intentionally narrow and non-authoritative; its small improvement does not demonstrate that formatting is the dominant problem.
- No Prompt V2 has been created or tested, and no engineering change is justified solely by this report without a controlled follow-up benchmark.
