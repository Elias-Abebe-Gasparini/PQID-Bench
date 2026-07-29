# PQID-Bench Clean Generation View

`pqid_bench_clean_generation_734.jsonl` contains the frozen clean generation
population used to construct PQID-Bench:

- `415` `strict_n8` rows;
- `319` `extended_n8` rows;
- `734` rows in total.

`pqid_bench_evaluator_source_734.jsonl` contains the corresponding seeded
prompt/code records used by the frozen split and executable evaluator. It
contains `415` `gold_generation` and `319` `broad_generation` records. The two
files are deliberately separate: the first preserves the governance view,
while the second preserves the exact evaluator input contract.

`splits/train.jsonl`, `splits/validation.jsonl`, and `splits/test.jsonl`
materialize the complete evaluator source as a lossless `514/66/154`
partition. They are generated from the frozen assignment manifest by matching
its `row_id` to each evaluator record's `metadata.content_hash`. The three
files contain every evaluator record exactly once.

Historical row-level release fields are retained for audit. The added
`pqid_bench_effective_release_bucket` and
`pqid_bench_release_clearance_basis` fields record the repository-level
clearance decision used by the benchmark package. The deterministic
train/validation/test assignment remains authoritative under
`artifacts/test_split_154/`; the separate JSONL files are convenience views.
No parent PQID download is required to use the frozen benchmark or its splits.
The source PQID v1.0.2 dataset remains a separately versioned object with DOI
`10.5281/zenodo.20674853`.
