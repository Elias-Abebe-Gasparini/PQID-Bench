# PQID-Bench Software Paper Blueprint

## 1. Purpose

This document separates three related outputs:

| Output | Primary question | Main evidence |
| --- | --- | --- |
| benchmark paper | what do current models reveal about executable and structural recovery? | frozen 21-model experiment and robustness analyses |
| user manual | how does a user install, inspect, reproduce, collect, compare, and replay? | commands, schemas, workflows, and troubleshooting |
| software paper | how does the package make those operations reproducible, traceable, safe, and independently auditable? | software architecture, contract tests, portability, provider-failure injection, and replay parity |

The software paper should not repeat the benchmark paper's complete empirical
story. Its central contribution is the executable reproducibility contract:
release bytes, scientific denominators, evaluator identity, predicate identity,
record schemas, and replay controls are checked as separate, versioned objects.

## 2. Candidate Titles

1. **PQID-Bench: A Reproducibility Toolkit for Validation-Aware Quantum
   Program Generation**
2. **From Frozen Evidence to Denominator-Safe Replication: The PQID-Bench
   Software Toolkit**
3. **PQID-Bench: Auditable Evaluation and Isolated Replay for Generated
   Quantum Programs**

The first title is the clearest general-purpose choice. The second foregrounds
the methodological novelty. The third is strongest when the venue emphasizes
research software or secure evaluation infrastructure.

## 3. Contribution Thesis

The paper should defend one compact thesis:

> PQID-Bench turns a frozen quantum-program-generation study into an auditable
> software contract by separating byte verification, metric reproduction,
> supplied-record evaluation, traceable live collection, denominator-aligned
> comparison, and isolated executable replay.

Five supporting contributions follow:

1. a versioned evidence model that distinguishes package, benchmark,
   evaluator, predicate, schema, and artifact-manifest identity;
2. a dependency-light offline path for deterministic metric reproduction;
3. denominator and endpoint invariants that reject scientifically invalid
   comparisons before reporting a score; and
4. an explicitly authorized, resumable collection path that separates
   credential-free request evidence from provider-specific raw payloads; and
5. a credential-free, network-disabled Docker path for explicitly authorized
   replay of archived generated programs.

## 4. Research Questions

| ID | Research question |
| --- | --- |
| RQ1 | Can an independent installation reproduce the frozen summary exactly from archived evaluation records? |
| RQ2 | Does the package detect byte corruption, schema violations, endpoint contradictions, and denominator mismatch? |
| RQ3 | Does isolated replay reproduce the archived evaluator outputs and aggregate counts? |
| RQ4 | Are installation, verification, and reproduction portable across supported Python and operating-system environments? |
| RQ5 | Does the interface make reproduction, new evaluation, and stochastic replication difficult to conflate? |
| RQ6 | What time, storage, and optional-runtime costs are required at each reproduction level? |
| RQ7 | Does live collection preserve request identity and recover from provider failures without leaking credentials or target metadata? |

These questions concern software behavior and scientific auditability. They do
not ask whether one model architecture causes better quantum reasoning.

## 5. Proposed Paper Structure

### 5.1 Motivation

Explain why a collection of scripts and output files is not yet a
reproducibility interface. Emphasize three recurring risks:

- comparing different prompt denominators;
- silently changing evaluator or target predicates; and
- treating regenerated stochastic model text as reproduction of archived
  outputs.

### 5.2 Design Principles

Introduce:

- immutable evidence before recomputation;
- explicit version dimensions;
- data-only operations by default;
- one normalized model-prompt cell key;
- fail-closed endpoint and denominator validation;
- raw provider evidence separated from normalized records; and
- explicit consent plus isolation for generated-code execution.

### 5.3 Architecture

Describe five layers:

1. **Evidence layer:** manifest, frozen prompts, responses, evaluations, and
   analysis artifacts.
2. **Contract layer:** JSON Schemas, version identifiers, logical endpoint
   nesting, and denominator rules.
3. **Collection layer:** model-facing request construction, provider transport,
   atomic resume state, attempts, and raw payload digests.
4. **Computation layer:** summary, comparison, verification, and replay
   orchestration.
5. **Interface layer:** CLI, stable Python API, documentation, and container
   entry point.

### 5.4 User Operations

Present the seven CLI commands as distinct operations:

| Command | Scientific role |
| --- | --- |
| `doctor` | environment description |
| `verify` | release-byte integrity |
| `reproduce` | deterministic frozen-result reconstruction |
| `evaluate` | summary of compatible scored records |
| `compare` | prompt-aligned candidate comparison |
| `run-model` | traceable fresh stochastic collection |
| `replay` | isolated execution of archived or newly collected code |

### 5.5 Record And Metric Contracts

Summarize the six schemas and the nesting relation:

```text
parameter-aware => ordered => signature => execution
assembly admissibility => execution
```

For the frozen release, separately validate the empirical chain `parameter <=
ordered <= signature <= assembly <= execution`. Define the ES-Gap, its nested
Assembly-Structure Gap (AS-Gap), their exact decomposition, and conditional
executable disagreement, but refer readers to the benchmark paper for
substantive model comparisons.

### 5.6 Validation Study

Report the experiments in Section 6 below. This should be the empirical center
of the software paper.

### 5.7 Limitations And Governance

State that package version 1.2.0:

- supports only OpenAI-compatible chat completion routes in its stable live
  adapter;
- does not estimate or control provider prices, quotas, retention, or policy;
- does not prove semantic equivalence;
- cannot make arbitrary Python intrinsically safe;
- does not infer compatibility across changed evaluator or predicate versions;
  and
- requires new model calls to be identified as stochastic replications.

## 6. Validation Plan

### Experiment 1: clean-install reproduction

For every supported Python environment:

1. create a fresh environment;
2. install the exact source distribution;
3. run `pqid-bench doctor`;
4. run `pqid-bench verify RELEASE_DIR --full`;
5. run `pqid-bench reproduce --release-dir RELEASE_DIR`; and
6. compare the emitted JSON with the frozen summary.

Report installation success, command exit status, elapsed time, peak disk use,
and count parity.

### Experiment 2: artifact-integrity failure injection

Starting from a disposable release copy, independently:

- alter one byte;
- delete one manifested file;
- change one manifest size;
- change one manifest hash;
- duplicate a manifest path; and
- add an unsafe absolute or parent-traversal path.

Each mutation should be detected, localized, and returned with a nonzero exit
status. The clean control must pass.

### Experiment 3: evaluation-contract failure injection

Construct minimal fixtures that contain:

- a duplicate `(model, prompt_id)` cell;
- a missing execution endpoint;
- conflicting aliases;
- parameter match without ordered match;
- ordered match without signature match; and
- signature match without execution.

Each fixture should fail before aggregate statistics are emitted.

### Experiment 4: denominator-safety matrix

Exercise `compare` with:

- one complete 154-prompt candidate model;
- several complete candidate models;
- a common strict subset without `--allow-partial`;
- the same subset with `--allow-partial`;
- unequal prompt sets across candidate models;
- an unknown prompt ID; and
- each incompatible version dimension.

The report should distinguish full-test and matched-subset comparisons and
verify that no partial candidate is compared against the complete frozen
matrix.

### Experiment 5: executable-replay parity

With the archived container or a locally built image:

1. inspect a dry-run plan;
2. confirm the documented isolation flags;
3. replay the frozen response bundle;
4. compare cell-level evaluator records; and
5. compare aggregate execution and structural counts.

Record the image digest, Docker version, host platform, elapsed time, and every
parity difference. A zero-difference result supports replay parity; it does not
prove universal container security.

### Experiment 6: live-collection failure injection

Use an injected transport rather than a paid provider to test:

- credential-free dry-run planning;
- target-metadata exclusion;
- credential non-persistence;
- success canonicalization and raw-payload hashing;
- retryable rate-limit recovery;
- explicit terminal-error recovery;
- completed-row resume skipping;
- uncertain in-flight refusal and acknowledged duplicate draw; and
- insecure-route and secret-field rejection.

Optionally report a real one-prompt smoke run as deployment validation, clearly
separate from deterministic contract tests.

### Experiment 7: portability matrix

At minimum, test supported Python versions on Windows and Linux. macOS may be
added when an actual environment is available. Separate:

- data-only command portability; and
- Docker replay portability.

Do not report an untested platform as validated merely because the package is
written in portable Python.

### Experiment 8: independent-user quickstart

Give a frozen release and the reviewer quickstart to one or more users who did
not implement the package. Measure:

- time to first valid integrity report;
- time to reproduced summary;
- number and type of interventions;
- encountered error messages; and
- whether the user correctly distinguishes reproduction from replication.

This is the strongest usability evidence, but it should be reported only after
the exercise has actually occurred.

## 7. Suggested Figures

1. **Architecture and trust-boundary diagram:** evidence, contracts,
   collection, computation, CLI/API, and the isolated replay worker.
2. **Operation decision tree:** verify, reproduce, collect, evaluate, compare,
   or replay.
3. **Version-compatibility lattice:** which identity changes invalidate direct
   comparison.
4. **Validation matrix:** clean controls and injected failures by check.
5. **Replay data-flow diagram:** read-only inputs, network-disabled worker, and
   allowlisted outputs.
6. **Live recovery state machine:** pending, in-flight, success, error,
   uncertain interruption, and explicit recovery paths.

Use diagrams to explain contracts and workflows. Do not reuse benchmark-result
figures merely to increase the visual count.

## 8. Suggested Tables

1. command and trust-boundary matrix;
2. schema and join-key dictionary;
3. version dimensions and compatibility consequences;
4. clean-install portability results;
5. failure-injection detection results;
6. replay parity results;
7. live failure-injection and secret-exclusion results;
8. resource and elapsed-time requirements by reproduction level; and
9. claim-to-evidence crosswalk.

## 9. Claim-To-Evidence Crosswalk

| Proposed claim | Required evidence |
| --- | --- |
| exact frozen-summary reproduction | clean-install parity on the released sdist or wheel |
| tamper-evident release | complete manifest verification plus injected-corruption detection |
| denominator-safe comparison | complete and partial comparison contract tests |
| evaluator replay parity | cell-level and aggregate comparison from the isolated worker |
| traceable live replication | mocked failure-injection tests plus one declared deployment smoke test |
| credentials and target metadata are not persisted | artifact-content assertions over every generated live-run file |
| portable data-only workflow | successful clean installs on every named platform/version |
| usable by independent researchers | documented independent-user exercise |
| secure replay | do not make this absolute claim; report concrete isolation controls and residual risk |

Claims without completed evidence should remain future-work statements.

## 10. Relationship To The User Manual

The paper should explain and evaluate the design. The manual should remain the
authoritative operational reference. Avoid copying complete flag tables,
schema dictionaries, and troubleshooting lists into the paper.

Stable paper references should point to:

- the installation chapter;
- CLI and Python API references;
- the data dictionary;
- metrics and invariants;
- reproducibility contract;
- security and governance; and
- release-specific validation reports.

## 11. Evidence Freeze For A Software Submission

Create a distinct software-paper evidence freeze containing:

- exact wheel and source-distribution hashes;
- exact benchmark-release archive hash;
- container image digest and optional offline image archive hash;
- test logs by Python and operating-system environment;
- failure-injection fixtures and expected outcomes;
- live-run transport fixtures, recovery logs, and non-persistence assertions;
- replay-parity report;
- documentation build output;
- a software bill of materials or dependency inventory;
- archival DOI and repository tag; and
- a machine-readable run manifest for each validation environment.

The software-paper freeze should reference, not overwrite, the benchmark's
scientific freeze.

## 12. Presubmission Gates

- Every documented command is generated from or tested against the released
  parser.
- Every schema field appears in the data dictionary.
- Every local documentation link resolves.
- The wheel and source distribution contain the complete manual and schemas.
- A clean installation reproduces the canonical counts.
- The released archive passes `verify --full`.
- Docker replay parity is documented for the released image.
- Supported and unsupported provider protocols are named explicitly.
- Live transport tests make no undeclared external API calls.
- Completed validation is separated from proposed validation.
- The benchmark paper, manual, and software paper use the same version
  identifiers and metric terminology.

Once these gates pass, the package supports a credible arXiv software paper
and a later research-software submission without forcing either document to
duplicate the benchmark manuscript.
