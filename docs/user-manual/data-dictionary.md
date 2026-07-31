# Data Dictionary

## 1. General Record Rules

PQID-Bench uses UTF-8 JSON and JSONL records. In JSONL files:

- each nonblank line must contain one JSON object;
- line order is preserved as evidence but is not used as a record key;
- identifiers are strings;
- hashes are lowercase 64-character SHA-256 hexadecimal strings where the
  schema applies that constraint;
- timestamps use ISO 8601 date-time strings; and
- `null` means unavailable or inapplicable, not false.

All six JSON Schemas use JSON Schema draft 2020-12 and allow additional
properties. The required fields define the interoperable minimum. Additional
fields preserve provider, evaluator, or analysis detail without weakening that
minimum.

Installed schemas are available under `src/pqid_bench/schemas/` and through
`pqid_bench.schemas.load_schema`.

## 2. Benchmark Record

Schema: `benchmark-record.schema.json`  
Schema name: `benchmark-record`

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `row_id` | string | yes | stable identifier for the source benchmark row |
| `instruction` | string | yes | natural-language task associated with the row |
| `source_code` | string | no | reference or source program retained for benchmark construction |
| `pqid_bench_effective_release_bucket` | enum | no | `strict_n8` or `extended_n8` clean-release bucket |

The benchmark record is a source/governance object. It is not the same object
as a model-facing prompt or model response.

## 3. Prompt Record

Schema: `prompt.schema.json`  
Schema name: `prompt`

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `prompt_id` | string | yes | stable model-facing prompt identifier |
| `row_id` | string | yes | source benchmark-row identifier |
| `prompt` | string | yes | exact text transmitted or presented to a model |
| `prompt_sha256` | string | no | SHA-256 digest of the canonical prompt text |

The frozen external-generation prompt IDs use names such as
`pqid_bench_external_gen_0001`. A prompt ID is the join key across prompt,
response, evaluation, and provider-attempt records.

## 4. Canonical Response Record

Schema: `response.schema.json`  
Schema name: `response`

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `prompt_id` | string | yes | prompt answered by this record |
| `model` | string | no | canonical model or model-route label |
| `provider` | string | no | provider associated with the response |
| `generated_text` | string or null | no | complete normalized textual response |
| `generated_code` | string or null | no | extracted program submitted to evaluation |
| `response_sha256` | string | no | digest of the canonical response representation |
| `error` | object or null | no | normalized provider or collection error |

The schema requires only `prompt_id` because response artifacts may retain
failed or empty provider attempts. Scientific completion requirements are
enforced by the run/audit layer rather than by pretending every response has
generated code.

`generated_text` and `generated_code` are distinct. The latter is the extracted
program used by the evaluator; the former preserves the broader response.

## 5. Evaluation Record

Schema: `evaluation.schema.json`  
Schema name: `evaluation`

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `prompt_id` | string | yes | evaluated prompt |
| `model` | string | yes | model or route assigned to the cell |
| `report_executable` | Boolean | yes | generated program executed under the evaluator |
| `report_assembly_admissible` | Boolean | no | executable circuit serialized successfully to OpenQASM 3 |
| `report_signature_match` | Boolean | yes | output passed the frozen reference-signature predicate |
| `ordered_wire_tape_match` | Boolean | no | exact ordered operation and operand tape matched |
| `parameter_aware_tape_match` | Boolean | no | normalized ordered parameter sequence also matched |
| `row_id` | string | no | source benchmark-row identifier |

The canonical key is `(model, prompt_id)`. Duplicate keys are rejected by the
summarizer.

### Accepted endpoint aliases

The CLI accepts these equivalent input names:

| Endpoint | Accepted names |
| --- | --- |
| execution | `report_executable`, `execution`, `execution_success` |
| assembly admissibility | `report_assembly_admissible`, `assembly`, `assembly_admissible`, `qasm3_export_success` |
| signature | `report_signature_match`, `signature`, `signature_match` |
| ordered tape | `ordered_wire_tape_match`, `ordered_match` |
| parameter-aware tape | `parameter_aware_tape_match`, `parameter_match` |

At least one execution alias and one signature alias are required. Assembly
admissibility is optional for backward-compatible candidate bundles, but it
must be supplied for every record or omitted from every record in one summary.
Values may be JSON Booleans or integer `0`/`1`. When more than one alias for an
endpoint is supplied, every value must agree. Conflicting aliases are rejected.

### Endpoint invariants

Every record must satisfy:

```text
parameter-aware match => ordered match => signature match => execution
assembly admissibility => execution
```

These are logical validity rules, not observed correlations. The frozen
release also has `signature match => assembly admissibility` in every cell,
but that relation is a release-parity result rather than a universal input
rule. Future violations are counted in `signature_without_assembly_count`
instead of being rejected as malformed.

If ordered or parameter-aware values are incomplete across executable rows,
the corresponding aggregate count is reported as unavailable rather than as a
partial total.

## 6. Run Manifest

Schema: `run-manifest.schema.json`  
Schema name: `run-manifest`

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `package_version` | string | yes | package implementation used to create or process the run |
| `benchmark_release` | string | yes | benchmark split and frozen-target release |
| `evaluator_version` | string | yes | evaluator implementation contract |
| `predicate_version` | string | yes | reference-structure scoring predicate |
| `schema_version` | string | yes | record-schema contract |
| `artifact_manifest_version` | string | yes | release inventory contract |
| `run_type` | enum | yes | scientific role of the run |

Allowed `run_type` values:

| Value | Meaning |
| --- | --- |
| `canonical_reproduction` | deterministic reconstruction from frozen records |
| `archived_replay` | re-execution of archived generated code |
| `supplied_evaluation` | summary or comparison of supplied scored records |
| `live_replication` | new model/provider generation through `run-model` |

For candidate comparison, all seven fields must be present. Package version 1.2.1
requires exact compatibility for `benchmark_release`, `evaluator_version`,
`predicate_version`, and `schema_version`. The package and artifact-manifest
versions are retained in the report even when they are not the comparison
gate.

Minimal compatible candidate manifest:

```json
{
  "package_version": "1.2.1",
  "benchmark_release": "1.0.0",
  "evaluator_version": "pqid-bench-evaluator-1.1.0-safe-builtins",
  "predicate_version": "pqid-bench-reference-signature-1.0.0-count-map",
  "schema_version": "1.0.0",
  "artifact_manifest_version": "1.0.0",
  "run_type": "supplied_evaluation"
}
```

## 7. Provider Attempt

Schema: `provider-attempt.schema.json`  
Schema name: `provider-attempt`

The provider-attempt record is the live runner's normalization boundary. It
separates shared scientific metadata from raw provider-specific payloads.

| Field | Type | Required | Definition |
| --- | --- | ---: | --- |
| `attempt_id` | string | yes | unique request-attempt identifier |
| `run_id` | string | yes | parent experiment identifier |
| `prompt_id` | string | yes | prompt submitted in the attempt |
| `provider` | string | yes | provider organization or API family |
| `route` | string | yes | concrete endpoint or routing identifier |
| `requested_model` | string | yes | model identifier requested by the client |
| `resolved_model` | string or null | no | model identifier reported or resolved by the provider |
| `request_sha256` | SHA-256 string | yes | digest of the canonical request |
| `raw_response_path` | string or null | no | path to the separately archived raw payload |
| `raw_response_sha256` | SHA-256 string or null | no | digest of the raw payload |
| `status` | string | yes | normalized attempt outcome |
| `attempt_index` | integer | yes | one-based attempt number within retry history |
| `started_at` | date-time string | yes | request start time |
| `completed_at` | date-time string or null | no | completion time |
| `transport_affected` | Boolean | no | whether transport/provider failure affected observation |

The supporting `ProviderAttempt` dataclass additionally defines:

| Field | Definition |
| --- | --- |
| `response_text` | normalized response text when available |
| `provider_request_id` | provider-side request identifier |
| `finish_reason` | provider termination reason |
| `input_tokens` | reported input-token usage |
| `output_tokens` | reported output-token usage |
| `error_type` | normalized error class |
| `error_message` | retained error message |

Because schemas allow additional properties, these fields can be preserved
without embedding raw provider response trees in the shared record.

### Live-run files

`run-model` writes a credential-free `requests.jsonl`, canonical
`responses.jsonl`, normalized `provider-attempts.jsonl`, atomic prompt state
under `records/`, raw bodies under `raw/`, a `run-manifest.json`, and a
`run-summary.json`.

Each request record contains `request_body`, `request_sha256`,
`model_input_sha256`, `prompt_record_sha256`, and the explicit
`target_metadata_policy`. The body contains only the selected model, model
messages, and declared generation controls. It never contains the evaluator's
`target_metadata` field.

The live run manifest adds `run_id`, provider, route, requested model, prompt
and request-set digests, generation configuration, credential source class,
retry policy, and the Boolean audit assertions
`credential_value_recorded`, `target_metadata_exported`, and
`third_party_prompt_export_acknowledged`.

In live response rows, `model` and `requested_model` are the stable requested
analysis key. `resolved_model` records the model identifier returned by the
provider for that prompt. Keeping those fields separate prevents one
replication run from silently fragmenting into multiple candidate groups while
still exposing routing or snapshot variation. Persisted prompt-source and
output-file references are release-relative or filename-only; machine-local
absolute paths are not part of the portable run artifact.

## 8. Benchmark Summary Output

`doctor`, `reproduce`, `evaluate`, and nested sections of `compare` emit
versioned JSON. The `BenchmarkSummary` fields are:

| Field | Type | Definition |
| --- | --- | --- |
| `cells` | integer | supplied model-prompt cell count |
| `models` | integer | distinct model labels |
| `prompts` | integer | distinct prompt IDs |
| `execution_count` | integer | executable cells |
| `assembly_count` | integer or null | quantum-assembly-admissible cells |
| `signature_count` | integer | signature-match cells |
| `ordered_count` | integer or null | complete ordered-tape matches |
| `parameter_count` | integer or null | complete parameter-aware matches |
| `es_gap_count` | integer | execution count minus signature count |
| `execution_rate` | number | execution count divided by cells |
| `assembly_rate` | number or null | assembly count divided by cells |
| `signature_rate` | number | signature count divided by cells |
| `es_gap_rate` | number | ES-Gap count divided by cells |
| `execution_to_assembly_attrition_count` | integer or null | execution count minus assembly count |
| `execution_to_assembly_attrition_rate` | number or null | execution-to-assembly attrition divided by cells |
| `as_gap_count` | integer or null | signed assembly count minus signature count |
| `as_gap_rate` | number or null | AS-Gap count divided by cells |
| `assembly_without_signature_count` | integer or null | assembly-admissible cells without signature match |
| `signature_without_assembly_count` | integer or null | signature matches without assembly admissibility |
| `as_gap_share_of_es_gap` | number or null | AS-Gap count divided by ES-Gap count |
| `executable_signature_disagreement_rate` | number or null | ES-Gap count divided by execution count |
| `identifiable_cells` | integer or null | cells under identifiable-subset policy |
| `identifiable_execution_count` | integer or null | identifiable executions |
| `identifiable_signature_count` | integer or null | identifiable signature matches |
| `identifiable_disagreement_count` | integer or null | identifiable executable mismatches |
| `structural_hallucination_rate` | number or null | identifiable disagreement divided by identifiable execution |

Every summary also contains the seven run/version fields.

## 9. Comparison Scope

`compare` adds `comparison_scope`:

| Field | Definition |
| --- | --- |
| `mode` | `full_test_set` or `matched_subset` |
| `prompt_count` | number of common prompts |
| `prompt_ids_sha256` | digest of sorted prompt IDs joined with newline separators |
| `prompt_ids` | exact ordered list of compared prompt IDs |
| `candidate_models` | number of candidate models |
| `candidate_cells` | candidate cells |
| `frozen_models` | frozen comparator models |
| `frozen_cells` | frozen comparator cells |
| `identifiable_exclusions` | frozen prompt IDs excluded only for identifiable-subset metrics |

The candidate and frozen model counts need not be equal. Their prompt
denominators must be equal.

## 10. Artifact Manifest

`ARTIFACT_MANIFEST.tsv` has exactly three tab-separated columns:

| Column | Definition |
| --- | --- |
| `path` | safe path relative to the release root |
| `bytes` | exact file size |
| `sha256` | lowercase SHA-256 digest |

The manifest does not include itself. Verification rejects duplicate, empty,
absolute, and parent-traversal paths.

## 11. Minimal Evaluation JSONL

Each line below is a separate JSON object:

```json
{"prompt_id":"pqid_bench_external_gen_0001","model":"example-model","report_executable":true,"report_signature_match":false,"ordered_wire_tape_match":false,"parameter_aware_tape_match":false}
{"prompt_id":"pqid_bench_external_gen_0002","model":"example-model","report_executable":true,"report_signature_match":true,"ordered_wire_tape_match":true,"parameter_aware_tape_match":true}
```

This example can be summarized with `evaluate`, but it cannot be compared in
default mode because it does not contain all 154 frozen prompt IDs.
