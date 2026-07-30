"""Run dependency-free learned readiness baselines for PQID-Bench.

The baseline in this file is intentionally modest: a categorical Naive Bayes
classifier over row-level metadata tokens. It gives the benchmark study a real
train/test result without requiring scikit-learn or network-installed
dependencies in an artifact-review environment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
PQID_DIR = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
DEFAULT_INPUT = (
    PQID_DIR
    / "data"
    / "processed"
    / "pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl"
)
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts"

LABEL_ORDER = [
    "strict_n8",
    "extended_n8",
    "validated_broad_n8",
    "validated_master_only",
    "mutation_stress_n8",
    "tier2_unvalidated",
]

CLEAN_LABELS = {"strict_n8", "extended_n8"}
STRESS_OR_DIAGNOSTIC_LABELS = {"mutation_stress_n8", "tier2_unvalidated"}

DIRECT_LABEL_FIELDS_EXCLUDED = [
    "benchmark_view_membership",
    "benchmark_suitability_tier",
    "benchmark_suitability_tier_v2",
    "expected_model_stance",
    "evidence_regime",
    "release_view_membership",
    "public_release_bucket",
    "review_trace_id",
]

PRIMITIVE_CATEGORICAL_FEATURES = [
    "validation_status",
    "extraction_confidence",
    "contains_demo_scaffolding",
    "cleanup_candidate",
    "retrieval_strategy",
    "retrieval_mode",
    "mutation_suite_candidate",
]

PRIMITIVE_NUMERIC_FEATURES = [
    "code_lines",
    "gate_count",
]

SOURCE_PROXY_CATEGORICAL_FEATURES = [
    "source",
    "language",
    "retrieval_mode",
    "qiskit_version",
    "circuit_stats_available",
    "validation_error_type",
    "openqasm3_export_successful",
    "api_deprecated_usage",
]

SOURCE_PROXY_NUMERIC_FEATURES = [
    "prompt_length_chars",
    "prompt_word_count",
    "prompt_token_count_cl100k",
    "output_token_count_cl100k",
]

BROAD_CATEGORICAL_FEATURES = PRIMITIVE_CATEGORICAL_FEATURES + [
    "circuit_stats_available",
    "context_sufficiency_class",
    "repairability_band",
    "domain_slice",
    "shift_axis",
    "source",
    "language",
    "validation_error_type",
    "openqasm3_export_successful",
    "api_deprecated_usage",
]

BROAD_NUMERIC_FEATURES = PRIMITIVE_NUMERIC_FEATURES + [
    "repairability_score",
    "prompt_length_chars",
    "prompt_word_count",
    "prompt_token_count_cl100k",
    "output_token_count_cl100k",
]

FEATURE_SETS = {
    "source_proxy_metadata": {
        "description": (
            "Gate-stripped source and proxy signals. This ablation omits the "
            "primitive n/8 readiness gates and is a better difficulty probe "
            "than the gate-reconstruction-style feature sets."
        ),
        "categorical": SOURCE_PROXY_CATEGORICAL_FEATURES,
        "numeric": SOURCE_PROXY_NUMERIC_FEATURES,
    },
    "primitive_metadata": {
        "description": (
            "Validation, extraction, size, retrieval, and mutation signals. "
            "Direct readiness labels and target aliases are omitted."
        ),
        "categorical": PRIMITIVE_CATEGORICAL_FEATURES,
        "numeric": PRIMITIVE_NUMERIC_FEATURES,
    },
    "broad_metadata": {
        "description": (
            "Primitive features plus context sufficiency, repairability, "
            "domain, shift, source, language, and validation-error signals."
        ),
        "categorical": BROAD_CATEGORICAL_FEATURES,
        "numeric": BROAD_NUMERIC_FEATURES,
    },
}


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


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def normalize_value(value: object) -> str:
    if value is None:
        return "<missing>"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text if text else "<empty>"


def numeric_bin(value: object) -> str:
    if value is None:
        return "<missing>"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "<non_numeric>"
    if math.isnan(number):
        return "<missing>"
    if number < 0:
        return "negative"
    if number == 0:
        return "0"
    if number == 1:
        return "1"
    if number == 2:
        return "2"
    if number <= 4:
        return "3_4"
    if number <= 9:
        return "5_9"
    if number <= 24:
        return "10_24"
    if number <= 49:
        return "25_49"
    if number <= 99:
        return "50_99"
    if number <= 249:
        return "100_249"
    if number <= 999:
        return "250_999"
    return "1000_plus"


def feature_tokens(row: dict, feature_set: str) -> list[str]:
    config = FEATURE_SETS[feature_set]
    tokens: list[str] = []
    for field in config["categorical"]:
        tokens.append(f"{field}={normalize_value(row.get(field))}")
    for field in config["numeric"]:
        tokens.append(f"{field}_bin={numeric_bin(row.get(field))}")
    return tokens


def load_rows(path: Path) -> list[dict]:
    selected_fields = set()
    for config in FEATURE_SETS.values():
        selected_fields.update(config["categorical"])
        selected_fields.update(config["numeric"])
    selected_fields.update({"benchmark_view_membership", "split_group_id"})

    rows = []
    for metadata in iter_metadata(path):
        label = metadata.get("benchmark_view_membership") or "<missing>"
        group_id = metadata.get("split_group_id") or metadata.get("hash") or f"row_{len(rows)}"
        row = {field: metadata.get(field) for field in selected_fields}
        row["_label"] = label
        row["_group_id"] = str(group_id)
        rows.append(row)
    return rows


def split_rows(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["_group_id"]].append(row)

    groups_by_label: dict[str, list[str]] = defaultdict(list)
    label_rank = {label: index for index, label in enumerate(LABEL_ORDER)}
    for group_id, group_rows in grouped.items():
        counts = Counter(row["_label"] for row in group_rows)
        majority_label = sorted(
            counts,
            key=lambda label: (-counts[label], label_rank.get(label, len(LABEL_ORDER)), label),
        )[0]
        groups_by_label[majority_label].append(group_id)

    split_for_group: dict[str, str] = {}
    for label, group_ids in groups_by_label.items():
        ordered = sorted(group_ids, key=lambda group_id: stable_int(f"{label}:{group_id}"))
        train_cut = int(0.8 * len(ordered))
        validation_cut = int(0.9 * len(ordered))
        for index, group_id in enumerate(ordered):
            if index < train_cut:
                split = "train"
            elif index < validation_cut:
                split = "validation"
            else:
                split = "test"
            split_for_group[group_id] = split

    splits = {"train": [], "validation": [], "test": []}
    for row in rows:
        splits[split_for_group[row["_group_id"]]].append(row)
    return splits


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
        support = sum(1 for true in y_true if true == label)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        recalls.append(recall)
        f1s.append(f1)

    stress_or_diagnostic = sum(1 for true in y_true if true in STRESS_OR_DIAGNOSTIC_LABELS)
    false_clean = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if true in STRESS_OR_DIAGNOSTIC_LABELS and pred in CLEAN_LABELS
    )
    confusion = {
        true: {pred: 0 for pred in labels}
        for true in labels
    }
    for true, pred in zip(y_true, y_pred):
        if true in confusion and pred in confusion[true]:
            confusion[true][pred] += 1

    return {
        "accuracy": correct / total if total else 0.0,
        "balanced_accuracy": sum(recalls) / len(recalls) if recalls else 0.0,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "mismatches": total - correct,
        "false_clean_rate": false_clean / stress_or_diagnostic if stress_or_diagnostic else 0.0,
        "per_label": per_label,
        "confusion": confusion,
    }


class CategoricalNaiveBayes:
    def __init__(self, labels: list[str], alpha: float = 1.0, balanced_prior: bool = False) -> None:
        self.labels = labels
        self.alpha = alpha
        self.balanced_prior = balanced_prior
        self.class_counts: Counter = Counter()
        self.token_counts: dict[str, Counter] = {label: Counter() for label in labels}
        self.total_tokens: Counter = Counter()
        self.vocabulary: set[str] = set()

    def fit(self, rows: list[dict], feature_set: str) -> None:
        for row in rows:
            label = row["_label"]
            if label not in self.token_counts:
                continue
            tokens = feature_tokens(row, feature_set)
            self.class_counts[label] += 1
            self.token_counts[label].update(tokens)
            self.total_tokens[label] += len(tokens)
            self.vocabulary.update(tokens)

    def predict_one(self, row: dict, feature_set: str) -> str:
        tokens = feature_tokens(row, feature_set)
        total_rows = sum(self.class_counts.values())
        vocab_size = max(len(self.vocabulary), 1)
        best_label = self.labels[0]
        best_score = -math.inf
        for label in self.labels:
            if self.balanced_prior:
                prior = 1.0 / len(self.labels)
            else:
                prior = self.class_counts[label] / total_rows if total_rows else 0.0
            score = math.log(prior if prior > 0 else 1e-12)
            denominator = self.total_tokens[label] + self.alpha * vocab_size
            for token in tokens:
                numerator = self.token_counts[label][token] + self.alpha
                score += math.log(numerator / denominator)
            if score > best_score:
                best_label = label
                best_score = score
        return best_label

    def predict(self, rows: list[dict], feature_set: str) -> list[str]:
        return [self.predict_one(row, feature_set) for row in rows]


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def split_summary(splits: dict[str, list[dict]]) -> dict[str, dict]:
    summary = {}
    for split, rows in splits.items():
        groups = {row["_group_id"] for row in rows}
        labels = Counter(row["_label"] for row in rows)
        summary[split] = {
            "rows": len(rows),
            "groups": len(groups),
            "labels": {label: labels[label] for label in LABEL_ORDER},
        }
    return summary


def run_baselines(rows: list[dict], alpha: float) -> tuple[dict[str, list[dict]], list[dict]]:
    splits = split_rows(rows)
    train_rows = splits["train"]
    test_rows = splits["test"]
    y_test = [row["_label"] for row in test_rows]
    train_majority = Counter(row["_label"] for row in train_rows).most_common(1)[0][0]

    results = [
        {
            "name": f"majority class (`{train_majority}`)",
            "model": "majority",
            "feature_set": "none",
            "description": "Predict the most frequent train label for every test row.",
            "metrics": classify_metrics(y_test, [train_majority] * len(test_rows), LABEL_ORDER),
        }
    ]

    for feature_set in FEATURE_SETS:
        for balanced_prior in (False, True):
            model = CategoricalNaiveBayes(
                LABEL_ORDER,
                alpha=alpha,
                balanced_prior=balanced_prior,
            )
            model.fit(train_rows, feature_set)
            y_pred = model.predict(test_rows, feature_set)
            prior_name = "uniform priors" if balanced_prior else "empirical priors"
            results.append(
                {
                    "name": f"categorical Naive Bayes ({feature_set}, {prior_name})",
                    "model": "categorical_naive_bayes",
                    "feature_set": feature_set,
                    "description": FEATURE_SETS[feature_set]["description"],
                    "balanced_prior": balanced_prior,
                    "alpha": alpha,
                    "metrics": classify_metrics(y_test, y_pred, LABEL_ORDER),
                }
            )
    return splits, results


def write_outputs(
    output_dir: Path,
    input_path: Path,
    rows: list[dict],
    splits: dict[str, list[dict]],
    results: list[dict],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "pqid_bench_readiness_learned_baseline_report.md"
    json_path = output_dir / "pqid_bench_readiness_learned_baseline_report.json"

    learned_results = [row for row in results if row["model"] != "majority"]
    best = sorted(
        learned_results,
        key=lambda row: (
            -row["metrics"]["macro_f1"],
            -row["metrics"]["balanced_accuracy"],
            row["metrics"]["false_clean_rate"],
            row["name"],
        ),
    )[0]
    source_proxy_empirical = next(
        row
        for row in results
        if row["name"] == "categorical Naive Bayes (source_proxy_metadata, empirical priors)"
    )

    split_stats = split_summary(splits)
    train_groups = {row["_group_id"] for row in splits["train"]}
    validation_groups = {row["_group_id"] for row in splits["validation"]}
    test_groups = {row["_group_id"] for row in splits["test"]}
    group_overlap = {
        "train_validation": len(train_groups & validation_groups),
        "train_test": len(train_groups & test_groups),
        "validation_test": len(validation_groups & test_groups),
    }

    lines = [
        "# PQID-Bench Learned Readiness Baseline Report",
        "",
        f"- input file: `{display_path(input_path)}`",
        f"- source rows: `{len(rows):,}`",
        "- split policy: deterministic stratified group split by `split_group_id`",
        f"- group overlap: train/validation `{group_overlap['train_validation']}`, "
        f"train/test `{group_overlap['train_test']}`, "
        f"validation/test `{group_overlap['validation_test']}`",
        "",
        "## Direct Fields Excluded",
        "",
        ", ".join(f"`{field}`" for field in DIRECT_LABEL_FIELDS_EXCLUDED),
        "",
        "## Feature Sets",
        "",
        "| feature set | categorical fields | numeric fields |",
        "| --- | --- | --- |",
    ]
    for name, config in FEATURE_SETS.items():
        categorical = ", ".join(f"`{field}`" for field in config["categorical"])
        numeric = ", ".join(f"`{field}`" for field in config["numeric"])
        lines.append(f"| `{name}` | {categorical} | {numeric} |")

    lines.extend(
        [
            "",
            "## Split Summary",
            "",
            "| split | rows | groups | strict_n8 | extended_n8 | validated_broad_n8 | validated_master_only | mutation_stress_n8 | tier2_unvalidated |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for split in ("train", "validation", "test"):
        stats = split_stats[split]
        labels = stats["labels"]
        lines.append(
            f"| {split} | {stats['rows']:,} | {stats['groups']:,} | "
            f"{labels['strict_n8']:,} | {labels['extended_n8']:,} | "
            f"{labels['validated_broad_n8']:,} | {labels['validated_master_only']:,} | "
            f"{labels['mutation_stress_n8']:,} | {labels['tier2_unvalidated']:,} |"
        )

    lines.extend(
        [
            "",
            "## Test Results",
            "",
            "| baseline | accuracy | balanced accuracy | macro-F1 | false-clean rate | mismatches |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        metrics = result["metrics"]
        lines.append(
            f"| {result['name']} | {pct(metrics['accuracy'])} | "
            f"{pct(metrics['balanced_accuracy'])} | {pct(metrics['macro_f1'])} | "
            f"{pct(metrics['false_clean_rate'])} | {metrics['mismatches']:,} |"
        )

    lines.extend(
        [
            "",
            "## Source-Proxy Empirical Priors Per-Class Metrics",
            "",
            "| label | precision | recall | F1 | support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        metrics = source_proxy_empirical["metrics"]["per_label"][label]
        lines.append(
            f"| `{label}` | {pct(metrics['precision'])} | {pct(metrics['recall'])} | "
            f"{pct(metrics['f1'])} | {metrics['support']:,} |"
        )

    lines.extend(
        [
            "",
            f"Best learned model by macro-F1: **{best['name']}**.",
            "",
            "## Best Learned Model Per-Class Metrics",
            "",
            "| label | precision | recall | F1 | support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        metrics = best["metrics"]["per_label"][label]
        lines.append(
            f"| `{label}` | {pct(metrics['precision'])} | {pct(metrics['recall'])} | "
            f"{pct(metrics['f1'])} | {metrics['support']:,} |"
        )

    lines.extend(
        [
            "",
            "## Best Learned Model Confusion Matrix",
            "",
            "| true label | strict_n8 | extended_n8 | validated_broad_n8 | validated_master_only | mutation_stress_n8 | tier2_unvalidated |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    confusion = best["metrics"]["confusion"]
    for true_label in LABEL_ORDER:
        row = confusion[true_label]
        lines.append(
            f"| `{true_label}` | {row['strict_n8']:,} | {row['extended_n8']:,} | "
            f"{row['validated_broad_n8']:,} | {row['validated_master_only']:,} | "
            f"{row['mutation_stress_n8']:,} | {row['tier2_unvalidated']:,} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "input_file": display_path(input_path),
        "source_rows": len(rows),
        "split_policy": "deterministic stratified group split by split_group_id",
        "group_overlap": group_overlap,
        "direct_fields_excluded": DIRECT_LABEL_FIELDS_EXCLUDED,
        "feature_sets": FEATURE_SETS,
        "split_summary": split_stats,
        "results": results,
        "best_learned_model": best["name"],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(md_path)
    print(json_path)
    print(best["name"])
    print(
        f"macro-F1={pct(best['metrics']['macro_f1'])}; "
        f"balanced_accuracy={pct(best['metrics']['balanced_accuracy'])}; "
        f"false_clean_rate={pct(best['metrics']['false_clean_rate'])}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--alpha", type=float, default=1.0)
    args = parser.parse_args()

    rows = load_rows(args.input)
    splits, results = run_baselines(rows, alpha=args.alpha)
    write_outputs(args.output_dir, args.input, rows, splits, results)


if __name__ == "__main__":
    main()
