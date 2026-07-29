# Frozen PQID-Bench Evaluator Splits

These files are a lossless materialization of the deterministic split stored
in `../../artifacts/test_split_154/pqid_bench_split_154_manifest.json`:

| file | rows |
| --- | ---: |
| `train.jsonl` | 514 |
| `validation.jsonl` | 66 |
| `test.jsonl` | 154 |

Every line is copied byte-for-byte, apart from normalized LF line endings,
from `../pqid_bench_evaluator_source_734.jsonl`. The manifest's `row_id`
matches `metadata.content_hash` in the evaluator record. Their union contains
all 734 evaluator records exactly once, and their pairwise intersections are
empty.

The archived parent PQID dataset is not required to load or use these splits.
It is needed only to reconstruct the upstream benchmark-construction process.

With Hugging Face Datasets:

```python
from datasets import load_dataset

splits = load_dataset(
    "json",
    data_files={
        "train": "data/splits/train.jsonl",
        "validation": "data/splits/validation.jsonl",
        "test": "data/splits/test.jsonl",
    },
)
```
