# Ground-Truth Design

## Purpose

The benchmark establishes an independent reference before testing document-processing and extraction systems. Outputs will be compared against manually verified source truth; no extraction accuracy is claimed at this checkpoint.

## Benchmark Scope

The benchmark contains five heterogeneous financial-statement documents covering deposit/current-account and credit-card statement types, single-page and multi-page layouts, complete and incomplete source pagination, multiple transaction representations, varying date representations, visual/layout extraction challenges, handwriting or noise in at least one source, and irrelevant or legal content.

There are 96 manually verified transaction rows across the benchmark.

## Stable Document IDs

Benchmark documents use stable internal IDs: `document-01` through `document-05`. These IDs remain stable even if local filenames change.

## Local Ground-Truth Naming Convention

Private ground-truth files use the convention:

```text
<document-id>__<sanitized-source-name>.json
```

The document ID provides stable benchmark identity, while the sanitized source slug improves local traceability. The original source filename remains metadata inside private ground truth. Ground-truth files remain local and private.

## Verification Workflow

```text
Source PDF
    ↓
Candidate ground truth
    ↓
Independent visual/source comparison
    ↓
Corrections
    ↓
manually_verified
    ↓
Locked benchmark reference
```

A candidate must not become `manually_verified` solely because an automated extraction or self-check reports success. Human visual and layout verification is required.

## Canonical Extraction Boundary

Ground truth represents source-supported extraction, not the final normalized database model.

- Unsupported fields remain `null`.
- Identifiers remain strings.
- Source monetary values remain extraction-boundary strings.
- Dates normalize only when interpretation is sufficiently supported.
- Source anomalies are preserved rather than silently repaired.
- Transaction order follows source order.
- Deposit and credit-card semantics remain distinct.
- Handwriting and non-authoritative annotations are excluded.
- Irrelevant or legal content is excluded from transaction extraction.

## Heterogeneous Transaction Representations

The benchmark intentionally includes separate credit/debit columns, separate paid-in/paid-out columns, generic amount columns, signed amounts, rows with and without running balances, explicit transaction references, transactions without references, and wrapped or multi-line descriptions.

These source structures map into one canonical contract without forcing every document into identical source semantics.

## Date Interpretation

Date handling must remain contextual:

- Never use one global day-first or month-first assumption.
- Resolve dates using field-level and document-wide evidence.
- Unambiguous dates can establish a format.
- Statement-level and transaction-level date representations can differ within one document.
- Unresolved ambiguity must not be guessed.
- Normalization must remain contextual.
- Logical or source inconsistencies must be preserved and later flagged.

## Visual Layout Verification

Flattened PDF text can lose relationships between dates, references, descriptions, credits/debits, amounts, and balances. Row reconstruction must therefore consider visual and layout structure. At least one benchmark document demonstrated that relying only on flattened text could create incorrect transaction rows.

## Source Anomalies

Sanitized anomaly categories encountered include transaction dates inconsistent with a stated period, a supplied file missing a page indicated by printed pagination, handwritten or non-authoritative annotations, unusual monetary digit grouping, mixed date representations, and disagreement between flattened text and table layout.

Ground truth preserves source-supported values. Anomalies are not silently repaired; later deterministic validation or HITL processing can flag them.

## Ground Truth vs Derived Processing

**Ground truth / extraction** contains source-supported fields.

**Post-extraction processing** may contain date-normalization metadata, decimal normalization, transaction direction, reconciliation, validation status, validation errors, review decisions, and HITL routing.

Derived processing must not contaminate the extraction benchmark.

## Privacy

- Source PDFs remain local-only.
- Manually verified ground-truth JSON remains local-only.
- Raw extraction outputs remain local-only.
- The public repository contains only code, schema, methodology, and sanitized aggregate results.
- Secrets, API keys, and tokens must not be committed.
- Screenshots must be sanitized before publication.

## Benchmark Status

- Documents: 5
- Manually verified documents: 5
- Manually verified transaction rows: 96
- Ground-truth phase: COMPLETE
- Benchmark locked before Unstract evaluation

Extraction accuracy and evaluation results have not yet been established.
