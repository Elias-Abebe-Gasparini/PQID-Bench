# Reporting And Numerical Exports

PQID-Bench provides one numerical reporting contract through both the command
line and Python. The default JSON remains suitable for scripts and archival
records. Text and Markdown provide R-like printed summaries for readers, while
CSV provides a tidy long-form table for R, pandas, spreadsheets, and statistical
software.

Reporting never executes generated code, contacts a model provider, changes an
evaluation cell, or substitutes one denominator for another.

## Quick Start

After `replay`, the output directory already contains the candidate summary in
JSON, text, Markdown, and tidy CSV, together with canonical evaluation JSONL.
The commands below remain useful for archived records, custom destinations,
or rerendering.

Print the frozen summary in a compact terminal layout:

```bash
pqid-bench reproduce --release-dir RELEASE_DIR --format text
```

Write a copy-ready Markdown report:

```bash
pqid-bench reproduce \
  --release-dir RELEASE_DIR \
  --format markdown \
  --output reproduced-summary.md
```

Write a tidy CSV report:

```bash
pqid-bench evaluate \
  --evaluations EVALUATIONS.jsonl \
  --format csv \
  --output candidate-summary.csv
```

Print an aligned candidate-versus-frozen comparison:

```bash
pqid-bench compare \
  --evaluations EVALUATIONS.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --format text
```

## Available Formats

The `reproduce`, `evaluate`, and `compare` commands accept:

| `--format` value | Intended use | Representation |
| --- | --- | --- |
| `json` | automation, archival interchange | complete nested machine payload |
| `text` | terminal reading and review | aligned compact tables |
| `markdown` | reports, issues, appendices, notebooks | copy-ready Markdown tables |
| `csv` | R, pandas, spreadsheets, statistical tools | tidy long-form numerical rows |

`json` is the default and preserves the original command-line behavior. The
selected format is printed to standard output. When `--output` is supplied,
the same rendered content is also written to that path and its parent
directories are created automatically.

The filename extension does not override `--format`. This keeps scripted
behavior explicit and prevents a renamed file from changing its contents.

`doctor`, `verify`, and `replay --dry-run` retain JSON-only output because they
describe environment, integrity, or execution plans rather than statistical
summaries.

## Interactive HTML

`dashboard` complements rather than replaces the four numerical formats. It
loads the frozen per-model evaluator reports, ordered-structure audit, and
three-run repeatability table; checks their pooled execution, assembly, and
signature counts against `reproduce`; and writes an interactive Plotly HTML
report.

```bash
pqid-bench dashboard \
  --release-dir RELEASE_DIR \
  --output pqid-bench-dashboard.html
```

The default output embeds Plotly.js and can be opened offline. The smaller
`--plotlyjs cdn` form requires a browser network connection. Both forms keep
the numerical table in the page and allow chart export to SVG.

The public GitHub Pages explorer is built through the same interface. Its
generated HTML and SVG fallbacks are deployment products, not files in the
frozen evidence archive.

## Summary Layout

Human-readable summaries separate four blocks:

1. the package, benchmark, evaluator, predicate, schema, and manifest identity;
2. the model, prompt, and model-prompt-cell scope;
3. primary execution and reconstruction endpoints; and
4. diagnostic and identifiable-subset quantities.

Every rate is displayed beside its denominator. Assembly fields appear as
`N/A` when assembly admissibility was omitted from the complete supplied
bundle. Ordered and parameter-aware layers that were not supplied for every
executable cell also appear as `N/A`; unavailable layers are never converted
to zero. Structural-hallucination quantities appear only when an
identifiable-subset summary is available.

The frozen report begins:

```text
PQID-Bench Evaluation Summary
=============================

Scope
-----
Metric              Value
------------------  -----
Models                 21
Prompts               154
Model-prompt cells  3,234
```

The complete report then prints execution, quantum-assembly admissibility,
reference-signature, ordered, and parameter-aware endpoints; execution-to-
assembly attrition; the AS-Gap and ES-Gap; both directions of assembly-
signature disagreement; and the identifiable-subset structural-hallucination
rate.

## Tidy CSV Contract

Summary CSV has one row per numerical quantity. Stable identification columns
include:

| Column | Meaning |
| --- | --- |
| `section` | `scope`, `primary`, `diagnostic`, or `identifiable` |
| `metric_key` | stable machine-oriented metric name |
| `metric` | human-readable label |
| `available` | whether the complete metric layer was supplied |
| `count` | numerator or standalone scope count |
| `denominator` | denominator when the row represents a rate |
| `rate` | raw proportion in `[0,1]` |
| `rate_percent` | the same rate multiplied by 100 |

Version dimensions, run type, source, and canonical-parity status accompany
the rows. Repeating this metadata makes every filtered row self-identifying.

Comparison CSV uses paired columns:

```text
candidate_count
candidate_denominator
candidate_rate
frozen_count
frozen_denominator
frozen_rate
delta_rate
delta_percentage_points
```

The delta is always candidate minus frozen. The comparison command first
aligns prompt denominators; the renderer does not perform or weaken that
alignment.

## Importing Into R

Generate a report and read it directly:

```r
system2(
  "pqid-bench",
  c(
    "reproduce",
    "--release-dir", shQuote("PQID-Bench-v1.0.0"),
    "--format", "csv",
    "--output", shQuote("pqid-bench-summary.csv")
  )
)

summary_rows <- read.csv(
  "pqid-bench-summary.csv",
  stringsAsFactors = FALSE
)

primary <- subset(summary_rows, section == "primary" & available == "true")
primary[c("metric", "count", "denominator", "rate_percent")]
```

Because the file is tidy rather than presentation-oriented, the same rows can
be passed to `dplyr`, `data.table`, `ggplot2`, or a manuscript-table workflow
without parsing console text.

## Python Reporting Interface

`BenchmarkSummary` supports direct printing:

```python
from pathlib import Path

from pqid_bench import reproduce_release

summary = reproduce_release(Path("PQID-Bench-v1.0.0"))
print(summary)
```

Explicit renderers are available when the destination matters:

```python
print(summary.to_text())

Path("summary.md").write_text(summary.to_markdown(), encoding="utf-8")
Path("summary.csv").write_text(summary.to_csv(), encoding="utf-8")

rows = summary.to_rows()
```

The top-level functional interface is:

```python
from pqid_bench import (
    REPORT_FORMATS,
    render_comparison,
    render_summary,
    summary_rows,
)
```

`to_rows()` and `summary_rows()` return ordinary lists of dictionaries and do
not require pandas. A user who already has pandas can write:

```python
import pandas as pd

frame = pd.DataFrame(summary.to_rows())
```

No dataframe library is added to the core package dependency set.

## Statistical Boundary

The summary renderer reports descriptive counts, rates, operational and
nested reconstruction endpoints, the AS-Gap and ES-Gap, conditional
disagreement, and identifiable-subset structural hallucination. The comparison
renderer reports aligned descriptive differences.

The release contains separately versioned inferential, robustness,
family/vendor-sensitivity, and stochastic-repeatability artifacts. Rendering a
summary does not refit those models, recompute bootstrap intervals, or turn a
descriptive comparison into a causal estimate. Use the published artifacts and
their methods documentation when those analyses are required.

This separation is deliberate: a readable report may change presentation, but
it must not change the frozen scientific result.
