"""Build reproducible PQID-Bench planning tables.

This script intentionally uses only the Python standard library so it can run
in a minimal artifact-review environment. It does not train the later ML
baseline; it produces release-availability tables and simple readiness
baselines that are useful before scikit-learn-style experiments are available.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


PQID_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    PQID_DIR
    / "data"
    / "processed"
    / "pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl"
)
DEFAULT_OUTPUT_DIR = PQID_DIR / "data" / "processed" / "pqid_bench_tables"

LABEL_ORDER = [
    "strict_n8",
    "extended_n8",
    "validated_broad_n8",
    "validated_master_only",
    "mutation_stress_n8",
    "tier2_unvalidated",
]

BUCKET_ORDER = [
    "public_open",
    "public_open_with_obligations",
    "public_review_required",
    "restricted_internal_only",
]

CLEAN_LABELS = {"strict_n8", "extended_n8"}
REPOSITORY_CLEARED_CLEAN_LABELS = {"strict_n8", "extended_n8"}
STRESS_OR_DIAGNOSTIC_LABELS = {"mutation_stress_n8", "tier2_unvalidated"}


def iter_metadata(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            yield row.get("metadata", row)


def truth_label(metadata: dict) -> str:
    return metadata.get("benchmark_view_membership") or "<missing>"


def gate_reconstruction_label(metadata: dict) -> str:
    """Reconstruct the documented n/8 readiness view from primitive fields."""

    validated = metadata.get("validation_status") == "validated"
    high_confidence = metadata.get("extraction_confidence") == "high"
    no_demo = metadata.get("contains_demo_scaffolding") is not True
    no_cleanup = metadata.get("cleanup_candidate") is not True
    code_lines = metadata.get("code_lines") or 0
    gate_count = metadata.get("gate_count") or 0
    enough_code = code_lines >= 5
    enough_gates = gate_count >= 2
    trusted_strategy = metadata.get("retrieval_strategy") != "empirical_promoted_repo"
    mutation_suite = metadata.get("mutation_suite_candidate") is True

    benchmark_core = (
        validated
        and high_confidence
        and no_demo
        and no_cleanup
        and enough_code
        and enough_gates
    )

    if benchmark_core and not mutation_suite:
        return "strict_n8" if trusted_strategy else "extended_n8"
    if benchmark_core and mutation_suite:
        return "mutation_stress_n8"
    if validated and gate_count == 0:
        return "validated_master_only"
    if validated:
        return "validated_broad_n8"
    return "tier2_unvalidated"


def effective_release_bucket(label: str, raw_bucket: str, *, clean_n8_repository_cleared: bool) -> str:
    """Return the release bucket after documented repository-level clearance."""

    if clean_n8_repository_cleared and label in REPOSITORY_CLEARED_CLEAN_LABELS:
        return "public_open"
    return raw_bucket


def classify_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    total = len(y_true)
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    per_label = {}
    recalls = []
    f1s = []

    for label in labels:
        tp = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred == label)
        fp = sum(1 for true, pred in zip(y_true, y_pred) if true != label and pred == label)
        fn = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(1 for true in y_true if true == label),
        }
        recalls.append(recall)
        f1s.append(f1)

    stress_or_diagnostic = sum(1 for true in y_true if true in STRESS_OR_DIAGNOSTIC_LABELS)
    false_clean = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if true in STRESS_OR_DIAGNOSTIC_LABELS and pred in CLEAN_LABELS
    )

    return {
        "accuracy": correct / total if total else 0.0,
        "balanced_accuracy": sum(recalls) / len(recalls) if recalls else 0.0,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "mismatches": total - correct,
        "false_clean_rate": false_clean / stress_or_diagnostic if stress_or_diagnostic else 0.0,
        "per_label": per_label,
    }


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_outputs(
    output_dir: Path,
    input_path: Path,
    row_count: int,
    slice_release_counts: dict[str, Counter],
    raw_slice_release_counts: dict[str, Counter],
    target_counts: Counter,
    baseline_rows: list[dict],
    per_label: dict[str, dict],
    clean_n8_repository_cleared: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_readiness_and_packaging_report.md"
    json_path = output_dir / "pqid_bench_readiness_and_packaging_report.json"

    lines = [
        "# PQID-Bench Readiness And Packaging Report",
        "",
        f"- input file: `{display_path(input_path)}`",
        f"- source rows: `{row_count:,}`",
        f"- clean n/8 repository-clearance view: `{clean_n8_repository_cleared}`",
        "",
        "## Effective Slice By Release Bucket",
        "",
        "This PQID benchmark release view treats `strict_n8` and `extended_n8` as repository-cleared based on the updated repository-level license evidence. The raw source-metadata audit is preserved in the next table.",
        "",
        "| benchmark view | total | public_open | public_open_with_obligations | public_review_required | restricted_internal_only |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label in LABEL_ORDER:
        bucket_counts = slice_release_counts[label]
        total = sum(bucket_counts.values())
        values = [bucket_counts[bucket] for bucket in BUCKET_ORDER]
        lines.append(
            f"| `{label}` | {total:,} | {values[0]:,} | {values[1]:,} | {values[2]:,} | {values[3]:,} |"
        )

    lines.extend(
        [
            "",
            "## Raw Source-Metadata Release Bucket Audit",
            "",
            "These counts preserve the older row-level metadata before the repository-level clearance decision for the clean n/8 benchmark package.",
            "",
            "| benchmark view | total | public_open | public_open_with_obligations | public_review_required | restricted_internal_only |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        bucket_counts = raw_slice_release_counts[label]
        total = sum(bucket_counts.values())
        values = [bucket_counts[bucket] for bucket in BUCKET_ORDER]
        lines.append(
            f"| `{label}` | {total:,} | {values[0]:,} | {values[1]:,} | {values[2]:,} | {values[3]:,} |"
        )

    lines.extend(
        [
            "",
            "## Readiness Label Distribution",
            "",
            "| label | rows |",
            "| --- | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        lines.append(f"| `{label}` | {target_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## Dependency-Free Baselines",
            "",
            "The deterministic gate reconstruction is a sanity check for the documented readiness rules, not a learned ML baseline.",
            "",
            "| baseline | accuracy | balanced accuracy | macro-F1 | false-clean rate | mismatches |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in baseline_rows:
        metrics = row["metrics"]
        lines.append(
            f"| {row['name']} | {pct(metrics['accuracy'])} | {pct(metrics['balanced_accuracy'])} | "
            f"{pct(metrics['macro_f1'])} | {pct(metrics['false_clean_rate'])} | {metrics['mismatches']:,} |"
        )

    lines.extend(
        [
            "",
            "## Gate Reconstruction Per-Class Metrics",
            "",
            "| label | precision | recall | F1 | support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        metrics = per_label[label]
        lines.append(
            f"| `{label}` | {pct(metrics['precision'])} | {pct(metrics['recall'])} | "
            f"{pct(metrics['f1'])} | {metrics['support']:,} |"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "input_file": display_path(input_path),
        "source_rows": row_count,
        "clean_n8_repository_clearance_view": clean_n8_repository_cleared,
        "slice_by_release_bucket": {
            label: {bucket: slice_release_counts[label][bucket] for bucket in BUCKET_ORDER}
            for label in LABEL_ORDER
        },
        "raw_slice_by_release_bucket": {
            label: {bucket: raw_slice_release_counts[label][bucket] for bucket in BUCKET_ORDER}
            for label in LABEL_ORDER
        },
        "target_distribution": {label: target_counts[label] for label in LABEL_ORDER},
        "baselines": baseline_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(report_path)
    print(json_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--raw-release-buckets",
        action="store_true",
        help="Use raw public_release_bucket metadata without the clean n/8 repository-clearance view.",
    )
    args = parser.parse_args()

    y_true: list[str] = []
    y_majority: list[str] = []
    y_gate: list[str] = []
    target_counts: Counter = Counter()
    slice_release_counts: dict[str, Counter] = defaultdict(Counter)
    raw_slice_release_counts: dict[str, Counter] = defaultdict(Counter)
    clean_n8_repository_cleared = not args.raw_release_buckets

    metadata_rows = list(iter_metadata(args.input))
    for metadata in metadata_rows:
        label = truth_label(metadata)
        raw_bucket = metadata.get("public_release_bucket") or "<missing>"
        bucket = effective_release_bucket(
            label,
            raw_bucket,
            clean_n8_repository_cleared=clean_n8_repository_cleared,
        )
        y_true.append(label)
        target_counts[label] += 1
        raw_slice_release_counts[label][raw_bucket] += 1
        slice_release_counts[label][bucket] += 1
        y_gate.append(gate_reconstruction_label(metadata))

    majority_label = target_counts.most_common(1)[0][0]
    y_majority = [majority_label] * len(y_true)

    majority_metrics = classify_metrics(y_true, y_majority, LABEL_ORDER)
    gate_metrics = classify_metrics(y_true, y_gate, LABEL_ORDER)
    baseline_rows = [
        {
            "name": f"majority class (`{majority_label}`)",
            "description": "Predict the most frequent readiness label for every row.",
            "metrics": majority_metrics,
        },
        {
            "name": "deterministic n/8 gate reconstruction",
            "description": "Reconstruct readiness labels from primitive validation, extraction, size, retrieval, and mutation fields.",
            "metrics": gate_metrics,
        },
    ]

    write_outputs(
        args.output_dir,
        args.input,
        len(metadata_rows),
        slice_release_counts,
        raw_slice_release_counts,
        target_counts,
        baseline_rows,
        gate_metrics["per_label"],
        clean_n8_repository_cleared,
    )


if __name__ == "__main__":
    main()
