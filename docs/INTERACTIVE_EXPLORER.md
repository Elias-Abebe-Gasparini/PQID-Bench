# Interactive Explorer

The PQID-Bench explorer is a static Plotly report generated deterministically
from the frozen evaluator, ordered-structure, and repeatability artifacts. It
does not contact model providers, retain credentials, execute generated code,
or change any benchmark result.

[Open the interactive explorer](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html)

The explorer provides five coordinated views:

1. the operational-to-structural measurement ladder;
2. model-level execution, assembly, and reference-signature profiles;
3. a component and nested-structure recovery matrix;
4. three-run stochastic-repeatability estimates; and
5. provider-route aggregates, reported descriptively rather than as causal
   vendor comparisons.

## Workflow Map

[Open the ecosystem workflow diagram](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/assets/ecosystem-flow.svg)

The flowchart separates the frozen PQID source, deterministic benchmark split,
model-response collection, isolated Docker replay, numerical reports, and
interactive presentation. The explorer is the final presentation layer; it
does not sit inside the scoring path.

## Generate A Local Report

Install the optional visualization dependency:

```bash
python -m pip install "pqid-bench[visualization]"
```

Generate a self-contained report that works without a network connection:

```bash
pqid-bench dashboard \
  --release-dir /path/to/PQID-Bench \
  --output pqid-bench-dashboard.html
```

The default embeds Plotly.js in the output HTML. Use `--plotlyjs cdn` for a
smaller file that loads Plotly.js from its content-delivery network.

The command validates the 21 model rows against the frozen aggregate counts
before writing any output. Its model table and charts can therefore be traced
back to the same archived evidence used by `pqid-bench reproduce`.

## Interface Boundary

Plotly replaces the former Gradio concept for result exploration, not for
provider-backed model execution. Live model collection remains an explicit CLI
operation through `pqid-bench run-model`, and generated-code execution remains
confined to `pqid-bench replay` inside the isolated Docker evaluator. A
browser-based live runner would require a separate authenticated server and is
outside the frozen release.
