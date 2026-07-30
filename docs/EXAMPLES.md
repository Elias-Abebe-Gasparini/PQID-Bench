# Worked Examples

The repository includes three small scripts that demonstrate the public Python
API without blurring collection, evaluation, and presentation.

## Reproduce Frozen Results

```bash
python examples/reproduce_frozen.py
python examples/reproduce_frozen.py --format markdown
```

This reads the archived canonical evaluation records and prints the same
21-model, 154-prompt summary used by the package. It does not execute generated
code or contact a provider.

## Build an Interactive Dashboard

```bash
python -m pip install ".[visualization]"
python examples/build_dashboard.py --output pqid-bench-dashboard.html
```

Use `--plotlyjs inline` when the HTML file must remain fully offline.

## Plan a Live Model Run

```bash
python examples/plan_live_run.py \
  --provider groq \
  --model MODEL_ID \
  --limit 3
```

The planner validates the route, evidence manifest, prompt selection, and
prospective output contract. It reports `contacts_provider: false`; no
credential or prompt-export acknowledgement is needed until an actual
`run-model` invocation.

## Trust Boundary

| operation | contacts a provider | executes generated code |
| --- | ---: | ---: |
| reproduce example | no | no |
| dashboard example | no | no |
| live-run planner | no | no |
| `pqid-bench run-model` | yes | no |
| `pqid-bench replay` | no | yes, isolated Docker worker |

See the
[complete examples directory](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/tree/main/examples),
[Live Model Testing](user-manual/live-model-testing.md), and [Security and
Governance](user-manual/security-governance.md).
