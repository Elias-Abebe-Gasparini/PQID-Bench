"""Materialize the frozen PQID-Bench train, validation, and test views."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_COUNTS = {"train": 514, "validation": 66, "test": 154}
SPLIT_FILENAMES = {
    "train": "train.jsonl",
    "validation": "validation.jsonl",
    "test": "test.jsonl",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(path: Path) -> tuple[list[str], dict[str, str]]:
    lines: list[str] = []
    line_by_id: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            metadata = row.get("metadata")
            if not isinstance(metadata, dict):
                raise ValueError(f"Missing metadata at {path}:{line_number}")
            row_id = str(metadata.get("content_hash") or "")
            if not row_id:
                raise ValueError(f"Missing metadata.content_hash at {path}:{line_number}")
            if row_id in line_by_id:
                raise ValueError(f"Duplicate evaluator-source ID: {row_id}")
            normalized = line.rstrip("\r\n") + "\n"
            lines.append(row_id)
            line_by_id[row_id] = normalized
    return lines, line_by_id


def load_assignments(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assignments = payload.get("assignments")
    if not isinstance(assignments, list):
        raise ValueError(f"Split manifest has no assignments array: {path}")

    split_by_id: dict[str, str] = {}
    for index, assignment in enumerate(assignments):
        if not isinstance(assignment, dict):
            raise ValueError(f"Invalid split assignment at index {index}")
        row_id = str(assignment.get("row_id") or "")
        split = str(assignment.get("split") or "")
        if split not in EXPECTED_COUNTS:
            raise ValueError(f"Unexpected split {split!r} for row {row_id!r}")
        if not row_id:
            raise ValueError(f"Missing row_id in assignment {index}")
        if row_id in split_by_id:
            raise ValueError(f"Duplicate split assignment for row {row_id}")
        split_by_id[row_id] = split
    return split_by_id


def expected_split_payloads(
    source_order: list[str],
    line_by_id: dict[str, str],
    split_by_id: dict[str, str],
) -> dict[str, str]:
    source_ids = set(line_by_id)
    assignment_ids = set(split_by_id)
    if source_ids != assignment_ids:
        missing = sorted(assignment_ids - source_ids)
        unassigned = sorted(source_ids - assignment_ids)
        raise ValueError(
            "Evaluator source and split manifest IDs differ: "
            f"missing_from_source={len(missing)}, unassigned_source={len(unassigned)}"
        )

    lines_by_split: dict[str, list[str]] = {
        split: [] for split in EXPECTED_COUNTS
    }
    for row_id in source_order:
        lines_by_split[split_by_id[row_id]].append(line_by_id[row_id])

    observed = Counter(
        split_by_id[row_id]
        for row_id in source_order
    )
    if dict(observed) != EXPECTED_COUNTS:
        raise ValueError(
            f"Unexpected split counts: {dict(observed)}; expected {EXPECTED_COUNTS}"
        )
    return {
        split: "".join(lines_by_split[split])
        for split in EXPECTED_COUNTS
    }


def split_readme() -> str:
    return """# Frozen PQID-Bench Evaluator Splits

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
"""


def materialize_splits(
    source_path: Path,
    manifest_path: Path,
    output_dir: Path,
    *,
    check_only: bool = False,
) -> dict[str, dict[str, Any]]:
    source_order, line_by_id = load_source(source_path)
    split_by_id = load_assignments(manifest_path)
    payloads = expected_split_payloads(source_order, line_by_id, split_by_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not check_only:
        for split, payload in payloads.items():
            destination = output_dir / SPLIT_FILENAMES[split]
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_text(
                payload,
                encoding="utf-8",
                newline="\n",
            )
            temporary.replace(destination)
        (output_dir / "README.md").write_text(
            split_readme(),
            encoding="utf-8",
            newline="\n",
        )

    results: dict[str, dict[str, Any]] = {}
    for split, expected_payload in payloads.items():
        path = output_dir / SPLIT_FILENAMES[split]
        if not path.is_file():
            raise FileNotFoundError(path)
        observed_payload = path.read_text(encoding="utf-8")
        if observed_payload != expected_payload:
            raise ValueError(f"Materialized {split} split differs from its frozen source")
        results[split] = {
            "path": path,
            "rows": expected_payload.count("\n"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    readme = output_dir / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(readme)
    return results


def default_release_root() -> Path:
    script_root = Path(__file__).resolve().parents[1]
    if (script_root / ".zenodo.json").is_file():
        return script_root
    return script_root / "PQID-Bench"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-root", type=Path, default=default_release_root())
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing split files without rewriting them.",
    )
    args = parser.parse_args()

    root = args.release_root.resolve()
    results = materialize_splits(
        root / "data" / "pqid_bench_evaluator_source_734.jsonl",
        root
        / "artifacts"
        / "test_split_154"
        / "pqid_bench_split_154_manifest.json",
        root / "data" / "splits",
        check_only=args.check,
    )
    mode = "Verified" if args.check else "Materialized"
    print(f"{mode} frozen evaluator splits under {root / 'data' / 'splits'}")
    for split in ("train", "validation", "test"):
        result = results[split]
        print(
            f"{split}: rows={result['rows']}, bytes={result['bytes']}, "
            f"sha256={result['sha256']}"
        )


if __name__ == "__main__":
    main()
