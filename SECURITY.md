# Security Policy

PQID-Bench separates offline evidence reproduction, third-party API collection,
and execution of generated code. Please read
[Security and Privacy](docs/SECURITY_AND_PRIVACY.md) before using `run-model`
or `replay`.

## Supported Versions

| Component | Supported line |
| --- | --- |
| Python toolkit | latest published `1.1.x` release |
| frozen benchmark | `1.0.0` integrity and documentation fixes |
| evaluator container | `1.0.0` image contract |

Older development snapshots are not supported.

## Reporting a Vulnerability

Do not open a public issue for a vulnerability, exposed credential, unsafe
execution path, or private-data disclosure.

Use GitHub's **Report a vulnerability** action in the repository Security tab.
If private vulnerability reporting is temporarily unavailable, contact the
repository owner through the GitHub profile linked from the repository and
share only enough information to establish a private reporting channel.

Include the affected version or commit, operating system, minimal reproduction,
expected and observed behavior, and potential impact. Never include a live API
credential or sensitive provider response.

The maintainer will acknowledge a complete report as soon as practicable,
validate its scope, and coordinate remediation and disclosure. A frozen
scientific artifact will not be silently rewritten: any integrity-relevant
correction will receive an explicit audit trail and version identifier.

## Trust Boundary

- `verify`, `reproduce`, `evaluate`, `compare`, and `dashboard` do not execute
  generated model code.
- `run-model` contacts a third-party endpoint only after explicit prompt-export
  acknowledgement and must not persist credential values.
- `replay` executes untrusted generated code only in the credential-free,
  network-disabled Docker evaluator after explicit code-execution
  acknowledgement.

The complete operational controls are documented in
[Security and Governance](docs/user-manual/security-governance.md).
