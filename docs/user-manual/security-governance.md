# Security And Governance

## 1. Trust Model

PQID-Bench separates data processing from generated-code execution.

The following commands are data-only:

```text
doctor
verify
reproduce
evaluate
compare
```

They parse metadata, hashes, JSON/JSONL, and archived evaluation results. They
do not execute generated Python or contact providers.

`run-model --dry-run` validates a network plan without reading credentials or
contacting a provider. `run-model` crosses the third-party data-export and
billing boundary but does not execute generated code.

`replay` crosses the generated-code trust boundary and therefore requires
Docker plus explicit acknowledgement.

## 2. Restricted Built-Ins Are Not A Sandbox

The evaluator's restricted namespace defines what generated programs are
admissible under the benchmark. It is part of the scientific evaluator
contract.

It is not presented as a complete security sandbox. Process isolation,
network controls, filesystem controls, and resource limits are supplied by the
Docker boundary.

## 3. Docker Controls

The replay worker is planned with:

- `--network none`;
- `--read-only`;
- `--cap-drop ALL`;
- `--security-opt no-new-privileges`;
- `--pids-limit 128`;
- `--memory 2g`;
- `--cpus 2`;
- `--tmpfs /tmp:rw,noexec,nosuid,size=256m`;
- read-only release and response mounts; and
- no API credentials.

The runtime user is nonroot. These controls reduce risk but do not prove that
arbitrary code is safe.

## 4. Explicit Acknowledgement

Replay requires:

```text
--acknowledge-code-execution
```

Without it, the command exits before constructing or running the worker.

The flag is also required for `--dry-run`. This prevents replay from becoming
an unnoticed extension of ordinary data-only workflows.

Live generation separately requires:

```text
--acknowledge-third-party-prompt-export
```

That acknowledgement is not required for `run-model --dry-run`, which exports
nothing. The two acknowledgements are not interchangeable.

## 5. Input And Output Staging

The package stages external response files and worker output through a
temporary short-path directory. This:

- avoids deeply nested Windows bind-mount failures;
- limits the writable host surface;
- prevents direct writes into the requested destination during execution; and
- permits post-run validation of expected output files.

The evaluator must produce two regular report files:

```text
pqid_bench_external_model_generation_harness_report.json
pqid_bench_external_model_generation_harness_report.md
```

Symlinked or missing outputs are rejected.

After validating those reports, the host package derives canonical evaluation
JSONL and JSON, text, Markdown, and tidy CSV summaries. These derivatives do
not execute generated code or change evaluator outcomes.

## 6. Credentials

Frozen-result reproduction does not require API credentials. `run-model`
accepts a key from a preset or explicit environment variable, or from an
external file supplied through `--api-key-file`.

Never place these in the repository or release bundle:

- `.env` files;
- API-key files;
- access tokens;
- billing credentials;
- cloud-provider profiles; or
- machine-local secret paths.

The release builder scans for known local path and credential-file patterns.
That scan supplements, rather than replaces, repository-secret scanning.

Do not mount credential directories into the replay container.

## 7. Provider Data

The live adapter retains:

- requested and resolved model identifiers;
- provider and route;
- timestamps;
- request and response hashes;
- usage metadata;
- attempt and recovery history;
- error types; and
- a `transport_affected` indicator.

Raw provider payloads remain separate files referenced by digest. This limits
provider-specific structure in the shared scientific record.

Credential values are held only in request headers and are not serialized.
The manifest records only the source class or environment-variable name.
Provider route URLs may not contain usernames, passwords, query strings, or
fragments. The request body may not contain credential-like keys.

## 8. Privacy

Public artifacts must not contain:

- user-profile paths;
- local credential filenames;
- temporary launcher defaults that expose a workstation;
- private billing or account metadata; or
- caches and transient files.

Model-facing prompt records must not expose hidden benchmark targets beyond
what was actually transmitted.

## 9. Frozen Artifact Governance

Canonical artifacts are immutable evidence. New operations write to separate
locations:

- candidate summaries do not overwrite frozen summaries;
- matched-subset reports retain their scope;
- replay output uses a new output directory;
- recovery attempts remain visible; and
- live replications receive new run identities.

Do not edit a canonical response to repair a failed evaluation. Preserve the
original record and log any recovery as another attempt.

## 10. Version Governance

Changes to:

- evaluator behavior require a new evaluator identifier and impact audit;
- structural scoring require a new predicate identifier;
- interoperable records may require a schema version;
- benchmark prompts, split, or targets require a benchmark release; and
- package code require a package version.

Independent version dimensions prevent a software patch from being mistaken
for a new scientific benchmark.

## 11. Incident Procedure

If a suspected secret, private path, malformed artifact, or unsafe replay
output is found:

1. stop publication or replay;
2. preserve the local evidence needed to diagnose the issue;
3. rotate exposed credentials outside the repository;
4. remove the sensitive object from the public package source;
5. rebuild the manifest and all release archives;
6. rerun privacy, integrity, and parity checks;
7. issue a new package/release identity when public bytes have already been
   distributed; and
8. document scientific impact separately from packaging impact.

Never rewrite an already published checksum while pretending the artifact is
unchanged.

## 12. User Checklist Before Replay

- [ ] Docker Engine is running.
- [ ] The response file is known and archived.
- [ ] Release-manifest verification passes.
- [ ] The output directory is not canonical evidence.
- [ ] No credentials are mounted or inherited.
- [ ] The dry-run command has been inspected.
- [ ] The timeout and resource limits are acceptable.
- [ ] Generated-code execution risk is understood.
