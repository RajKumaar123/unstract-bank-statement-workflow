# Unstract Bank Statement Processing Workflow

This repository contains the hands-on implementation accompanying a technical article on document processing workflow automation using Unstract. It demonstrates a production-oriented workflow for structured bank-statement extraction, deterministic validation, exception handling, Human-in-the-Loop review, API integration, evaluation, and traceability.

The repository documents the implemented workflow and its evidence boundaries. It does not claim that every possible Unstract deployment mode was fully executed.

## Project Status

The hands-on implementation and technical validation are complete. The article is still being prepared.

Completed work includes:

- independent ground-truth benchmark preparation
- Prompt V1 baseline evaluation
- versioned prompt and schema evolution through V2.2
- transaction-level structured extraction
- `payment_type` in the V2.2 transaction contract
- secure Python API integration
- deterministic post-extraction validation
- exception and review-required handling
- optional HITL routing
- manual review workflow demonstration
- Prompt Studio versus API consistency evaluation
- automated offline testing
- privacy-safe benchmark reporting

## What This Project Demonstrates

The implemented workflow covers:

- extraction from heterogeneous bank-statement layouts
- versioned Prompt Studio extraction instructions
- a documented V2.2 structured extraction contract
- transaction-level fields for dates, narratives, payment classification, references, monetary values, and balances
- API-based document processing through a small Python client
- deterministic validation after extraction
- structural and semantic exception detection
- conservative `valid`, `review_required`, and `invalid` validation statuses
- optional routing to a Human-in-the-Loop queue
- manual review in the Unstract Review interface
- offline comparison of Prompt Studio and API execution paths
- reproducible local tests and sanitized aggregate reporting

## Processing Flow

```text
Bank Statement PDF
        |
        v
Unstract Prompt Studio
        |
        v
V2.2 Structured Extraction
        |
        v
Unstract API Workflow
        |
        v
Python Integration Client
        |
        v
Deterministic Validation
        |
        +----------------------+
        |                      |
        v                      v
Usable Output          Review / Exception
                               |
                               v
                         HITL Review
```

## ETL and Task Pipeline Boundary

The task-based ETL deployment path was explored and configured. Actual task execution was not performed because a persistent external source and destination connector is required. No external cloud-storage dependency was introduced solely for the demonstration.

The API workflow is the primary executable integration demonstrated. HITL routing was demonstrated separately. The task and ETL deployment remains configured but unscheduled, with no task run claimed.

## Dataset and Privacy

Five heterogeneous bank-statement documents were used for the private benchmark, containing 96 manually verified transaction rows. Independent ground truth was prepared before extraction experiments.

The following remain private and Git-ignored:

- source PDFs
- manually verified ground truth
- raw Prompt Studio outputs
- raw API responses
- detailed validation and comparison reports
- local credentials

The public repository contains implementation artifacts and sanitized aggregate evidence only. No document-derived names, identifiers, descriptions, amounts, balances, or addresses are published.

## Prompt and Schema Evolution

Historical contracts and evidence are preserved rather than overwritten:

- [Prompt V1](prompts/bank-statement-extraction-v1.md) is the historical baseline.
- Later prompt revisions are documented in [Prompt V2](prompts/bank-statement-extraction-v2.md), [Prompt V2.1](prompts/bank-statement-extraction-v2.1.md), and [Prompt V2.2](prompts/bank-statement-extraction-v2.2.md).
- [Schema V2](schemas/bank-statement-schema-v2.md) extends the historical contract with `payment_type` while retaining the existing document structure and transaction semantics.

The V2.2 transaction contract distinguishes complete source-supported descriptions, optional payment classifications, and actual transaction references. Missing or ambiguous information remains null rather than being inferred.

## Benchmark

The historical Prompt V1 benchmark covers five documents and 96 manually verified transaction rows. Its pooled strict seven-field result was 581 / 779, or 74.58%.

See the [sanitized Prompt V1 baseline results](results/prompt-v1-baseline-summary.md).

The legacy-compatible V2.2 evaluation produced 602 / 772, or 77.98%, in the preserved private evidence. This is not an apples-to-apples accuracy comparison with V1 because the denominators and semantic rules differ. `payment_type` was not included in that legacy-compatible seven-field evaluation, and verified eight-field V2 ground truth is incomplete. Therefore, this repository makes no V2.2 eight-field extraction accuracy claim.

## API and Prompt Studio Consistency

The completed private five-document comparison produced the following sanitized evidence:

- documents compared: 5
- transactions: 96
- `payment_type` coverage: 96 / 96
- compared fields: 868
- matching fields: 752
- differing fields: 116
- field-level API/Prompt Studio consistency: 752 / 868, approximately 86.64%

This percentage measures agreement between two execution paths. It is field-level API/Prompt Studio consistency, not extraction accuracy, model accuracy, field accuracy, or ground-truth accuracy. Agreement between execution paths does not establish that either output is correct against source evidence.

## Validation and Exception Handling

The deterministic validation layer operates on already parsed canonical JSON. It does not extract text, call an LLM, require ground truth, or repair extracted values.

The validator checks schema shape and types, statement semantics, date syntax and calendar validity, statement periods, monetary representations, transaction structure, possible non-transaction rows, and reconciliation conditions. It returns structured issues and conservative statuses:

- `valid` for clean validation
- `review_required` when findings should be reviewed
- `invalid` for blocking structural or error-severity findings

Valid JSON is not treated as automatically trustworthy. Validation is a separate deterministic control after extraction. See the [deterministic validation notes](docs/notes/deterministic-validation-v1.md).

## Human-in-the-Loop Review

HITL routing is optional in the Python client. The demonstrated flow was:

1. The client optionally supplies a HITL queue name.
2. A selected document is routed for manual review.
3. The API response indicates that the file was sent to HITL.
4. The document becomes available in the Unstract Review interface.
5. A reviewer can inspect the source document alongside the structured extraction.
6. The review can be completed.

The demonstrated review completed without modifying extracted fields, so no field-change audit entries were generated. The client does not hardcode a queue or expose queue identifiers.

## Python API Client

The public client is [src/unstract_api_client.py](src/unstract_api_client.py). It supports:

- repository-root `.env` loading with explicit environment-variable precedence
- multipart PDF submission
- synchronous responses
- bounded asynchronous execution polling
- safe non-overwriting private output persistence
- response and network error handling
- optional HITL queue routing

The client uses `UNSTRACT_API_URL` and `UNSTRACT_API_KEY` from the environment or local `.env`. It does not print credentials or authorization headers.

Non-HITL example:

```bash
python src/unstract_api_client.py \
  --pdf "/path/to/statement.pdf" \
  --output "data/outputs/statement-api-response.json"
```

Optional HITL routing:

```bash
python src/unstract_api_client.py \
  --pdf "/path/to/statement.pdf" \
  --output "data/outputs/statement-hitl-response.json" \
  --hitl-queue-name "<your-review-queue>"
```

## Environment Configuration

The public template is [.env.example](.env.example):

```env
UNSTRACT_API_URL=https://us-central.unstract.com/deployment/api/<your-org-id>/bank_statement_processing/
UNSTRACT_API_KEY=REPLACE_WITH_YOUR_API_KEY
```

Put real credentials only in a local `.env`. The `.env` file is Git-ignored and must never be committed. The template contains placeholders only.

## Testing

Run the complete offline suite with:

```bash
python -m unittest discover -s tests -v
```

The verified suite contains 32 passing tests covering schema behavior, API request construction, configuration loading, authentication and timeout handling, response persistence, asynchronous polling, optional HITL queue handling, whitespace handling, and deterministic validation behavior.

## Repository Structure

```text
data/       Private/local source, ground-truth, and output areas (Git-ignored)
prompts/    Versioned extraction prompt documentation
schemas/    Extraction schema documentation
src/        API integration, validation, and evaluation utilities
tests/      Offline automated tests
docs/       Architecture and implementation documentation
results/    Sanitized benchmark and evaluation summaries
```

## Reproducibility and Privacy

The repository separates public implementation artifacts from private evaluation data.

Public repository contents include implementation code, prompt documentation, schema documentation, automated tests, architecture notes, and sanitized aggregate benchmark evidence.

Private/local data includes source PDFs, manually verified ground truth, raw Prompt Studio outputs, raw API responses, detailed document-derived validation reports, and credentials.

This separation keeps the implementation inspectable while preventing sensitive source data from being published.

## Limitations

- The benchmark contains five documents.
- The dataset is private and intentionally limited.
- Bank-statement layouts vary across institutions and document formats.
- Verified V2 eight-field ground truth is not yet complete.
- No V2.2 eight-field extraction accuracy is claimed.
- API/Prompt Studio consistency measures execution-path agreement, not extraction correctness.
- Task/ETL execution was not performed because a persistent external source and destination connector was intentionally not introduced solely for the demonstration.

## Related Article

A detailed hands-on article covering the architecture, implementation, evaluation, API integration, deterministic validation, exception handling, and Human-in-the-Loop workflow is being prepared. The final article link will be added later.
