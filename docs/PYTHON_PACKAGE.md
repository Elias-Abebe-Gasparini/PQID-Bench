# PQID-Bench Python Package Contract

## Scientific Boundary

`pqid-bench 1.0.0` is a reproducibility and replication toolkit for the
immutable PQID-Bench v1.0.0 study. Its safe default path recomputes reported
quantities from archived evaluator records. Live calls are a separate,
explicitly acknowledged path that creates new evidence.

The package distinguishes:

1. **verification**: byte and SHA-256 integrity of the release;
2. **reproduction**: deterministic metric calculation from archived
   evaluations;
3. **evaluation summarization**: calculation from another canonical evaluation
   bundle;
4. **live replication**: timestamped collection through an OpenAI-compatible
   provider route;
5. **executable replay**: execution of generated Python in the isolated
   evaluator container; and
6. **comparison**: denominator-aligned interpretation against frozen cells.

## Version Dimensions

Every core machine-readable scientific report carries:

| dimension | frozen identifier |
| --- | --- |
| package | `1.0.0` |
| benchmark release | `1.0.0` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| schema | `1.0.0` |
| artifact manifest | `1.0.0` |

Executable replay additionally records container artifact version `1.0.0`,
image tag `pqid-bench-evaluator:1.0.0`, and the applicable content identity.
The container distribution and its embedded evaluator contract are separately
versioned. A local Docker image ID or archive digest must not be presented as
an OCI registry manifest digest.

Changing evaluator behavior requires a new evaluator identifier and an impact
audit. It must never silently replace the evaluator attached to the frozen
matrix.

## Commands

```bash
pqid-bench doctor
pqid-bench verify RELEASE_DIR
pqid-bench verify RELEASE_DIR --full
pqid-bench reproduce --release-dir RELEASE_DIR --output summary.json
pqid-bench reproduce --release-dir RELEASE_DIR --format text
pqid-bench evaluate --evaluations evaluation_records.jsonl
pqid-bench compare --evaluations evaluation_records.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR
pqid-bench run-model --release-dir RELEASE_DIR \
  --output-dir runs/model-a --provider groq --model MODEL_ID --dry-run
```

`verify --full` checks all 3,234 primary model-prompt cells and all 4,536
stochastic-repeatability cells in addition to the release manifest.

`evaluate` rejects duplicate model-prompt cells and conflicting Boolean aliases.
`compare` additionally requires a compatible versioned run manifest and one
common prompt denominator across candidate models. By default that denominator
must be the complete frozen 154-prompt set. `--allow-partial` permits a strict
subset only as an explicitly labelled matched-subset comparison and restricts
the frozen records to the same prompt IDs.

`reproduce`, `evaluate`, and `compare` accept
`--format json|text|markdown|csv`. JSON remains the default. Human-readable
formats always show denominators, and CSV uses stable long-form metric keys for
R, pandas, spreadsheet, and statistical-software import. These renderers do not
recompute inferential models or modify the scientific payload. See
[Reporting And Numerical Exports](user-manual/reporting-and-exports.md).

See [`REVIEWER_QUICKSTART.md`](REVIEWER_QUICKSTART.md) for the tiered audit
workflow and a candidate run-manifest example.

## Live Replication

`run-model` exports only the prompt record's model-facing `messages`, never
its evaluator-only `target_metadata`. A networked call requires
`--acknowledge-third-party-prompt-export`; a credential-free `--dry-run`
requires no acknowledgement because it exports nothing.

The runner supports provider presets, custom OpenAI-compatible base URLs,
environment or external-file credentials, atomic per-prompt state, bounded
retry, quota-aware `--max-new` chunks, terminal-error recovery, and explicit
duplicate-draw handling after an interrupted in-flight request. It writes
canonical responses, normalized provider attempts, raw payloads, request and
response hashes, and a versioned `live_replication` manifest. Credential
values and key-file paths are never persisted.

Native Anthropic Messages and Google Gemini protocols are not silently mapped
onto this interface. See
[Live Model Testing](user-manual/live-model-testing.md).

## Executable Replay

Generated Python is untrusted. Restricted built-ins define benchmark
admissibility but are not a security sandbox. Replay therefore requires an
explicit acknowledgement and the Docker worker:

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --acknowledge-code-execution
```

The command disables container networking, mounts the release and responses
read-only, drops Linux capabilities, enables `no-new-privileges`, and applies
CPU, memory, process, and temporary-filesystem limits. No API credential may be
mounted into the worker.

Host input/output is staged through a temporary Docker-friendly directory at
execution time. After a successful run, the package validates the evaluator
reports, derives canonical evaluation JSONL, and writes JSON, text, Markdown,
and tidy CSV summaries. This avoids Windows long-path bind-mount failures and
prevents the worker from writing directly into the requested destination.

Use `--dry-run` to inspect the complete Docker build and execution commands
without running them.

The completed one-record smoke test and 154-response replay-parity audit are
documented in [`DOCKER_REPLAY_VALIDATION.md`](DOCKER_REPLAY_VALIDATION.md).

## Test Tiers

```bash
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/integration -v
python -m unittest discover -s tests/release_parity -v
```

Unit tests use synthetic records. Integration tests exercise representative
release workflows. Release parity exhaustively checks the published scientific
matrix and repeatability audit and is mandatory before a version tag.

## Dependency Policy

`pyproject.toml` is the sole declaration of installable dependencies and
optional extras. Files under `requirements/` pin complete execution
environments, such as the canonical evaluator container; they do not duplicate
the package's abstract dependency metadata.

## Live-Run Record Boundary

Every provider response is normalized into a versioned `ProviderAttempt`
record before canonicalization. Raw payloads remain separate files referenced
by digest. Live runs record provider and route, requested and resolved model
identifiers, timestamps, decoding parameters, attempt history, usage, errors,
and request and response hashes.
