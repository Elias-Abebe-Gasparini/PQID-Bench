# Reproducibility Contract

## 1. Purpose

The reproducibility contract defines what must remain fixed for a result to be
called reproduction of PQID-Bench v1.0.0, what may vary, and what evidence is
required for stronger claims.

## 2. Frozen Scientific Objects

The release fixes:

- the 734-row clean generation population;
- the deterministic 514/66/154 split;
- 154 model-facing test prompts;
- 144 evaluator-facing target signatures;
- 21 completed model routes;
- 3,234 canonical primary cells;
- the prompt-identifiability decisions;
- the ordered and parameter-aware replay audit;
- the 72-prompt, 21-model, three-run repeatability panel;
- evaluator and predicate identifiers; and
- the artifact inventory.

Reproduction does not replace any of these objects with current provider
outputs.

## 3. Frozen Canonical Counts

| Quantity | Expected value |
| --- | ---: |
| primary cells | 3,234 |
| models | 21 |
| prompts | 154 |
| executions | 2,950 |
| assembly-admissible cells | 2,944 |
| signature matches | 1,703 |
| execution-to-assembly attrition | 6 |
| AS-Gap cells | 1,241 |
| signature matches without assembly admissibility | 0 |
| ordered matches | 1,576 |
| parameter-aware matches | 1,545 |
| identifiable cells | 3,150 |
| identifiable executions | 2,890 |
| identifiable signature matches | 1,703 |
| identifiable executable mismatches | 1,187 |
| repeatability cells | 4,536 |
| repeatability models | 21 |
| repeatability prompts | 72 |
| repeatability runs | 3 |

`pqid-bench reproduce` checks the primary summary. `pqid-bench verify --full`
checks the primary and repeatability contracts after verifying release bytes.

## 4. Reproduction Levels

### Level A: File identity

Evidence:

- archive checksum matches the release sidecar;
- internal manifest verifies all 1,125 files.

Claim:

> The reviewer has the intended public evidence bundle.

### Level B: Deterministic metric reproduction

Evidence:

- `canonical_parity` is true;
- expected primary counts are reconstructed.

Claim:

> The published summary can be recomputed from archived evaluations.

### Level C: Exhaustive scientific parity

Evidence:

- no primary parity errors;
- no repeatability parity errors.

Claim:

> The complete frozen cell and repeatability contracts reconstruct their
> published dimensions and endpoints.

### Level D: Executable replay

Evidence:

- archived responses are re-executed in the named evaluator environment;
- cell-level replay outcomes are compared with canonical outcomes;
- differences and platform-specific diagnostics are retained.

Claim:

> Archived code can be re-evaluated under the specified container, subject to
> the documented platform and security boundary.

### Level E: Stochastic replication

Evidence:

- prompts are sent again under a new versioned run;
- provider attempts, routes, timestamps, parameters, and hashes are retained;
- new outcomes are compared on aligned denominators.

Claim:

> A new experiment estimates deployment-time repeatability.

Level E is not necessary for Levels A-C. Package version 1.1.0 can collect its
records,
but a live run never becomes evidence for historical reproduction merely
because the same package created it.

## 5. Required Version Record

Every scientific report must carry:

```json
{
  "package_version": "1.1.0",
  "benchmark_release": "1.0.0",
  "evaluator_version": "pqid-bench-evaluator-1.1.0-safe-builtins",
  "predicate_version": "pqid-bench-reference-signature-1.0.0-count-map",
  "schema_version": "1.0.0",
  "artifact_manifest_version": "1.0.0",
  "run_type": "canonical_reproduction"
}
```

Change `run_type` to match the operation. Do not change a version identifier
merely to label a new output file.

Executable replay must additionally identify the separately versioned
container distribution:

```json
{
  "container_artifact_version": "1.0.0",
  "container_image_tag": "pqid-bench-evaluator:1.0.0",
  "container_image_id": "sha256:849bf53e449fd618633199c0b622abeca270591dff248cd0bf3a0fd461abf2e2",
  "container_archive_sha256": "8abff46dcb1fa10f375a713d94845d2b0bdb3cd7601985ee6ef2da24dfdc09ba",
  "oci_registry_digest": null,
  "evaluator_version": "pqid-bench-evaluator-1.1.0-safe-builtins"
}
```

The null registry digest is intentional before OCI publication. The local
image ID, archive digest, and future registry manifest digest describe
different content-addressed objects and must not be substituted for one
another.

## 6. Invariants

The record layer must satisfy:

```text
parameter-aware => ordered => signature => execution
assembly admissibility => execution
```

For frozen-release parity, the package separately verifies the observed
`signature => assembly admissibility` relation. It reports rather than
universally rejects such violations in future supplied data.

The matrix layer must satisfy:

- one unique cell per `(model, prompt_id)`;
- one common prompt set across candidate models;
- no unknown prompt ID in a frozen comparison; and
- the same prompt denominator on candidate and frozen sides.

The manifest layer must satisfy:

- safe relative paths;
- no duplicates;
- exact byte counts; and
- exact SHA-256 digests.

## 7. Allowed Variation

The following may vary without invalidating deterministic reproduction:

- host operating system;
- absolute local paths;
- Python patch version within supported releases;
- Docker Desktop implementation details;
- JSON output destination;
- wall-clock execution time; and
- harmless floating-point or platform-path diagnostics that do not change
  scoring endpoints.

Such variation must not change the frozen prompt, response, target, evaluator,
predicate, or denominator.

## 8. Changes That Require New Identity

Use a new evaluator identifier when execution admissibility or scoring
implementation changes.

Use a new predicate identifier when the structural pass condition changes.

Use a new schema version when the interoperable record contract changes
incompatibly.

Use a new benchmark release when prompts, splits, target signatures, or frozen
model roster change.

Use a new package version when the distributed software changes.

Use a new run ID and run manifest for every new stochastic replication.

## 9. Candidate Comparison Contract

A complete candidate comparison means:

- the candidate contains all 154 frozen prompt IDs;
- every candidate model has the same 154 IDs;
- no duplicate model-prompt cells exist;
- evaluator, predicate, benchmark, and schema versions are compatible; and
- frozen and candidate metrics use the same prompt denominator.

A matched-subset comparison is a different, explicitly labelled estimand.
Its output must retain the prompt IDs and their digest.

## 10. Evidence Preservation

Preserve:

- input records;
- credential-free request records and raw-response digests for live runs;
- provider-attempt history, including errors and uncertain interruptions;
- run manifests;
- command invocation;
- standard output and error when diagnosing failure;
- package and platform versions;
- result JSON;
- relevant file hashes; and
- deviations from expected counts.

Do not overwrite canonical artifacts with replay or candidate output. Use a
new output directory. Live credentials and key-file paths are not evidence and
must not be preserved in the run artifact.

## 11. Acceptance Checklist

A frozen-result reproduction is complete when:

- [ ] distribution checksums match;
- [ ] package version is recorded;
- [ ] `doctor` output is retained;
- [ ] manifest verification is valid;
- [ ] `reproduce` reports canonical parity;
- [ ] `verify --full` reports no parity errors;
- [ ] no live provider call was treated as historical reproduction;
- [ ] no generated code executed unless replay was explicitly intended; and
- [ ] all deviations are reported rather than silently normalized.
