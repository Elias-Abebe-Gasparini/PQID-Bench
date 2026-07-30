# PQID-Bench Examples

These examples use the public Python API and preserve the package trust
boundary.

| example | purpose | network | generated-code execution |
| --- | --- | --- | --- |
| `reproduce_frozen.py` | reproduce and print the frozen benchmark summary | no | no |
| `build_dashboard.py` | build a standalone interactive report | no | no |
| `plan_live_run.py` | inspect a provider request plan before transmission | no | no |

From the repository root:

```bash
python examples/reproduce_frozen.py
python examples/plan_live_run.py --provider groq --model MODEL_ID --limit 3
python -m pip install ".[visualization]"
python examples/build_dashboard.py --output pqid-bench-dashboard.html
```

`plan_live_run.py` never contacts the selected provider. Actual transmission
uses `pqid-bench run-model` and requires explicit prompt-export
acknowledgement. Executable replay is a separate Docker-backed operation.
