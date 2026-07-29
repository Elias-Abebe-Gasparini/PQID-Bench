# Security And Privacy

## Generated-Code Execution

The benchmark's restricted built-in namespace is part of evaluator
admissibility and is not a security sandbox. The `pqid-bench` package never
executes generated code during `verify`, `reproduce`, `evaluate`, `compare`,
or `run-model`.
The separate `replay` command requires explicit acknowledgement and delegates
execution to the credential-free Docker worker with networking disabled,
read-only scientific inputs, dropped capabilities, `no-new-privileges`, and
resource limits. No interactive web gateway is included in this release.

The public package contains no API keys, provider tokens, billing credentials,
or machine-local credential paths. `run-model` resolves authentication only at
runtime from an environment variable or an explicitly named external key file.
The key value and key-file path are not persisted.

Live generation requires `--acknowledge-third-party-prompt-export`. It sends
only the model-facing `messages` array and does not send `target_metadata`.
Routes containing embedded credentials, query strings, or fragments are
rejected. Extra request bodies with credential-like field names are also
rejected because request bodies are retained for traceability.

Canonical provider outputs retain model identifiers, timestamps, request
hashes, token usage, generated code, and provider status fields needed for
traceability. They do not contain hidden benchmark targets in the model-facing
request objects.

Raw provider payloads may contain provider-specific account, safety, or
transport metadata. Inspect them before publication. Provider retention and
billing policies remain external risks that package-level hashing cannot
remove.

The immutable local stochastic-repeatability preregistration bundle contained
machine-local launcher defaults. The public package therefore includes its
scientific contracts, panel, protocols, requests, empty-output assertion, and
original cryptographic manifests, while omitting the local launcher copies and
the transcript lines that exposed workstation paths. Equivalent sanitized
runner code is available under `scripts/`.

Before each release, run the package builder. Its privacy scan rejects:

- absolute Windows user-profile paths;
- known local credential-file names;
- generated Python caches and temporary files.

Never add local `.env`, `*API_KEY*`, `*.token`, or `*.secret` files to the
repository.
