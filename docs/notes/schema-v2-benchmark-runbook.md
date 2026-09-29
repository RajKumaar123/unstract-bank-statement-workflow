# Schema V2 Five-Document Benchmark Runbook

1. Preserve the existing V1, V2, and V2.1 Prompt Studio cards. Create a separate V2.2 card and use `prompts/bank-statement-extraction-v2.2.md`.
2. Use stable IDs `document-01` through `document-05`, with private input pattern `data/raw/<local-source>.pdf` and private output pattern `data/outputs/<local-source>__unstract-v2.json`. Never publish or overwrite historical files.
3. Reuse the same model, text extractor, parameters, schema configuration, and document settings used for the historical baseline. Do not use credentials or authenticated URLs in project files.
4. Execute in order: document-01, document-02, document-03, document-04, document-05. Run each once and record failures without fabricating JSON or retrying for a preferred result.
5. Parse and integrity-check each output. Run `python src/evaluate_extraction_v2.py --ground-truth <private-v2-gt> --prediction <private-output> --output <private-report> --document-id <id> --schema-version 2` and `python src/validate_extraction_v2.py --input <private-output> --output <private-report> --document-id <id> --expected-transaction-count <authorized-count>` separately.
6. Keep V1-compatible and Schema V2 views distinct. Compare new reports with historical V1 reports using their original denominators; do not rewrite historical results or average incompatible metrics.
7. Extraction readiness is separate from scoring readiness: a document may run through Prompt V2.2 while its V2 ground truth remains provisional or blocked. Do not score against unverified V2 ground truth.
8. Route ambiguous Payment Type/Detail mappings, references, dates, and failed or non-JSON runs to human review. Do not silently correct values.

Codex does not operate authenticated Unstract sessions. No benchmark execution is claimed by this runbook.
