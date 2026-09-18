# Unstract Bank Statement Processing Workflow

This repository is being developed as the hands-on implementation accompanying a technical article on document processing workflow automation using Unstract.

The eventual project will explore document intake, text extraction, structured bank-statement extraction, validation, exception handling, human-in-the-loop review, workflow orchestration, downstream integration, and evaluation and traceability.

## Project Status

The independent ground-truth benchmark is complete and locked. The Prompt V1 baseline benchmark is complete, with sanitized aggregate results published under `results/`.

## Data

The bank-statement source documents used during development were provided for the collaboration and are not included in the repository.

Source bank statements, manually verified ground truth, and raw extraction outputs are excluded from this public repository because they may contain document-derived sensitive values. Only sanitized aggregate evaluation summaries may be published later.

## Benchmark

The benchmark contains five heterogeneous statement documents and 96 manually verified transaction rows. Independent ground truth was prepared before extraction experiments; private source and ground-truth data are excluded from Git. Evaluation results are published only as sanitized aggregate metrics.

## Baseline Benchmark

Prompt V1 was tested unchanged across all five manually verified documents using the reusable evaluation utility. See the [Prompt V1 definition](prompts/bank-statement-extraction-v1.md) and [sanitized baseline results](results/prompt-v1-baseline-summary.md).

Raw PDFs, ground truth, raw outputs, and detailed evaluations are intentionally excluded from the public repository.

## Repository Structure

```text
data/       Source, ground-truth, and output data areas
prompts/    Prompt documentation
schemas/    Canonical extraction schema documentation
src/        Future integration and workflow code
tests/      Future automated tests
docs/       Architecture, screenshots, and implementation notes
results/    Reviewed experiment evidence and summaries
```
