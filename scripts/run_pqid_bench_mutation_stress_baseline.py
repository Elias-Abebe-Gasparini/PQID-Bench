"""Run dependency-free mutation-stress detection baselines for PQID-Bench.

This script evaluates whether mutation-derived stress examples can be separated
from clean generation controls. The direct mutation flag is reported only as an
audit sanity check. The learned baselines exclude direct target aliases and use
metadata/code-token features.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
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

CLEAN_LABELS = {"strict_n8", "extended_n8"}
TARGET_LABELS = {"clean_control", "mutation_stress"}
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?")

DIRECT_ALIAS_FIELDS = [
    "benchmark_view_membership",
    "benchmark_suitability_tier",
    "benchmark_suitability_tier_v2",
    "expected_model_stance",
    "evidence_regime",
    "mutation_suite_candidate",
    "release_view_membership",
    "public_release_bucket",
    "review_trace_id",
]

SOURCE_PROXY_CATEGORICAL = [
    "source",
    "retrieval_strategy",
    "retrieval_mode",
    "language",
    "qiskit_version",
    "source_snapshot_granularity",
]

STRUCTURAL_CATEGORICAL = [
    "validation_status",
    "extraction_confidence",
    "materialized_circuit",
    "openqasm3_export_successful",
    "api_deprecated_usage",
    "contains_demo_scaffolding",
    "cleanup_candidate",
    "circuit_stats_available",
    "has_measurement",
    "has_entangling_gates",
    "has_rotation_gates",
    "has_clifford_only",
    "has_barriers",
    "is_parameterized",
    "size_class",
    "benchmark_difficulty",
    "circuit_expressiveness",
]

STRUCTURAL_NUMERIC = [
    "code_lines",
    "gate_count",
    "num_qubits",
    "num_clbits",
    "circuit_depth",
    "circuit_width",
    "num_gate_types",
    "two_qubit_gate_count",
    "measurement_count",
    "output_token_count_cl100k",
]

FEATURE_SETS = {
    "source_proxy_metadata": {
        "description": "source and retrieval metadata, excluding direct mutation and release aliases",
        "categorical": SOURCE_PROXY_CATEGORICAL,
        "numeric": [],
        "include_code_tokens": False,
        "include_gate_tokens": False,
    },
    "structural_metadata": {
        "description": "validated circuit-structure metadata, excluding direct mutation aliases",
        "categorical": STRUCTURAL_CATEGORICAL,
        "numeric": STRUCTURAL_NUMERIC,
        "include_code_tokens": False,
        "include_gate_tokens": True,
    },
    "code_tokens": {
        "description": "code lexical tokens only",
        "categorical": [],
        "numeric": [],
        "include_code_tokens": True,
        "include_gate_tokens": False,
    },
    "structure_plus_code": {
        "description": "structural metadata plus code lexical tokens",
        "categorical": STRUCTURAL_CATEGORICAL,
        "numeric": STRUCTURAL_NUMERIC,
        "include_code_tokens": True,
        "include_gate_tokens": True,
    },
}


def iter_rows(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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


def tokenize_code(text: object) -> list[str]:
    if text is None:
        return []
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(str(text)):
        token = raw.lower()
        if len(token) == 1 and token not in {"h", "x", "y", "z", "s", "t"}:
            continue
        tokens.append(token)
    return tokens[:400]


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for index, raw in enumerate(iter_rows(path)):
        metadata = raw.get("metadata", raw)
        benchmark_label = metadata.get("benchmark_view_membership")
        if benchmark_label == "mutation_stress_n8":
            target = "mutation_stress"
        elif benchmark_label in CLEAN_LABELS:
            target = "clean_control"
        else:
            continue

        group_id = metadata.get("split_group_id") or metadata.get("hash") or f"row_{index}"
        rows.append(
            {
                "_target": target,
                "_benchmark_label": benchmark_label,
                "_group_id": str(group_id),
                "_row_id": metadata.get("hash") or f"row_{index}",
                "_code": raw.get("output") or "",
                "_metadata": metadata,
            }
        )
    return rows


def split_rows(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["_group_id"]].append(row)

    groups_by_target: dict[str, list[str]] = defaultdict(list)
    for group_id, group_rows in grouped.items():
        counts = Counter(row["_target"] for row in group_rows)
        majority = sorted(counts, key=lambda label: (-counts[label], label))[0]
        groups_by_target[majority].append(group_id)

    split_for_group: dict[str, str] = {}
    for target, group_ids in groups_by_target.items():
        ordered = sorted(group_ids, key=lambda group_id: stable_int(f"{target}:{group_id}"))
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


def feature_tokens(row: dict, feature_set: str) -> list[str]:
    config = FEATURE_SETS[feature_set]
    metadata = row["_metadata"]
    tokens: list[str] = []

    for field in config["categorical"]:
        tokens.append(f"{field}={normalize_value(metadata.get(field))}")
    for field in config["numeric"]:
        tokens.append(f"{field}_bin={numeric_bin(metadata.get(field))}")
    if config["include_gate_tokens"]:
        gate_types = metadata.get("gate_types")
        if isinstance(gate_types, dict):
            for gate, count in sorted(gate_types.items()):
                repeat_count = min(int(count or 1), 5)
                tokens.extend([f"gate={gate}"] * repeat_count)
    if config["include_code_tokens"]:
        tokens.extend(f"code={token}" for token in tokenize_code(row["_code"]))

    return tokens


class NaiveBayes:
    def __init__(self, alpha: float = 1.0, uniform_priors: bool = False) -> None:
        self.alpha = alpha
        self.uniform_priors = uniform_priors
        self.labels = ["clean_control", "mutation_stress"]
        self.class_counts: Counter = Counter()
        self.token_counts: dict[str, Counter] = {label: Counter() for label in self.labels}
        self.total_tokens: Counter = Counter()
        self.vocabulary: set[str] = set()

    def fit(self, rows: list[dict], feature_set: str) -> None:
        for row in rows:
            label = row["_target"]
            self.class_counts[label] += 1
            tokens = feature_tokens(row, feature_set)
            self.token_counts[label].update(tokens)
            self.total_tokens[label] += len(tokens)
            self.vocabulary.update(tokens)

    def score_label(self, tokens: list[str], label: str) -> float:
        total_docs = sum(self.class_counts.values())
        if self.uniform_priors:
            score = -math.log(len(self.labels))
        else:
            score = math.log((self.class_counts[label] + self.alpha) / (total_docs + self.alpha * len(self.labels)))

        denominator = self.total_tokens[label] + self.alpha * max(len(self.vocabulary), 1)
        unknown_log_prob = math.log(self.alpha / denominator)
        counts = Counter(tokens)
        for token, count in counts.items():
            if token not in self.vocabulary:
                log_prob = unknown_log_prob
            else:
                log_prob = math.log((self.token_counts[label][token] + self.alpha) / denominator)
            score += count * log_prob
        return score

    def predict_one(self, row: dict, feature_set: str) -> tuple[str, float]:
        tokens = feature_tokens(row, feature_set)
        clean_score = self.score_label(tokens, "clean_control")
        stress_score = self.score_label(tokens, "mutation_stress")
        pred = "mutation_stress" if stress_score >= clean_score else "clean_control"
        return pred, stress_score - clean_score


def direct_flag_predict(row: dict) -> tuple[str, float]:
    value = row["_metadata"].get("mutation_suite_candidate")
    pred = "mutation_stress" if value is True else "clean_control"
    score = 1.0 if value is True else -1.0
    return pred, score


def evaluate_predictions(rows: list[dict], predictions: list[str], scores: list[float]) -> dict:
    y_true = [row["_target"] for row in rows]
    labels = ["clean_control", "mutation_stress"]
    total = len(rows)
    correct = sum(1 for true, pred in zip(y_true, predictions) if true == pred)
    per_label = {}
    f1s = []
    recalls = []

    for label in labels:
        tp = sum(1 for true, pred in zip(y_true, predictions) if true == label and pred == label)
        fp = sum(1 for true, pred in zip(y_true, predictions) if true != label and pred == label)
        fn = sum(1 for true, pred in zip(y_true, predictions) if true == label and pred != label)
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

    clean_rows = sum(1 for true in y_true if true == "clean_control")
    stress_rows = sum(1 for true in y_true if true == "mutation_stress")
    false_clean = sum(
        1
        for true, pred in zip(y_true, predictions)
        if true == "mutation_stress" and pred == "clean_control"
    )
    false_stress = sum(
        1
        for true, pred in zip(y_true, predictions)
        if true == "clean_control" and pred == "mutation_stress"
    )

    return {
        "accuracy": correct / total if total else 0.0,
        "balanced_accuracy": sum(recalls) / len(recalls) if recalls else 0.0,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "auroc": auroc(y_true, scores),
        "false_clean_rate": false_clean / stress_rows if stress_rows else 0.0,
        "false_stress_rate": false_stress / clean_rows if clean_rows else 0.0,
        "mismatches": total - correct,
        "per_label": per_label,
        "clean_slice_false_stress": clean_slice_false_stress(rows, predictions),
    }


def clean_slice_false_stress(rows: list[dict], predictions: list[str]) -> dict:
    by_slice: dict[str, Counter] = defaultdict(Counter)
    for row, pred in zip(rows, predictions):
        label = row["_benchmark_label"]
        if label not in CLEAN_LABELS:
            continue
        by_slice[label]["total"] += 1
        if pred == "mutation_stress":
            by_slice[label]["false_stress"] += 1
    return {
        label: {
            "support": counts["total"],
            "false_stress": counts["false_stress"],
            "false_stress_rate": counts["false_stress"] / counts["total"] if counts["total"] else 0.0,
        }
        for label, counts in by_slice.items()
    }


def auroc(y_true: list[str], scores: list[float]) -> float:
    positives = [(score, 1) for true, score in zip(y_true, scores) if true == "mutation_stress"]
    negatives = [(score, 0) for true, score in zip(y_true, scores) if true == "clean_control"]
    if not positives or not negatives:
        return 0.0

    wins = 0.0
    total = len(positives) * len(negatives)
    negative_scores = [score for score, _flag in negatives]
    for pos_score, _flag in positives:
        for neg_score in negative_scores:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / total


def run_model(train_rows: list[dict], test_rows: list[dict], feature_set: str, uniform_priors: bool) -> dict:
    model = NaiveBayes(uniform_priors=uniform_priors)
    model.fit(train_rows, feature_set)
    predictions = []
    scores = []
    for row in test_rows:
        pred, score = model.predict_one(row, feature_set)
        predictions.append(pred)
        scores.append(score)
    return evaluate_predictions(test_rows, predictions, scores)


def evaluate_direct_flag(test_rows: list[dict]) -> dict:
    predictions = []
    scores = []
    for row in test_rows:
        pred, score = direct_flag_predict(row)
        predictions.append(pred)
        scores.append(score)
    return evaluate_predictions(test_rows, predictions, scores)


def evaluate_majority(test_rows: list[dict]) -> dict:
    predictions = ["mutation_stress"] * len(test_rows)
    scores = [1.0] * len(test_rows)
    return evaluate_predictions(test_rows, predictions, scores)


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_outputs(
    output_dir: Path,
    input_path: Path,
    rows: list[dict],
    splits: dict[str, list[dict]],
    results: list[dict],
    direct_alias_fields: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_mutation_stress_baseline_report.md"
    json_path = output_dir / "pqid_bench_mutation_stress_baseline_report.json"

    target_counts = Counter(row["_target"] for row in rows)
    benchmark_counts = Counter(row["_benchmark_label"] for row in rows)
    split_counts = {
        split: dict(Counter(row["_target"] for row in split_rows))
        for split, split_rows in splits.items()
    }
    test_counts = Counter(row["_target"] for row in splits["test"])

    lines = [
        "# PQID-Bench Mutation-Stress Detection Baseline Report",
        "",
        f"- input file: `{display_path(input_path)}`",
        f"- selected rows: `{len(rows):,}`",
        f"- clean controls: `{target_counts['clean_control']:,}`",
        f"- mutation-stress rows: `{target_counts['mutation_stress']:,}`",
        "- split: deterministic stratified group split by `split_group_id`",
        "",
        "## Detection Pool",
        "",
        "| benchmark label | rows | target |",
        "| --- | ---: | --- |",
    ]
    for label in ["strict_n8", "extended_n8", "mutation_stress_n8"]:
        target = "clean_control" if label in CLEAN_LABELS else "mutation_stress"
        lines.append(f"| `{label}` | {benchmark_counts[label]:,} | `{target}` |")

    lines.extend(
        [
            "",
            "## Split Counts",
            "",
            "| split | clean_control | mutation_stress | total |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for split in ["train", "validation", "test"]:
        clean = split_counts[split].get("clean_control", 0)
        stress = split_counts[split].get("mutation_stress", 0)
        lines.append(f"| {split} | {clean:,} | {stress:,} | {clean + stress:,} |")

    lines.extend(
        [
            "",
            "## Baselines",
            "",
            "The direct mutation flag baseline is an audit sanity check, not a fair learned baseline. Learned baselines exclude direct target aliases.",
            "",
            "| baseline | feature view | priors | accuracy | balanced accuracy | macro-F1 | AUROC | false-clean rate | false-stress rate | mismatches |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in results:
        metrics = row["metrics"]
        lines.append(
            f"| {row['name']} | {row['feature_view']} | {row['priors']} | "
            f"{pct(metrics['accuracy'])} | {pct(metrics['balanced_accuracy'])} | "
            f"{pct(metrics['macro_f1'])} | {metrics['auroc']:.4f} | "
            f"{pct(metrics['false_clean_rate'])} | {pct(metrics['false_stress_rate'])} | "
            f"{metrics['mismatches']:,} |"
        )

    best_fair = max(
        [row for row in results if row["fair_learned_baseline"]],
        key=lambda row: (row["metrics"]["balanced_accuracy"], row["metrics"]["macro_f1"]),
    )
    lines.extend(
        [
            "",
            "## Best Fair Learned Baseline Per-Class Metrics",
            "",
            f"Best fair baseline: `{best_fair['name']}`.",
            "",
            "| class | precision | recall | F1 | support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in ["clean_control", "mutation_stress"]:
        metrics = best_fair["metrics"]["per_label"][label]
        lines.append(
            f"| `{label}` | {pct(metrics['precision'])} | {pct(metrics['recall'])} | "
            f"{pct(metrics['f1'])} | {metrics['support']:,} |"
        )

    lines.extend(
        [
            "",
            "## Clean-Slice False-Stress Rates",
            "",
            "| clean slice | support | false-stress rows | false-stress rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for label in ["strict_n8", "extended_n8"]:
        metrics = best_fair["metrics"]["clean_slice_false_stress"].get(
            label,
            {"support": 0, "false_stress": 0, "false_stress_rate": 0.0},
        )
        lines.append(
            f"| `{label}` | {metrics['support']:,} | {metrics['false_stress']:,} | "
            f"{pct(metrics['false_stress_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Direct Alias Fields Excluded From Fair Baselines",
            "",
        ]
    )
    for field in direct_alias_fields:
        lines.append(f"- `{field}`")

    payload = {
        "input_file": display_path(input_path),
        "row_count": len(rows),
        "target_counts": dict(target_counts),
        "benchmark_counts": dict(benchmark_counts),
        "split_counts": split_counts,
        "test_counts": dict(test_counts),
        "direct_alias_fields_excluded": direct_alias_fields,
        "results": results,
        "best_fair_baseline": best_fair["name"],
    }

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {display_path(report_path)}")
    print(f"Wrote {display_path(json_path)}")


def run(input_path: Path, output_dir: Path) -> None:
    rows = load_rows(input_path)
    expected_count = 415 + 319 + 11265
    if len(rows) != expected_count:
        raise ValueError(f"Expected {expected_count:,} clean/stress rows, found {len(rows):,}")

    splits = split_rows(rows)
    train_rows = splits["train"]
    test_rows = splits["test"]

    results = [
        {
            "name": "majority class (mutation_stress)",
            "feature_view": "none",
            "priors": "n/a",
            "fair_learned_baseline": False,
            "metrics": evaluate_majority(test_rows),
        },
        {
            "name": "direct mutation flag",
            "feature_view": "mutation_suite_candidate",
            "priors": "n/a",
            "fair_learned_baseline": False,
            "metrics": evaluate_direct_flag(test_rows),
        },
    ]

    for feature_set in FEATURE_SETS:
        for uniform_priors in [False, True]:
            priors = "uniform" if uniform_priors else "empirical"
            results.append(
                {
                    "name": f"categorical Naive Bayes ({feature_set}, {priors} priors)",
                    "feature_view": FEATURE_SETS[feature_set]["description"],
                    "priors": priors,
                    "fair_learned_baseline": True,
                    "metrics": run_model(train_rows, test_rows, feature_set, uniform_priors),
                }
            )

    write_outputs(output_dir, input_path, rows, splits, results, DIRECT_ALIAS_FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
