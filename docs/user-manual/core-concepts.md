# Core Concepts

## Package, Benchmark, And Evidence Bundle

`pqid-bench` is the installable interface. PQID-Bench v1.0.0 is the frozen
benchmark release. The evidence bundle contains the prompts, archived
responses, evaluations, robustness analyses, repeatability records,
regeneration scripts, and reproducibility documentation. Unpublished
manuscript source and manuscript-facing publication derivatives are not part
of the public evidence bundle.

These are related but not interchangeable. The small Python wheel does not
embed the evidence bundle.

## Six Operations

### Verification

Verification checks whether the release files have their declared byte sizes
and SHA-256 digests. Full verification additionally checks frozen scientific
counts and repeatability dimensions.

### Reproduction

Reproduction recomputes the published summary from archived evaluation
records. It does not run generated programs and does not contact providers.

### Evaluation Summarization

Evaluation summarization computes the same metric family from a supplied
canonical evaluation JSONL file. The file must already contain scored
model-prompt cells.

### Candidate Comparison

Comparison aligns a supplied evaluation bundle with the frozen benchmark and
reports candidate-minus-frozen deltas. The default comparison requires the
complete 154-prompt test set for every candidate model. Partial comparison is
explicit and uses the same prompt subset on both sides.

### Live Replication

Live replication exports frozen model-facing prompt messages to one declared
OpenAI-compatible model route and records a new response panel, attempt
history, raw-payload digests, and run manifest. It contacts a provider but
does not execute generated code.

### Executable Replay

Replay executes archived or newly collected generated Python in a
credential-free Docker worker. It is the only package command that executes
generated code.

## Reproduction Versus Replication

Reproduction asks whether the frozen results can be reconstructed from the
published evidence.

Replication asks whether new calls to models, providers, or routes produce
similar results. Fresh generation can differ because models, aliases,
decoding systems, provider infrastructure, and policies change. It therefore
requires a new run identity. Package version 1.1.0 implements that replication path
without treating its outputs as frozen-result reproduction.

## The Frozen Primary Matrix

The primary matrix contains:

- 21 completed model routes;
- 154 held-out prompts;
- 144 evaluator-facing reference signatures; and
- 3,234 model-prompt cells.

The matrix is rectangular: each completed model row contains one canonical
cell for every frozen prompt.

## Execution And Reference Reconstruction

Execution means that the generated program runs in the frozen evaluator
environment.

Reference-signature recovery means that an executable output matches the
frozen target's:

- qubit count;
- classical-bit count; and
- complete evaluator-visible operation-type count map.

Scalar operation-count agreement follows from count-map equality under the
frozen convention and is reported as a separate diagnostic.

Ordered operation-and-operand equality is stricter than signature recovery.
Parameter-aware ordered equality is stricter again. None of these predicates
proves unitary, measurement-distribution, physical, or semantic equivalence.

## Identifiability

Four frozen prompts do not uniquely determine every exact component of their
stored reference signature. They remain in the primary 154-prompt
stress-inclusive matrix. A prespecified 150-prompt sensitivity subset excludes
them when assigning the cell-level term `structural hallucination`.

This distinction prevents prompt underspecification from being attributed
automatically to the model.

## Independent Version Dimensions

Every core machine-readable scientific report carries:

- package version;
- benchmark release;
- evaluator version;
- structural-predicate version;
- schema version;
- artifact-manifest version; and
- run type.

Executable replay adds a seventh distribution dimension:

- container-artifact version, together with its image identity or published
  OCI registry digest.

Container artifact `1.0.0` encapsulates evaluator
`pqid-bench-evaluator-1.1.0-safe-builtins`. Those values need not have the same
version number because one identifies a distribution object and the other
identifies the scientific execution contract. Before OCI publication, the
local image ID and container-archive SHA-256 are recorded separately and no
registry digest is claimed.

The evaluator may change without changing the prompt split. A schema may
change without changing the structural predicate. Keeping the identifiers
separate makes those changes auditable.

## Trust Boundary

The ordinary offline commands treat archived evaluation records as data.
`run-model` crosses a separate network, retention, and billing boundary and
requires prompt-export acknowledgement. Generated Python is outside both
boundaries. Replay therefore requires a second acknowledgement and delegates
execution to Docker with networking disabled, read-only scientific inputs,
dropped capabilities, resource limits, and no credentials.
