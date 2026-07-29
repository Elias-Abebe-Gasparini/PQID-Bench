"""Consolidate the original and augmentation repeatability halves into 21x72."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from build_pqid_bench_stochastic_repeatability_panel import (
    BIN_ORDER,
    COHORT_ORDER,
    cohort,
    display_path,
    gate_type_bin,
    has_barrier,
    iter_jsonl,
    prompt_number,
    reference_signature,
    sha256_file,
    stable_json,
    write_json,
    write_jsonl,
)
from prepare_pqid_bench_stochastic_repeatability_runs import MODEL_SPECS


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL_ROOT = (
    SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x36"
)
DEFAULT_EXPANDED_ROOT = (
    SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x72"
)
DEFAULT_AUGMENTATION_ROOT = DEFAULT_EXPANDED_ROOT / "augmentation_runs"
DEFAULT_OUTPUT_ROOT = DEFAULT_EXPANDED_ROOT / "consolidated"
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"


def canonical_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows = iter_jsonl(path)
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        prompt_id = str(row.get("prompt_id") or "")
        if not prompt_id:
            raise ValueError(f"Missing prompt_id in {path}")
        if prompt_id in mapped:
            raise ValueError(f"Duplicate prompt_id {prompt_id} in {path}")
        mapped[prompt_id] = row
    return mapped


def merged_rows(first: Path, second: Path, expected_ids: set[str]) -> list[dict[str, Any]]:
    first_rows = canonical_rows(first)
    second_rows = canonical_rows(second)
    overlap = set(first_rows).intersection(second_rows)
    if overlap:
        raise ValueError(f"Panel halves overlap in {first.name}: {sorted(overlap)[:5]}")
    combined = {**first_rows, **second_rows}
    if set(combined) != expected_ids:
        missing = sorted(expected_ids - set(combined))
        extra = sorted(set(combined) - expected_ids)
        raise ValueError(
            f"Combined rows in {first.name} do not match the 72-prompt panel; "
            f"missing={missing[:5]}, extra={extra[:5]}"
        )
    return sorted(combined.values(), key=lambda row: prompt_number(str(row["prompt_id"])))


def concatenate_optional_jsonl(first: Path, second: Path, output: Path) -> None:
    rows: list[str] = []
    for path in (first, second):
        if path.exists():
            rows.extend(line for line in path.read_text(encoding="utf-8").splitlines() if line)
    if not rows:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_panel_manifest(
    original_root: Path,
    expanded_root: Path,
    output_root: Path,
) -> tuple[Path, dict[str, Any]]:
    original_manifest_path = (
        original_root / "panel" / "pqid_bench_stochastic_repeatability_panel.json"
    )
    augmentation_manifest_path = (
        expanded_root
        / "panel"
        / "pqid_bench_stochastic_repeatability_augmentation_manifest.json"
    )
    original_manifest = json.loads(original_manifest_path.read_text(encoding="utf-8"))
    augmentation_manifest = json.loads(
        augmentation_manifest_path.read_text(encoding="utf-8")
    )
    source_combined_path = (
        expanded_root / "panel" / "pqid_bench_stochastic_repeatability_prompts_72.jsonl"
    )
    panel_rows = iter_jsonl(source_combined_path)
    if len(panel_rows) != 72:
        raise ValueError("The combined source panel does not contain 72 rows")

    records = [
        *original_manifest["selected_prompts"],
        *augmentation_manifest["selected_prompts"],
    ]
    records.sort(key=lambda row: prompt_number(str(row["prompt_id"])))
    prompt_ids = [str(row["prompt_id"]) for row in records]
    signature_keys = [stable_json(row["reference_signature"]) for row in records]
    if len(set(prompt_ids)) != 72 or len(set(signature_keys)) != 72:
        raise ValueError("Combined manifest records are not prompt- and signature-unique")

    panel_dir = output_root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    panel_path = panel_dir / "pqid_bench_stochastic_repeatability_prompts_72.jsonl"
    write_jsonl(panel_path, panel_rows)

    bin_counts = Counter(gate_type_bin(row) for row in panel_rows)
    cohort_counts = Counter(cohort(row) for row in panel_rows)
    manifest = {
        "schema_version": "pqid-bench-stochastic-repeatability-panel-v2",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "selection_seed": augmentation_manifest["selection_seed"],
        "selection_seed_derivation": augmentation_manifest["selection_seed_derivation"],
        "selection_is_outcome_blind": True,
        "selection_is_sequential_augmentation": True,
        "source_original_manifest": display_path(original_manifest_path),
        "source_original_manifest_sha256": sha256_file(original_manifest_path),
        "source_augmentation_manifest": display_path(augmentation_manifest_path),
        "source_augmentation_manifest_sha256": sha256_file(augmentation_manifest_path),
        "prompt_count": 72,
        "unique_signature_count": 72,
        "panel_file": display_path(panel_path),
        "panel_sha256": sha256_file(panel_path),
        "balance": {
            "gate_type_bins": dict(
                sorted(bin_counts.items(), key=lambda item: BIN_ORDER[item[0]])
            ),
            "cohorts": dict(
                sorted(cohort_counts.items(), key=lambda item: COHORT_ORDER[item[0]])
            ),
            "barrier": sum(has_barrier(row) for row in panel_rows),
            "no_barrier": sum(not has_barrier(row) for row in panel_rows),
        },
        "selected_prompts": records,
    }
    manifest_path = panel_dir / "pqid_bench_stochastic_repeatability_panel.json"
    write_json(manifest_path, manifest)
    return panel_path, manifest


def consolidate(
    original_root: Path,
    augmentation_root: Path,
    expanded_root: Path,
    output_root: Path,
) -> None:
    panel_path, panel_manifest = make_panel_manifest(
        original_root,
        expanded_root,
        output_root,
    )
    expected_ids = {
        str(row["prompt_id"]) for row in panel_manifest["selected_prompts"]
    }

    protocol_source = expanded_root / "PRESPECIFIED_AUGMENTATION_PROTOCOL.md"
    amendments_source = original_root / "PROTOCOL_AMENDMENTS.md"
    shutil.copyfile(protocol_source, output_root / "PRESPECIFIED_PROTOCOL.md")
    shutil.copyfile(amendments_source, output_root / "PROTOCOL_AMENDMENTS.md")

    file_records: list[dict[str, Any]] = []
    for run_number in (1, 2, 3):
        for spec in MODEL_SPECS:
            slug = spec.slug
            original_run = original_root / f"run_{run_number}"
            augmentation_run = augmentation_root / f"run_{run_number}"
            output_run = output_root / f"run_{run_number}"

            pairs = (
                (
                    original_run / "requests" / f"{slug}_requests.jsonl",
                    augmentation_run / "requests" / f"{slug}_requests.jsonl",
                    output_run / "requests" / f"{slug}_requests.jsonl",
                ),
                (
                    original_run / "responses" / f"{slug}_responses_template.jsonl",
                    augmentation_run / "responses" / f"{slug}_responses_template.jsonl",
                    output_run / "responses" / f"{slug}_responses_template.jsonl",
                ),
                (
                    original_run / "responses" / f"{slug}_responses.jsonl",
                    augmentation_run / "responses" / f"{slug}_responses.jsonl",
                    output_run / "responses" / f"{slug}_responses.jsonl",
                ),
            )
            for original_path, augmentation_path, output_path in pairs:
                rows = merged_rows(original_path, augmentation_path, expected_ids)
                write_jsonl(output_path, rows)
                file_records.append(
                    {
                        "run": run_number,
                        "model": spec.model,
                        "kind": output_path.parent.name,
                        "path": display_path(output_path),
                        "rows": len(rows),
                        "sha256": sha256_file(output_path),
                    }
                )

            concatenate_optional_jsonl(
                original_run / "raw_outputs" / f"{slug}_raw.jsonl",
                augmentation_run / "raw_outputs" / f"{slug}_raw.jsonl",
                output_run / "raw_outputs" / f"{slug}_raw.jsonl",
            )

    consolidation_manifest = {
        "schema_version": "pqid-bench-stochastic-repeatability-consolidation-v1",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "original_root": display_path(original_root),
        "augmentation_root": display_path(augmentation_root),
        "output_root": display_path(output_root),
        "panel_file": display_path(panel_path),
        "panel_sha256": panel_manifest["panel_sha256"],
        "models": len(MODEL_SPECS),
        "prompts": 72,
        "runs": 3,
        "expected_scored_cells": len(MODEL_SPECS) * 72 * 3,
        "files": file_records,
    }
    manifest_path = output_root / "pqid_bench_stochastic_repeatability_consolidation_manifest.json"
    write_json(manifest_path, consolidation_manifest)
    print(f"Wrote {display_path(manifest_path)}")
    print(f"Consolidated {len(MODEL_SPECS)} models x 72 prompts x 3 runs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-root", type=Path, default=DEFAULT_ORIGINAL_ROOT)
    parser.add_argument("--augmentation-root", type=Path, default=DEFAULT_AUGMENTATION_ROOT)
    parser.add_argument("--expanded-root", type=Path, default=DEFAULT_EXPANDED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    consolidate(
        args.original_root,
        args.augmentation_root,
        args.expanded_root,
        args.output_root,
    )


if __name__ == "__main__":
    main()
