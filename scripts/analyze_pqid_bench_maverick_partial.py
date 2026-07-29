"""Analyze the incomplete 99-response GitHub Models Maverick row.

The analysis keeps the provider error outside the model denominator, compares
all completed models on exactly the same prompts, and checks whether the
observed prefix differs from the 55 unobserved extension prompts.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable

from pqid_bench_model_registry import MODEL_LABELS, MODEL_ORDER, model_from_report_dir


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
MAVERICK_DIR = ROOT / "artifacts/external_model_batches_154/meta_expansion"
MAVERICK_RESPONSE_PATH = (
    MAVERICK_DIR
    / "responses/github_models_meta_llama-4-maverick-17b-128e-instruct-fp8_responses.jsonl"
)
MAVERICK_REPORT_PATH = (
    MAVERICK_DIR
    / "evaluations/github_models_meta_llama-4-maverick-17b-128e-instruct-fp8_partial"
    / "pqid_bench_external_model_generation_harness_report.json"
)
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
OUT_DIR = MAVERICK_DIR / "partial_99_analysis"
JSON_OUT = OUT_DIR / "maverick_partial_99_analysis.json"
MD_OUT = OUT_DIR / "maverick_partial_99_analysis.md"
CSV_OUT = OUT_DIR / "maverick_partial_99_matched_comparison.csv"

MAVERICK_ID = "meta/llama-4-maverick-17b-128e-instruct-fp8"
MAVERICK_LABEL = "Llama 4 Maverick"
Z_95 = 1.959963984540054


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f} pp"


def wilson(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    radius = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denom
    return (max(0.0, center - radius), min(1.0, center + radius))


def canonical_responses(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        prompt_id = str(row.get("prompt_id") or "")
        if prompt_id:
            rows[prompt_id] = row
    return rows


def record_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["prompt_id"]): row for row in report.get("records", [])}


def execution_success(record: dict[str, Any]) -> bool:
    execution = record.get("execution") or {}
    return bool(execution.get("execution_success") and execution.get("circuit_found"))


def qasm3_success(record: dict[str, Any]) -> bool:
    return bool(((record.get("execution") or {}).get("qasm3_export") or {}).get("success"))


def structural_checks(record: dict[str, Any]) -> dict[str, bool]:
    return {key: bool(value) for key, value in (record.get("structural_checks") or {}).items()}


METRICS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "execution_success": execution_success,
    "qasm3_success": qasm3_success,
    "structural_all_match": lambda row: structural_checks(row).get("all_match", False),
    "gate_types_match": lambda row: structural_checks(row).get("gate_types_match", False),
    "gate_count_match": lambda row: structural_checks(row).get("gate_count_match", False),
    "num_qubits_match": lambda row: structural_checks(row).get("num_qubits_match", False),
    "num_clbits_match": lambda row: structural_checks(row).get("num_clbits_match", False),
}


def metric_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    total = len(records)
    result = {}
    for name, predicate in METRICS.items():
        count = sum(predicate(row) for row in records)
        low, high = wilson(count, total)
        result[name] = {
            "count": count,
            "n": total,
            "rate": count / total if total else 0.0,
            "wilson_95": [low, high],
        }
    return result


def exact_mcnemar_p(maverick_wins: int, comparator_wins: int) -> float:
    discordant = maverick_wins + comparator_wins
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(maverick_wins, comparator_wins) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def phi(a: list[bool], b: list[bool]) -> float | None:
    n11 = sum(x and y for x, y in zip(a, b))
    n10 = sum(x and not y for x, y in zip(a, b))
    n01 = sum(not x and y for x, y in zip(a, b))
    n00 = sum(not x and not y for x, y in zip(a, b))
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return (n11 * n00 - n10 * n01) / denom if denom else None


def target_signature(prompt: dict[str, Any]) -> str:
    metadata = prompt["target_metadata"]
    gates = sorted((str(key), int(value)) for key, value in metadata["gate_types"].items())
    value = [
        int(metadata["num_qubits"]),
        int(metadata["num_clbits"]),
        int(metadata["gate_count"]),
        gates,
    ]
    return json.dumps(value, separators=(",", ":"))


def gate_entropy(prompt: dict[str, Any]) -> float:
    counts = [int(value) for value in prompt["target_metadata"]["gate_types"].values()]
    total = sum(counts)
    return -sum((count / total) * math.log(count / total) for count in counts if count) if total else 0.0


def gate_type_bin(prompt: dict[str, Any]) -> str:
    count = len(prompt["target_metadata"]["gate_types"])
    return "1-2" if count <= 2 else "3-4" if count <= 4 else "5+"


def bootstrap_signature_rate(
    prompts: dict[str, dict[str, Any]],
    prompt_ids: list[str],
    outcomes: dict[str, bool],
    iterations: int = 20_000,
) -> dict[str, Any]:
    groups: dict[str, list[bool]] = defaultdict(list)
    for prompt_id in prompt_ids:
        groups[target_signature(prompts[prompt_id])].append(outcomes[prompt_id])
    group_rates = [sum(values) / len(values) for values in groups.values()]
    point = mean(group_rates)
    rng = random.Random(20260713)
    boot = []
    for _ in range(iterations):
        boot.append(mean(rng.choice(group_rates) for _ in group_rates))
    boot.sort()
    low = boot[int(0.025 * iterations)]
    high = boot[int(0.975 * iterations)]
    return {
        "prompt_instances": len(prompt_ids),
        "unique_signatures": len(groups),
        "signature_collapsed_rate": point,
        "signature_cluster_bootstrap_95": [low, high],
        "duplicate_groups": sum(len(values) > 1 for values in groups.values()),
        "prompts_in_duplicate_groups": sum(len(values) for values in groups.values() if len(values) > 1),
    }


def permutation_mean_test(observed: list[float], missing: list[float], iterations: int = 50_000) -> float:
    actual = abs(mean(observed) - mean(missing))
    values = observed + missing
    n_observed = len(observed)
    rng = random.Random(20260713)
    extreme = 0
    for _ in range(iterations):
        rng.shuffle(values)
        delta = abs(mean(values[:n_observed]) - mean(values[n_observed:]))
        extreme += delta >= actual - 1e-15
    return (extreme + 1) / (iterations + 1)


def cohen_d(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    var_a = sum((value - mean(a)) ** 2 for value in a) / (len(a) - 1)
    var_b = sum((value - mean(b)) ** 2 for value in b) / (len(b) - 1)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    return (mean(a) - mean(b)) / pooled if pooled else 0.0


def linear_prediction(xs: list[float], ys: list[float], x: float) -> dict[str, float]:
    x_bar = mean(xs)
    y_bar = mean(ys)
    denominator = sum((value - x_bar) ** 2 for value in xs)
    slope = sum((a - x_bar) * (b - y_bar) for a, b in zip(xs, ys)) / denominator if denominator else 0.0
    intercept = y_bar - slope * x_bar
    predicted = min(1.0, max(0.0, intercept + slope * x))
    residuals = [b - (intercept + slope * a) for a, b in zip(xs, ys)]
    rmse = math.sqrt(mean(value * value for value in residuals))
    return {"intercept": intercept, "slope": slope, "predicted": predicted, "rmse": rmse}


def main() -> None:
    prompts_list = read_jsonl(PROMPT_PATH)
    prompts = {row["prompt_id"]: row for row in prompts_list}
    all_prompt_ids = [row["prompt_id"] for row in prompts_list]
    split = read_json(SPLIT_PATH)
    cohorts = {row["prompt_id"]: row["cohort"] for row in split["test_prompt_order"]}

    responses = canonical_responses(MAVERICK_RESPONSE_PATH)
    observed_ids = sorted(
        prompt_id
        for prompt_id, row in responses.items()
        if str(row.get("finish_reason") or "").lower() != "error"
        and bool(str(row.get("generated_code") or "").strip())
    )
    provider_error_ids = sorted(set(responses) - set(observed_ids))
    missing_ids = [prompt_id for prompt_id in all_prompt_ids if prompt_id not in responses]

    maverick_report = read_json(MAVERICK_REPORT_PATH)
    maverick_map = record_map(maverick_report)
    maverick_records = [maverick_map[prompt_id] for prompt_id in observed_ids]
    maverick_metrics = metric_summary(maverick_records)
    maverick_structural = {
        prompt_id: METRICS["structural_all_match"](maverick_map[prompt_id])
        for prompt_id in observed_ids
    }

    comparator_maps: dict[str, dict[str, dict[str, Any]]] = {}
    for report_path in sorted(EVAL_DIR.glob(f"*/{REPORT_NAME}")):
        model = model_from_report_dir(report_path.parent.name)
        if model not in MODEL_ORDER:
            continue
        comparator_maps[model] = record_map(read_json(report_path))

    if set(comparator_maps) != set(MODEL_ORDER):
        missing_models = sorted(set(MODEL_ORDER) - set(comparator_maps))
        raise RuntimeError(f"Missing completed comparator reports: {missing_models}")

    comparisons = []
    comparator_vectors: dict[str, list[bool]] = {}
    maverick_vector = [maverick_structural[prompt_id] for prompt_id in observed_ids]
    for model in MODEL_ORDER:
        records = comparator_maps[model]
        vector = [METRICS["structural_all_match"](records[prompt_id]) for prompt_id in observed_ids]
        comparator_vectors[model] = vector
        n11 = sum(a and b for a, b in zip(maverick_vector, vector))
        maverick_wins = sum(a and not b for a, b in zip(maverick_vector, vector))
        comparator_wins = sum(not a and b for a, b in zip(maverick_vector, vector))
        n00 = len(observed_ids) - n11 - maverick_wins - comparator_wins
        full_vector = [
            METRICS["structural_all_match"](records[prompt_id]) for prompt_id in all_prompt_ids
        ]
        missing_vector = [
            METRICS["structural_all_match"](records[prompt_id])
            for prompt_id in all_prompt_ids
            if prompt_id not in observed_ids
        ]
        comparisons.append(
            {
                "model": model,
                "label": MODEL_LABELS[model],
                "matched_n": len(observed_ids),
                "matched_structural_count": sum(vector),
                "matched_structural_rate": mean(vector),
                "full_154_structural_rate": mean(full_vector),
                "unobserved_55_structural_rate": mean(missing_vector),
                "maverick_minus_model": mean(maverick_vector) - mean(vector),
                "maverick_wins": maverick_wins,
                "model_wins": comparator_wins,
                "both_match": n11,
                "neither_matches": n00,
                "agreement": (n11 + n00) / len(observed_ids),
                "phi": phi(maverick_vector, vector),
                "jaccard": n11 / (n11 + maverick_wins + comparator_wins),
                "mcnemar_exact_p": exact_mcnemar_p(maverick_wins, comparator_wins),
            }
        )

    nearest = sorted(comparisons, key=lambda row: (-row["agreement"], -(row["phi"] or -2.0)))
    ranking = sorted(
        [(MAVERICK_ID, MAVERICK_LABEL, mean(maverick_vector))]
        + [(row["model"], row["label"], row["matched_structural_rate"]) for row in comparisons],
        key=lambda row: (-row[2], row[1]),
    )
    maverick_rank = 1 + sum(rate > mean(maverick_vector) for _, _, rate in ranking)

    existing_solve_count = {
        prompt_id: sum(comparator_vectors[model][index] for model in MODEL_ORDER)
        for index, prompt_id in enumerate(observed_ids)
    }
    unique_solves = [
        prompt_id
        for prompt_id in observed_ids
        if maverick_structural[prompt_id] and existing_solve_count[prompt_id] == 0
    ]
    rare_solves = [
        {"prompt_id": prompt_id, "existing_model_solves": existing_solve_count[prompt_id]}
        for prompt_id in observed_ids
        if maverick_structural[prompt_id] and existing_solve_count[prompt_id] <= 2
    ]

    item_rates = {
        prompt_id: mean(
            METRICS["structural_all_match"](comparator_maps[model][prompt_id])
            for model in MODEL_ORDER
        )
        for prompt_id in all_prompt_ids
    }
    unobserved_ids = [prompt_id for prompt_id in all_prompt_ids if prompt_id not in observed_ids]
    observed_item_rates = [item_rates[prompt_id] for prompt_id in observed_ids]
    unobserved_item_rates = [item_rates[prompt_id] for prompt_id in unobserved_ids]

    feature_names = {
        "num_qubits": lambda row: float(row["target_metadata"]["num_qubits"]),
        "num_clbits": lambda row: float(row["target_metadata"]["num_clbits"]),
        "gate_count": lambda row: float(row["target_metadata"]["gate_count"]),
        "gate_type_count": lambda row: float(len(row["target_metadata"]["gate_types"])),
        "gate_entropy": gate_entropy,
    }
    feature_balance = {}
    for name, extractor in feature_names.items():
        observed_values = [extractor(prompts[prompt_id]) for prompt_id in observed_ids]
        unobserved_values = [extractor(prompts[prompt_id]) for prompt_id in unobserved_ids]
        feature_balance[name] = {
            "observed_mean": mean(observed_values),
            "unobserved_mean": mean(unobserved_values),
            "standardized_difference": cohen_d(observed_values, unobserved_values),
        }

    observed_x = [row["matched_structural_rate"] for row in comparisons]
    missing_y = [row["unobserved_55_structural_rate"] for row in comparisons]
    calibration = linear_prediction(observed_x, missing_y, mean(maverick_vector))
    projected_full = (
        len(observed_ids) * mean(maverick_vector)
        + len(unobserved_ids) * calibration["predicted"]
    ) / len(all_prompt_ids)

    outcomes_by_bin: dict[str, list[bool]] = defaultdict(list)
    outcomes_by_cohort: dict[str, list[bool]] = defaultdict(list)
    for prompt_id in observed_ids:
        outcomes_by_bin[gate_type_bin(prompts[prompt_id])].append(maverick_structural[prompt_id])
        outcomes_by_cohort[cohorts[prompt_id]].append(maverick_structural[prompt_id])

    mismatch_counts = Counter()
    execution_errors = Counter()
    executable_nonmatches = 0
    for record in maverick_records:
        checks = structural_checks(record)
        if execution_success(record) and not checks.get("all_match", False):
            executable_nonmatches += 1
            for key in ("gate_types_match", "gate_count_match", "num_qubits_match", "num_clbits_match"):
                if not checks.get(key, False):
                    mismatch_counts[key.replace("_match", "_mismatch")] += 1
        if not execution_success(record):
            error_type = str((record.get("execution") or {}).get("execution_error_type") or "unknown")
            execution_errors[error_type] += 1

    signature_sensitivity = bootstrap_signature_rate(
        prompts, observed_ids, maverick_structural
    )
    observed_cohorts = Counter(cohorts[prompt_id] for prompt_id in observed_ids)
    unobserved_cohorts = Counter(cohorts[prompt_id] for prompt_id in unobserved_ids)
    observed_labels = Counter(prompts[prompt_id]["label"] for prompt_id in observed_ids)
    unobserved_labels = Counter(prompts[prompt_id]["label"] for prompt_id in unobserved_ids)
    observed_bins = Counter(gate_type_bin(prompts[prompt_id]) for prompt_id in observed_ids)
    unobserved_bins = Counter(gate_type_bin(prompts[prompt_id]) for prompt_id in unobserved_ids)

    result = {
        "scope": {
            "canonical_response_records": len(responses),
            "model_response_denominator": len(observed_ids),
            "provider_error_ids_excluded": provider_error_ids,
            "unattempted_prompt_ids": missing_ids,
            "observed_cohorts": dict(observed_cohorts),
            "unobserved_cohorts": dict(unobserved_cohorts),
            "observed_labels": dict(observed_labels),
            "unobserved_labels": dict(unobserved_labels),
            "observed_gate_type_bins": dict(observed_bins),
            "unobserved_gate_type_bins": dict(unobserved_bins),
        },
        "maverick_metrics": maverick_metrics,
        "execution_structure_gap": (
            maverick_metrics["execution_success"]["rate"]
            - maverick_metrics["structural_all_match"]["rate"]
        ),
        "runnable_but_structurally_wrong": {
            "count": sum(execution_success(row) and not METRICS["structural_all_match"](row) for row in maverick_records),
            "rate_all_prompts": mean(
                execution_success(row) and not METRICS["structural_all_match"](row)
                for row in maverick_records
            ),
            "rate_given_execution": sum(
                execution_success(row) and not METRICS["structural_all_match"](row)
                for row in maverick_records
            ) / sum(execution_success(row) for row in maverick_records),
        },
        "mismatch_counts": dict(mismatch_counts),
        "executable_structural_nonmatches": executable_nonmatches,
        "execution_errors": dict(execution_errors),
        "structural_by_gate_type_bin": {
            key: {"n": len(values), "count": sum(values), "rate": mean(values)}
            for key, values in sorted(outcomes_by_bin.items())
        },
        "structural_by_cohort": {
            key: {"n": len(values), "count": sum(values), "rate": mean(values)}
            for key, values in sorted(outcomes_by_cohort.items())
        },
        "signature_sensitivity": signature_sensitivity,
        "matched_comparisons": comparisons,
        "matched_ranking": [
            {"model": model, "label": label, "rate": rate}
            for model, label, rate in ranking
        ],
        "maverick_rank_of_19": maverick_rank,
        "nearest_profiles": nearest[:5],
        "complementarity": {
            "unique_solves_beyond_18_models": unique_solves,
            "rare_solves": rare_solves,
        },
        "representativeness": {
            "completed_model_item_rate_observed_99": mean(observed_item_rates),
            "completed_model_item_rate_unobserved_55": mean(unobserved_item_rates),
            "difference_observed_minus_unobserved": mean(observed_item_rates) - mean(unobserved_item_rates),
            "median_item_rate_observed_99": median(observed_item_rates),
            "median_item_rate_unobserved_55": median(unobserved_item_rates),
            "cohen_d": cohen_d(observed_item_rates, unobserved_item_rates),
            "permutation_p": permutation_mean_test(observed_item_rates, unobserved_item_rates),
            "feature_balance": feature_balance,
        },
        "descriptive_completion_projection": {
            "method": "OLS across 18 completed models: missing-55 rate from matched-99 rate",
            "predicted_missing_55_rate": calibration["predicted"],
            "projected_full_154_rate": projected_full,
            "intercept": calibration["intercept"],
            "slope": calibration["slope"],
            "comparator_fit_rmse": calibration["rmse"],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with CSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "model",
            "label",
            "matched_n",
            "matched_structural_count",
            "matched_structural_rate",
            "full_154_structural_rate",
            "unobserved_55_structural_rate",
            "maverick_minus_model",
            "maverick_wins",
            "model_wins",
            "agreement",
            "phi",
            "mcnemar_exact_p",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in comparisons:
            writer.writerow({key: row[key] for key in fieldnames})

    structural = maverick_metrics["structural_all_match"]
    execution = maverick_metrics["execution_success"]
    lines = [
        "# Llama 4 Maverick Partial-Row Diagnostic",
        "",
        "## Scope",
        "",
        f"The GitHub Models run returned `99` model responses before the provider quota stopped the batch. "
        f"Prompt `{provider_error_ids[0] if provider_error_ids else '--'}` is a provider error and is excluded from the model denominator; "
        f"the remaining `{len(missing_ids)}` prompts were never sent. The diagnostic therefore uses `n={len(observed_ids)}`, not `n=100`.",
        "",
        f"The observed set contains `{observed_cohorts.get('pilot', 0)}` pilot prompts and `{observed_cohorts.get('extension', 0)}` extension prompts. "
        f"All `{unobserved_cohorts.get('extension', 0)}` unobserved prompts belong to the extension cohort, so the partial row is not a simple random subsample of the final test set.",
        "",
        "## Partial Results",
        "",
        "| metric | count | rate | Wilson 95% interval |",
        "| --- | ---: | ---: | ---: |",
    ]
    metric_labels = {
        "execution_success": "executable circuit",
        "qasm3_success": "QASM3 export",
        "structural_all_match": "all-structure match",
        "gate_types_match": "gate-type count-map match",
        "gate_count_match": "gate-count match",
        "num_qubits_match": "qubit-count match",
        "num_clbits_match": "classical-bit-count match",
    }
    for key in METRICS:
        row = maverick_metrics[key]
        lines.append(
            f"| {metric_labels[key]} | {row['count']}/{row['n']} | {pct(row['rate'])} | "
            f"{pct(row['wilson_95'][0])}--{pct(row['wilson_95'][1])} |"
        )
    lines.extend(
        [
            "",
            f"The execution--structure gap is `{pp(result['execution_structure_gap'])}`. "
            f"Among `{execution['count']}` executable outputs, "
            f"`{result['runnable_but_structurally_wrong']['count']}` are structurally wrong "
            f"(`{pct(result['runnable_but_structurally_wrong']['rate_given_execution'])}`).",
            "",
            f"The observed prompts contain `{signature_sensitivity['unique_signatures']}` unique evaluator-facing target signatures. "
            f"Signature-collapsed structural match is `{pct(signature_sensitivity['signature_collapsed_rate'])}`, "
            f"versus `{pct(structural['rate'])}` at prompt level.",
            "",
            "## Failure Pattern",
            "",
            f"Component mismatches among the `{executable_nonmatches}` executable structural nonmatches are: "
            + ", ".join(f"`{key}` `{value}`" for key, value in sorted(mismatch_counts.items()))
            + ".",
            "",
            "| gate-type bin | matches | rate |",
            "| --- | ---: | ---: |",
        ]
    )
    for key in ("1-2", "3-4", "5+"):
        row = result["structural_by_gate_type_bin"].get(key, {"count": 0, "n": 0, "rate": 0.0})
        lines.append(f"| {key} | {row['count']}/{row['n']} | {pct(row['rate'])} |")
    lines.extend(
        [
            "",
            "| test cohort | matches | rate |",
            "| --- | ---: | ---: |",
        ]
    )
    for key in ("pilot", "extension"):
        row = result["structural_by_cohort"].get(key, {"count": 0, "n": 0, "rate": 0.0})
        lines.append(f"| {key} | {row['count']}/{row['n']} | {pct(row['rate'])} |")

    lines.extend(
        [
            "",
            "## Matched-Prompt Position",
            "",
            f"On the common 99 prompts, Maverick ranks `{maverick_rank}` of `19` rows by structural match. "
            "This ranking is diagnostic only because Maverick lacks the other 55 responses.",
            "",
            "| comparator | comparator rate | Maverick minus comparator | Maverick wins | comparator wins | agreement | exact paired p |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in comparisons:
        lines.append(
            f"| {row['label']} | {pct(row['matched_structural_rate'])} | {pp(row['maverick_minus_model'])} | "
            f"{row['maverick_wins']} | {row['model_wins']} | {pct(row['agreement'])} | {row['mcnemar_exact_p']:.4f} |"
        )
    lines.extend(
        [
            "",
            "The five nearest success/failure profiles are: "
            + ", ".join(
                f"{row['label']} ({pct(row['agreement'])} agreement)" for row in nearest[:5]
            )
            + ".",
            "",
            f"Maverick adds `{len(unique_solves)}` prompt solved by no completed model row. "
            f"It solves `{len(rare_solves)}` prompts solved by at most two of the 18 completed rows.",
            "",
            "## Representativeness Of The 99 Prompts",
            "",
            f"Across the 18 completed models, mean structural success is "
            f"`{pct(mean(observed_item_rates))}` on Maverick's observed prompts and "
            f"`{pct(mean(unobserved_item_rates))}` on the unobserved prompts "
            f"(`{pp(mean(observed_item_rates) - mean(unobserved_item_rates))}`; "
            f"permutation `p={result['representativeness']['permutation_p']:.4f}`).",
            "",
            f"A descriptive calibration across the 18 completed rows predicts Maverick at "
            f"`{pct(calibration['predicted'])}` on the missing 55 and "
            f"`{pct(projected_full)}` on all 154. This is a projection, not a substitute for observations; "
            f"the comparator-model fit RMSE is `{pp(calibration['rmse'])}`.",
            "",
            "## Decision",
            "",
            f"The 99-prompt row is adequate for a broad behavioral diagnosis: its all-structure estimate is "
            f"`{pct(structural['rate'])}` with a Wilson interval of "
            f"`{pct(structural['wilson_95'][0])}`--`{pct(structural['wilson_95'][1])}`. "
            "It can distinguish Maverick from substantially stronger or weaker tiers and supports paired profile comparisons.",
            "",
            "It is not adequate as a completed leaderboard row or as an equal participant in the 154-prompt heatmap. "
            "The missing prompts all come from the extension cohort, and differences of only a few percentage points remain unresolved. "
            "Use this artifact to decide whether a formal Meta row is worth completing; do not merge the partial GitHub row with another provider.",
            "",
            f"- JSON: `{JSON_OUT.relative_to(ROOT).as_posix()}`",
            f"- matched comparison CSV: `{CSV_OUT.relative_to(ROOT).as_posix()}`",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {MD_OUT}")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
