# Regenerating Publication Outputs

PQID-Bench v1.0.0 distributes the frozen numerical evidence and the scripts
needed to recreate publication-facing figures and tables. It intentionally
does not distribute rendered manuscript figures, captions, editable figure
sources, copy-ready manuscript tables, the manuscript walkthrough notebook,
or the undeployed interactive gateway.

This boundary separates scientific reproducibility inputs from submission
products. Regenerated files are local working outputs and are not part of the
frozen public manifest.

## Environment

From the release root:

```powershell
python -m pip install -r requirements.txt
```

## Main Regeneration Commands

The following scripts derive visual outputs from the archived data and
analysis files:

```powershell
python ".\scripts\build_clean_vs_mutation_stress_schematic.py"
python ".\scripts\build_pqid_bench_result_panels.py"
python ".\scripts\build_pqid_bench_inferential_figures.py"
python ".\scripts\build_pqid_bench_diagnostic_panels.py"
python ".\scripts\build_supplemental_method_expansion_figures.py"
python ".\scripts\build_pqid_bench_stochastic_repeatability_panel.py"
```

Additional specialized builders under `scripts/` regenerate retrieval,
signature-sensitivity, circuit-exemplar, and release-readiness panels.

Several analysis scripts can also emit tabular derivatives under a local
`tables_copy_ready/` directory. The canonical public evidence remains the
corresponding JSON, JSONL, CSV, TSV, and Markdown analysis files under
`artifacts/`; copy-formatted derivatives are not authoritative inputs.

## Verification Boundary

`ARTIFACT_MANIFEST.tsv` covers only the distributed release. Files generated
by these commands are expected to appear as untracked, ignored working
outputs. Their absence from the archive does not affect evaluation replay,
metric reconstruction, statistical analyses, or the lossless benchmark
splits.
