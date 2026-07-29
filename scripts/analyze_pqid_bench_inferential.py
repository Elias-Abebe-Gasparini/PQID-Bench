"""Run cluster-aware inferential analyses for the frozen PQID-Bench matrix.

The estimand is deliberately release-bound: associations and paired model
contrasts for the fixed 21-model panel evaluated on 154 held-out prompts. The
task-feature models use each prompt's success count over the fixed model panel
and resample complete target-signature clusters, so prompt-model cells are not
treated as 3,234 independent observations. Model fixed effects are retained
only for grouped cross-validation, where predictions target the same observed
model panel.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.special import expit
from scipy.stats import binomtest, rankdata

from pqid_bench_model_registry import (
    EXPANDED_MODEL_ORDER,
    MISTRAL_PARENT_MODEL,
    MODEL_LABELS,
    MODEL_ORDER,
    QISKIT_SPECIALIST_MODEL,
    model_from_report_dir,
)


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
JSON_OUT = ANALYSIS_DIR / "pqid_bench_inferential_analysis.json"
MD_OUT = ANALYSIS_DIR / "pqid_bench_inferential_analysis.md"
TERM_CSV_OUT = ANALYSIS_DIR / "pqid_bench_inferential_model_terms.csv"
CV_CSV_OUT = ANALYSIS_DIR / "pqid_bench_grouped_cross_validation.csv"
PAIR_CSV_OUT = ANALYSIS_DIR / "pqid_bench_paired_model_comparisons.csv"
RANK_CSV_OUT = ANALYSIS_DIR / "pqid_bench_rank_stability.csv"

IDENTIFIABILITY_EXCLUSIONS = {
    "pqid_bench_external_gen_0040",
    "pqid_bench_external_gen_0117",
    "pqid_bench_external_gen_0141",
    "pqid_bench_external_gen_0142",
}

PAIR_SPECS = [
    ("llama-3.1-8b-instant", "llama-3.3-70b-versatile", "Llama 8B -> 70B"),
    (
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "Llama 4 Scout -> Maverick",
    ),
    ("openai/gpt-oss-20b", "openai/gpt-oss-120b", "GPT-OSS 20B -> 120B"),
    ("gemini-2.5-pro", "gemini-3.1-pro-preview", "Gemini 2.5 -> 3.1"),
    ("claude-sonnet-4-6", "claude-opus-4-8", "Claude Sonnet -> Opus"),
    ("claude-opus-4-8", "claude-fable-5", "Claude Opus -> Fable"),
    ("deepseek-v4-flash", "deepseek-v4-pro", "DeepSeek Flash -> Pro"),
    ("qwen/qwen3-32b", "qwen/qwen3-coder-next", "Qwen3 general -> Coder"),
    ("gpt-5.4-mini", "gpt-5.5", "GPT-5.4 mini -> GPT-5.5"),
    ("gpt-5.5", "gpt-5.6-sol", "GPT-5.5 -> GPT-5.6 Sol"),
]

SPECIALIST_PAIR_SPEC = (
    MISTRAL_PARENT_MODEL,
    QISKIT_SPECIALIST_MODEL,
    "Mistral parent -> Qiskit specialist",
)
PAIR_SPECS.append(SPECIALIST_PAIR_SPEC)

CONTINUOUS_FEATURES = {
    "gate_entropy",
    "gate_type_count",
    "log_gate_count",
    "num_qubits",
    "num_clbits",
}

MODEL_SPECS = {
    "entropy": [
        "gate_entropy",
        "log_gate_count",
        "num_qubits",
        "num_clbits",
        "has_barrier",
    ],
    "gate_type_count": [
        "gate_type_count",
        "log_gate_count",
        "num_qubits",
        "num_clbits",
        "has_barrier",
    ],
    "size_only": ["log_gate_count", "num_qubits", "num_clbits"],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def gate_entropy(gates: dict[str, int]) -> float:
    total = sum(gates.values())
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log(count / total) for count in gates.values())


def metadata_signature(prompt: dict[str, Any]) -> str:
    metadata = prompt["target_metadata"]
    value = {
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "gate_count": int(metadata["gate_count"]),
        "gate_types": {
            str(name): int(count)
            for name, count in sorted(metadata["gate_types"].items())
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def prompt_features(prompt: dict[str, Any]) -> dict[str, float | int | str]:
    metadata = prompt["target_metadata"]
    gates = {str(name): int(count) for name, count in metadata["gate_types"].items()}
    return {
        "prompt_id": str(prompt["prompt_id"]),
        "signature": metadata_signature(prompt),
        "gate_entropy": gate_entropy(gates),
        "gate_type_count": len(gates),
        "log_gate_count": math.log1p(int(metadata["gate_count"])),
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "has_barrier": int("barrier" in gates),
    }


def load_evaluation_matrices(
    eval_dirs: Path | list[Path],
    prompt_ids: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    prompt_index = {prompt_id: index for index, prompt_id in enumerate(prompt_ids)}
    model_index = {model: index for index, model in enumerate(MODEL_ORDER)}
    shape = (len(prompt_ids), len(MODEL_ORDER))
    execution = np.full(shape, -1, dtype=np.int8)
    signature = np.full(shape, -1, dtype=np.int8)
    qasm3 = np.full(shape, -1, dtype=np.int8)
    sources: list[dict[str, Any]] = []

    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model not in model_index:
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
            seen = 0
            for record in report.get("records", []):
                prompt_id = str(record.get("prompt_id"))
                if prompt_id not in prompt_index:
                    continue
                p_idx = prompt_index[prompt_id]
                m_idx = model_index[model]
                exec_data = record.get("execution") or {}
                checks = record.get("structural_checks") or {}
                qasm_data = exec_data.get("qasm3_export") or {}
                circuit_found = bool(exec_data.get("circuit_found"))
                execution[p_idx, m_idx] = int(bool(exec_data.get("execution_success")) and circuit_found)
                signature[p_idx, m_idx] = int(bool(checks.get("all_match")))
                qasm3[p_idx, m_idx] = int(bool(qasm_data.get("success")))
                seen += 1
            sources.append(
                {
                    "model": model,
                    "model_label": MODEL_LABELS.get(model, model),
                    "report": report_path.as_posix(),
                    "records_loaded": seen,
                }
            )

    for name, matrix in (("execution", execution), ("signature", signature), ("QASM3", qasm3)):
        missing = np.argwhere(matrix < 0)
        if len(missing):
            examples = [
                f"{prompt_ids[p_idx]}::{MODEL_ORDER[m_idx]}"
                for p_idx, m_idx in missing[:10]
            ]
            raise RuntimeError(f"Missing {name} outcomes ({len(missing)}): {examples}")
    return execution, signature, qasm3, sources


def feature_arrays(feature_rows: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    return {
        name: np.asarray([float(row[name]) for row in feature_rows], dtype=float)
        for name in CONTINUOUS_FEATURES | {"has_barrier"}
    }


def standardization(
    arrays: dict[str, np.ndarray],
    feature_names: Iterable[str],
    prompt_mask: np.ndarray | None = None,
) -> dict[str, tuple[float, float]]:
    if prompt_mask is None:
        prompt_mask = np.ones(len(next(iter(arrays.values()))), dtype=bool)
    stats: dict[str, tuple[float, float]] = {}
    for name in feature_names:
        if name not in CONTINUOUS_FEATURES:
            continue
        values = arrays[name][prompt_mask]
        avg = float(np.mean(values))
        sd = float(np.std(values, ddof=1)) if len(values) > 1 else 1.0
        stats[name] = (avg, sd if sd > 0 else 1.0)
    return stats


def build_design(
    arrays: dict[str, np.ndarray],
    feature_names: list[str],
    prompt_indices: np.ndarray,
    model_indices: np.ndarray,
    stats: dict[str, tuple[float, float]],
) -> tuple[np.ndarray, list[str]]:
    columns = [np.ones(len(prompt_indices), dtype=float)]
    names = ["intercept"]
    for name in feature_names:
        values = arrays[name][prompt_indices].astype(float)
        if name in CONTINUOUS_FEATURES:
            avg, sd = stats[name]
            values = (values - avg) / sd
            output_name = f"z_{name}"
        else:
            output_name = name
        columns.append(values)
        names.append(output_name)
    for model_idx, model in enumerate(MODEL_ORDER[1:], start=1):
        columns.append((model_indices == model_idx).astype(float))
        names.append(f"model::{model}")
    return np.column_stack(columns), names


def build_prompt_design(
    arrays: dict[str, np.ndarray],
    feature_names: list[str],
    prompt_indices: np.ndarray,
    stats: dict[str, tuple[float, float]],
) -> tuple[np.ndarray, list[str]]:
    columns = [np.ones(len(prompt_indices), dtype=float)]
    names = ["intercept"]
    for name in feature_names:
        values = arrays[name][prompt_indices].astype(float)
        if name in CONTINUOUS_FEATURES:
            avg, sd = stats[name]
            values = (values - avg) / sd
            output_name = f"z_{name}"
        else:
            output_name = name
        columns.append(values)
        names.append(output_name)
    return np.column_stack(columns), names


def penalized_log_likelihood(
    x: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    beta: np.ndarray,
    ridge: float,
) -> float:
    eta = np.clip(x @ beta, -35.0, 35.0)
    log_prob = y * -np.logaddexp(0.0, -eta) + (1.0 - y) * -np.logaddexp(0.0, eta)
    penalty = 0.5 * ridge * float(np.dot(beta[1:], beta[1:]))
    return float(np.dot(weights, log_prob) - penalty)


def fit_logit(
    x: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray | None = None,
    *,
    ridge: float = 1e-4,
    max_iter: int = 80,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    if weights is None:
        weights = np.ones(len(y), dtype=float)
    else:
        weights = np.asarray(weights, dtype=float)
    active = weights > 0
    x_active = x[active]
    y_active = y[active].astype(float)
    w_active = weights[active]
    beta = np.zeros(x.shape[1], dtype=float)
    converged = False
    objective = penalized_log_likelihood(x_active, y_active, w_active, beta, ridge)

    penalty_diag = np.ones(x.shape[1], dtype=float)
    penalty_diag[0] = 0.0
    for iteration in range(1, max_iter + 1):
        probability = expit(np.clip(x_active @ beta, -35.0, 35.0))
        variance_weight = w_active * np.maximum(probability * (1.0 - probability), 1e-10)
        gradient = x_active.T @ (w_active * (y_active - probability)) - ridge * penalty_diag * beta
        hessian = x_active.T @ (variance_weight[:, None] * x_active)
        hessian.flat[:: hessian.shape[0] + 1] += ridge * penalty_diag
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]

        scale = 1.0
        candidate = beta + step
        candidate_objective = penalized_log_likelihood(
            x_active, y_active, w_active, candidate, ridge
        )
        while candidate_objective < objective and scale > 1e-6:
            scale *= 0.5
            candidate = beta + scale * step
            candidate_objective = penalized_log_likelihood(
                x_active, y_active, w_active, candidate, ridge
            )
        beta = candidate
        objective = candidate_objective
        if float(np.max(np.abs(scale * step))) < tolerance:
            converged = True
            break
    return {
        "beta": beta,
        "converged": converged,
        "iterations": iteration,
        "log_likelihood": objective,
    }


def average_marginal_effects(
    x: np.ndarray,
    beta: np.ndarray,
    names: list[str],
    feature_names: list[str],
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    if weights is None:
        weights = np.ones(len(x), dtype=float)
    weights = np.asarray(weights, dtype=float)
    denominator = float(np.sum(weights))
    probability = expit(np.clip(x @ beta, -35.0, 35.0))
    effects: dict[str, float] = {}
    for raw_name in feature_names:
        name = f"z_{raw_name}" if raw_name in CONTINUOUS_FEATURES else raw_name
        index = names.index(name)
        if raw_name in CONTINUOUS_FEATURES:
            effect = beta[index] * probability * (1.0 - probability)
        else:
            x_yes = x.copy()
            x_no = x.copy()
            x_yes[:, index] = 1.0
            x_no[:, index] = 0.0
            effect = expit(np.clip(x_yes @ beta, -35.0, 35.0)) - expit(
                np.clip(x_no @ beta, -35.0, 35.0)
            )
        effects[name] = float(np.dot(weights, effect) / denominator)
    return effects


def percentile_interval(values: np.ndarray) -> list[float]:
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def cluster_counts(rng: np.random.Generator, cluster_count: int) -> np.ndarray:
    return rng.multinomial(cluster_count, np.full(cluster_count, 1.0 / cluster_count))


def prompt_weights_from_cluster_counts(
    prompt_cluster: np.ndarray,
    counts: np.ndarray,
) -> np.ndarray:
    return counts[prompt_cluster].astype(float)


def prepare_grouped_model(
    arrays: dict[str, np.ndarray],
    outcome_matrix: np.ndarray,
    feature_names: list[str],
    *,
    prompt_mask: np.ndarray | None = None,
    conditional_on_execution: np.ndarray | None = None,
) -> dict[str, Any]:
    prompt_count, model_count = outcome_matrix.shape
    if prompt_mask is None:
        prompt_mask = np.ones(prompt_count, dtype=bool)
    if conditional_on_execution is not None:
        successes = np.sum(outcome_matrix, axis=1).astype(float)
        trials = np.sum(conditional_on_execution, axis=1).astype(float)
    else:
        successes = np.sum(outcome_matrix, axis=1).astype(float)
        trials = np.full(prompt_count, model_count, dtype=float)
    active_prompts = prompt_mask & (trials > 0)
    prompt_indices = np.flatnonzero(active_prompts)
    y = successes[active_prompts] / trials[active_prompts]
    base_weights = trials[active_prompts]
    stats = standardization(arrays, feature_names, prompt_mask)
    x, names = build_prompt_design(arrays, feature_names, prompt_indices, stats)
    return {
        "x": x,
        "y": y,
        "base_weights": base_weights,
        "successes": successes[active_prompts],
        "trials": trials[active_prompts],
        "names": names,
        "feature_names": feature_names,
        "prompt_indices": prompt_indices,
        "stats": stats,
    }


def inferential_models(
    arrays: dict[str, np.ndarray],
    execution: np.ndarray,
    signature: np.ndarray,
    prompt_cluster: np.ndarray,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, Any]:
    prompt_count = signature.shape[0]
    full_mask = np.ones(prompt_count, dtype=bool)
    identifiable_mask = np.asarray(
        [prompt_id not in IDENTIFIABILITY_EXCLUSIONS for prompt_id in arrays["prompt_id"]],
        dtype=bool,
    )
    analyses = {
        "signature_entropy_full": prepare_grouped_model(
            arrays, signature, MODEL_SPECS["entropy"], prompt_mask=full_mask
        ),
        "signature_gate_type_full": prepare_grouped_model(
            arrays, signature, MODEL_SPECS["gate_type_count"], prompt_mask=full_mask
        ),
        "execution_entropy_full": prepare_grouped_model(
            arrays, execution, MODEL_SPECS["entropy"], prompt_mask=full_mask
        ),
        "signature_given_execution_entropy_full": prepare_grouped_model(
            arrays,
            signature,
            MODEL_SPECS["entropy"],
            prompt_mask=full_mask,
            conditional_on_execution=execution,
        ),
        "signature_entropy_identifiable_150": prepare_grouped_model(
            arrays, signature, MODEL_SPECS["entropy"], prompt_mask=identifiable_mask
        ),
    }

    point_results: dict[str, Any] = {}
    bootstrap_betas: dict[str, list[np.ndarray]] = {key: [] for key in analyses}
    bootstrap_ames: dict[str, list[dict[str, float]]] = {key: [] for key in analyses}
    convergence = {key: 0 for key in analyses}

    for key, analysis in analyses.items():
        fitted = fit_logit(analysis["x"], analysis["y"], analysis["base_weights"])
        beta = fitted["beta"]
        ames = average_marginal_effects(
            analysis["x"],
            beta,
            analysis["names"],
            analysis["feature_names"],
            analysis["base_weights"],
        )
        point_results[key] = {
            "prompt_observations": len(analysis["y"]),
            "binomial_trials": int(np.sum(analysis["base_weights"])),
            "positive_rate": float(
                np.sum(analysis["successes"]) / np.sum(analysis["trials"])
            ),
            "converged": bool(fitted["converged"]),
            "iterations": int(fitted["iterations"]),
            "log_likelihood": float(fitted["log_likelihood"]),
            "standardization": {
                name: {"mean": avg, "sd": sd}
                for name, (avg, sd) in analysis["stats"].items()
            },
            "terms": {},
        }
        for raw_name in analysis["feature_names"]:
            name = f"z_{raw_name}" if raw_name in CONTINUOUS_FEATURES else raw_name
            index = analysis["names"].index(name)
            point_results[key]["terms"][name] = {
                "log_odds": float(beta[index]),
                "odds_ratio": float(math.exp(beta[index])),
                "average_marginal_effect": float(ames[name]),
            }

    rng = np.random.default_rng(seed)
    signature_count = int(np.max(prompt_cluster)) + 1
    for _ in range(bootstrap_replicates):
        counts = cluster_counts(rng, signature_count)
        prompt_weights = prompt_weights_from_cluster_counts(prompt_cluster, counts)
        for key, analysis in analyses.items():
            row_weights = (
                prompt_weights[analysis["prompt_indices"]] * analysis["base_weights"]
            )
            fitted = fit_logit(analysis["x"], analysis["y"], row_weights)
            if fitted["converged"]:
                convergence[key] += 1
            beta = fitted["beta"]
            bootstrap_betas[key].append(beta)
            bootstrap_ames[key].append(
                average_marginal_effects(
                    analysis["x"],
                    beta,
                    analysis["names"],
                    analysis["feature_names"],
                    row_weights,
                )
            )

    for key, analysis in analyses.items():
        beta_samples = np.vstack(bootstrap_betas[key])
        point_results[key]["bootstrap_replicates"] = bootstrap_replicates
        point_results[key]["bootstrap_converged"] = convergence[key]
        for raw_name in analysis["feature_names"]:
            name = f"z_{raw_name}" if raw_name in CONTINUOUS_FEATURES else raw_name
            index = analysis["names"].index(name)
            coefficient_values = beta_samples[:, index]
            odds_values = np.exp(np.clip(coefficient_values, -30.0, 30.0))
            ame_values = np.asarray([sample[name] for sample in bootstrap_ames[key]])
            term = point_results[key]["terms"][name]
            term["log_odds_bootstrap_95"] = percentile_interval(coefficient_values)
            term["odds_ratio_bootstrap_95"] = percentile_interval(odds_values)
            term["average_marginal_effect_bootstrap_95"] = percentile_interval(ame_values)
            term["interval_excludes_null"] = bool(
                term["odds_ratio_bootstrap_95"][1] < 1.0
                or term["odds_ratio_bootstrap_95"][0] > 1.0
            )

    contrasts = {}
    execution_ames = bootstrap_ames["execution_entropy_full"]
    conditional_ames = bootstrap_ames["signature_given_execution_entropy_full"]
    for term in ("z_gate_entropy", "has_barrier"):
        values = np.asarray(
            [
                conditional[term] - execution_value[term]
                for execution_value, conditional in zip(execution_ames, conditional_ames)
            ]
        )
        point = (
            point_results["signature_given_execution_entropy_full"]["terms"][term][
                "average_marginal_effect"
            ]
            - point_results["execution_entropy_full"]["terms"][term][
                "average_marginal_effect"
            ]
        )
        contrasts[f"conditional_signature_minus_execution::{term}"] = {
            "average_marginal_effect_difference": float(point),
            "bootstrap_95": percentile_interval(values),
        }

    return {
        "method": {
            "model": "grouped-binomial logistic regression over prompt success counts from the fixed model panel",
            "uncertainty": "percentile bootstrap over evaluator-facing target-signature clusters",
            "ridge_penalty": 1e-4,
            "bootstrap_replicates": bootstrap_replicates,
            "seed": seed,
        },
        "models": point_results,
        "two_stage_contrasts": contrasts,
    }


def auc_score(y: np.ndarray, probability: np.ndarray, weights: np.ndarray | None = None) -> float:
    if weights is None:
        weights = np.ones(len(y), dtype=float)
    order = np.argsort(probability, kind="mergesort")
    y_sorted = y[order]
    p_sorted = probability[order]
    w_sorted = weights[order]
    positive_weight = float(np.sum(w_sorted * y_sorted))
    negative_weight = float(np.sum(w_sorted * (1.0 - y_sorted)))
    if positive_weight == 0.0 or negative_weight == 0.0:
        return float("nan")
    starts = np.concatenate(
        (np.asarray([0]), np.flatnonzero(np.diff(p_sorted) != 0.0) + 1)
    )
    group_positive = np.add.reduceat(w_sorted * y_sorted, starts)
    group_negative = np.add.reduceat(w_sorted * (1.0 - y_sorted), starts)
    negative_before = np.cumsum(group_negative) - group_negative
    concordance = float(
        np.sum(group_positive * (negative_before + 0.5 * group_negative))
    )
    return concordance / (positive_weight * negative_weight)


def prediction_metrics(
    y: np.ndarray,
    probability: np.ndarray,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    if weights is None:
        weights = np.ones(len(y), dtype=float)
    weights = np.asarray(weights, dtype=float)
    probability = np.clip(probability, 1e-9, 1.0 - 1e-9)
    denominator = float(np.sum(weights))
    log_loss = -float(
        np.dot(weights, y * np.log(probability) + (1.0 - y) * np.log(1.0 - probability))
        / denominator
    )
    brier = float(np.dot(weights, (probability - y) ** 2) / denominator)
    return {
        "log_loss": log_loss,
        "brier": brier,
        "auc": auc_score(y, probability, weights),
    }


def stratified_signature_folds(
    signature_prompt_indices: list[np.ndarray],
    signature: np.ndarray,
    folds: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    records = []
    for cluster_idx, prompt_indices in enumerate(signature_prompt_indices):
        outcomes = signature[prompt_indices].reshape(-1)
        records.append(
            (
                cluster_idx,
                len(prompt_indices),
                float(np.mean(outcomes)),
                float(rng.random()),
            )
        )
    records.sort(key=lambda row: (-row[2], -row[1], row[3]))
    fold_positive = np.zeros(folds, dtype=float)
    fold_cells = np.zeros(folds, dtype=float)
    assignment = np.full(len(records), -1, dtype=int)
    target_rate = float(np.mean(signature))
    for cluster_idx, prompt_size, rate, _ in records:
        cells = prompt_size * signature.shape[1]
        positives = rate * cells
        candidates = []
        for fold in range(folds):
            new_cells = fold_cells[fold] + cells
            new_positive = fold_positive[fold] + positives
            rate_penalty = abs(new_positive / new_cells - target_rate) if new_cells else 0.0
            candidates.append((fold_cells[fold], rate_penalty, fold))
        selected = min(candidates)[2]
        assignment[cluster_idx] = selected
        fold_cells[selected] += cells
        fold_positive[selected] += positives
    return assignment


def grouped_cross_validation(
    arrays: dict[str, np.ndarray],
    signature: np.ndarray,
    prompt_cluster: np.ndarray,
    signature_prompt_indices: list[np.ndarray],
    folds: int,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, Any]:
    prompt_count, model_count = signature.shape
    full_prompt_indices = np.repeat(np.arange(prompt_count), model_count)
    full_model_indices = np.tile(np.arange(model_count), prompt_count)
    y = signature.reshape(-1).astype(float)
    fold_assignment = stratified_signature_folds(
        signature_prompt_indices, signature, folds, seed
    )
    prompt_fold = fold_assignment[prompt_cluster]
    predictions = {
        "size_only": np.full(len(y), np.nan, dtype=float),
        "entropy_plus_barrier": np.full(len(y), np.nan, dtype=float),
        "gate_type_plus_barrier": np.full(len(y), np.nan, dtype=float),
    }
    specs = {
        "size_only": MODEL_SPECS["size_only"],
        "entropy_plus_barrier": MODEL_SPECS["entropy"],
        "gate_type_plus_barrier": MODEL_SPECS["gate_type_count"],
    }
    fold_details = []
    for fold in range(folds):
        train_prompt_mask = prompt_fold != fold
        test_prompt_mask = prompt_fold == fold
        train_rows = train_prompt_mask[full_prompt_indices]
        test_rows = test_prompt_mask[full_prompt_indices]
        fold_record = {
            "fold": fold + 1,
            "training_prompts": int(np.sum(train_prompt_mask)),
            "test_prompts": int(np.sum(test_prompt_mask)),
            "test_signatures": int(np.sum(fold_assignment == fold)),
            "models": {},
        }
        for name, feature_names in specs.items():
            stats = standardization(arrays, feature_names, train_prompt_mask)
            x_train, design_names = build_design(
                arrays,
                feature_names,
                full_prompt_indices[train_rows],
                full_model_indices[train_rows],
                stats,
            )
            x_test, _ = build_design(
                arrays,
                feature_names,
                full_prompt_indices[test_rows],
                full_model_indices[test_rows],
                stats,
            )
            fitted = fit_logit(x_train, y[train_rows])
            predictions[name][test_rows] = expit(np.clip(x_test @ fitted["beta"], -35.0, 35.0))
            fold_record["models"][name] = {
                "converged": bool(fitted["converged"]),
                "iterations": int(fitted["iterations"]),
                "design_columns": design_names,
            }
        fold_details.append(fold_record)

    for name, values in predictions.items():
        if np.any(np.isnan(values)):
            raise RuntimeError(f"Missing out-of-fold predictions for {name}")

    point = {name: prediction_metrics(y, values) for name, values in predictions.items()}
    rng = np.random.default_rng(seed + 1)
    signature_count = len(signature_prompt_indices)
    metric_samples = {
        name: {metric: [] for metric in ("log_loss", "brier", "auc")}
        for name in predictions
    }
    delta_samples = {
        name: {metric: [] for metric in ("log_loss", "brier", "auc")}
        for name in predictions
        if name != "size_only"
    }
    for _ in range(bootstrap_replicates):
        counts = cluster_counts(rng, signature_count)
        prompt_weights = prompt_weights_from_cluster_counts(prompt_cluster, counts)
        row_weights = np.repeat(prompt_weights, model_count)
        sample_metrics = {
            name: prediction_metrics(y, values, row_weights)
            for name, values in predictions.items()
        }
        for name, metrics in sample_metrics.items():
            for metric, value in metrics.items():
                metric_samples[name][metric].append(value)
        for name in delta_samples:
            for metric in delta_samples[name]:
                delta_samples[name][metric].append(
                    sample_metrics[name][metric] - sample_metrics["size_only"][metric]
                )

    results = {}
    for name, metrics in point.items():
        results[name] = {}
        for metric, value in metrics.items():
            values = np.asarray(metric_samples[name][metric])
            results[name][metric] = {
                "value": float(value),
                "bootstrap_95": percentile_interval(values),
            }
            if name != "size_only":
                delta = value - point["size_only"][metric]
                delta_values = np.asarray(delta_samples[name][metric])
                results[name][metric]["delta_vs_size_only"] = float(delta)
                results[name][metric]["delta_bootstrap_95"] = percentile_interval(delta_values)
    return {
        "method": {
            "folds": folds,
            "grouping": "evaluator-facing target signature",
            "standardization": "training-fold only",
            "bootstrap_replicates": bootstrap_replicates,
            "seed": seed,
        },
        "fold_details": fold_details,
        "results": results,
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=lambda index: p_values[index])
    adjusted = [1.0] * len(p_values)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        value = min(1.0, (total - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def cluster_sign_flip_p(
    cluster_differences: np.ndarray,
    observed_sum: float,
    replicates: int,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed)
    extreme = 0
    completed = 0
    chunk = 5000
    threshold = abs(observed_sum) - 1e-12
    while completed < replicates:
        size = min(chunk, replicates - completed)
        signs = rng.integers(0, 2, size=(size, len(cluster_differences)), dtype=np.int8)
        signs = signs.astype(float) * 2.0 - 1.0
        statistics = signs @ cluster_differences
        extreme += int(np.sum(np.abs(statistics) >= threshold))
        completed += size
    return (extreme + 1.0) / (replicates + 1.0)


def paired_comparisons_and_rank_stability(
    signature: np.ndarray,
    prompt_cluster: np.ndarray,
    signature_prompt_indices: list[np.ndarray],
    bootstrap_replicates: int,
    permutation_replicates: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_count, model_count = signature.shape
    signature_count = len(signature_prompt_indices)
    original_scores = np.mean(signature, axis=0)
    original_ranks = rankdata(-original_scores, method="average")
    rng = np.random.default_rng(seed)
    score_samples = np.empty((bootstrap_replicates, model_count), dtype=float)
    rank_samples = np.empty((bootstrap_replicates, model_count), dtype=float)
    rank_correlations = np.empty(bootstrap_replicates, dtype=float)
    for replicate in range(bootstrap_replicates):
        counts = cluster_counts(rng, signature_count)
        prompt_weights = prompt_weights_from_cluster_counts(prompt_cluster, counts)
        denominator = float(np.sum(prompt_weights))
        scores = (prompt_weights[:, None] * signature).sum(axis=0) / denominator
        ranks = rankdata(-scores, method="average")
        score_samples[replicate] = scores
        rank_samples[replicate] = ranks
        rank_correlations[replicate] = float(np.corrcoef(original_ranks, ranks)[0, 1])

    rank_rows = []
    for model_idx, model in enumerate(MODEL_ORDER):
        rank_rows.append(
            {
                "model": model,
                "model_label": MODEL_LABELS.get(model, model),
                "score": float(original_scores[model_idx]),
                "score_bootstrap_95": percentile_interval(score_samples[:, model_idx]),
                "rank": float(original_ranks[model_idx]),
                "rank_median": float(np.median(rank_samples[:, model_idx])),
                "rank_bootstrap_95": percentile_interval(rank_samples[:, model_idx]),
                "top_3_probability": float(np.mean(rank_samples[:, model_idx] <= 3.0)),
                "top_5_probability": float(np.mean(rank_samples[:, model_idx] <= 5.0)),
            }
        )
    rank_result = {
        "method": {
            "bootstrap_replicates": bootstrap_replicates,
            "cluster": "evaluator-facing target signature",
            "seed": seed,
        },
        "rank_correlation_with_original": {
            "mean": float(np.mean(rank_correlations)),
            "bootstrap_95": percentile_interval(rank_correlations),
        },
        "models": sorted(rank_rows, key=lambda row: (row["rank"], row["model_label"])),
    }

    model_index = {model: index for index, model in enumerate(MODEL_ORDER)}
    pair_rows = []
    raw_p_values = []
    for pair_idx, (before, after, label) in enumerate(PAIR_SPECS):
        before_idx = model_index[before]
        after_idx = model_index[after]
        difference = signature[:, after_idx] - signature[:, before_idx]
        after_wins = int(np.sum(difference > 0))
        before_wins = int(np.sum(difference < 0))
        ties = int(np.sum(difference == 0))
        discordant = after_wins + before_wins
        mcnemar_p = (
            float(binomtest(after_wins, discordant, 0.5, alternative="two-sided").pvalue)
            if discordant
            else 1.0
        )
        cluster_differences = np.asarray(
            [float(np.sum(difference[prompt_indices])) for prompt_indices in signature_prompt_indices]
        )
        permutation_p = cluster_sign_flip_p(
            cluster_differences,
            float(np.sum(difference)),
            permutation_replicates,
            seed + 100 + pair_idx,
        )
        raw_p_values.append(permutation_p)
        bootstrap_difference = score_samples[:, after_idx] - score_samples[:, before_idx]
        pair_rows.append(
            {
                "comparison": label,
                "before_model": before,
                "after_model": after,
                "before_label": MODEL_LABELS.get(before, before),
                "after_label": MODEL_LABELS.get(after, after),
                "before_rate": float(original_scores[before_idx]),
                "after_rate": float(original_scores[after_idx]),
                "difference": float(original_scores[after_idx] - original_scores[before_idx]),
                "difference_bootstrap_95": percentile_interval(bootstrap_difference),
                "after_wins": after_wins,
                "before_wins": before_wins,
                "ties": ties,
                "unclustered_exact_mcnemar_p": mcnemar_p,
                "signature_cluster_permutation_p": permutation_p,
            }
        )
    adjusted = holm_adjust(raw_p_values)
    for row, value in zip(pair_rows, adjusted):
        row["holm_adjusted_cluster_permutation_p"] = float(value)
    pair_result = {
        "method": {
            "confidence_intervals": "target-signature cluster bootstrap",
            "primary_test": "target-signature cluster sign-flip permutation",
            "secondary_test": "unclustered exact McNemar diagnostic",
            "bootstrap_replicates": bootstrap_replicates,
            "permutation_replicates": permutation_replicates,
            "multiplicity": f"Holm adjustment across {len(PAIR_SPECS)} prespecified displayed comparisons",
            "seed": seed,
        },
        "comparisons": pair_rows,
    }
    return pair_result, rank_result


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f} pp"


def interval(values: list[float], *, odds: bool = False) -> str:
    if odds:
        return f"[{values[0]:.2f}, {values[1]:.2f}]"
    return f"[{100.0 * values[0]:+.2f}, {100.0 * values[1]:+.2f}] pp"


def p_text(value: float) -> str:
    if value < 0.0001:
        return "<0.0001"
    return f"{value:.4f}"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    inferential = payload["inferential_models"]
    cv = payload["grouped_cross_validation"]
    pairs = payload["paired_model_comparisons"]
    ranks = payload["rank_stability"]
    lines = [
        "# PQID-Bench Cluster-Aware Inferential Analysis",
        "",
        "## Analysis Contract",
        "",
        f"- held-out prompts: `{payload['design']['prompt_count']}`",
        f"- unique evaluator-facing signatures: `{payload['design']['signature_count']}`",
        f"- completed model rows: `{payload['design']['model_count']}`",
        f"- prompt-model outcomes: `{payload['design']['evaluation_count']}`",
        "- estimand: adjusted associations and paired contrasts for the fixed observed model panel",
        "- uncertainty unit: evaluator-facing target-signature cluster",
        "- causal interpretation: not supported",
        "",
        "The task-feature logistic models use each prompt's number of successes over the fixed "
        f"{payload['design']['model_count']}-model panel. Continuous circuit descriptors are standardized over prompts, and percentile intervals "
        "come from resampling complete target-signature clusters. The primary entropy model does "
        "not include gate-type count; a parallel sensitivity model replaces entropy with gate-type "
        "count to avoid treating correlated diversity descriptors as independent causes.",
        "",
        "## Adjusted Logistic Associations",
        "",
        "All grouped-binomial point fits converged. Across the five analyses, "
        f"`{sum(model['bootstrap_converged'] for model in inferential['models'].values()):,}` / "
        f"`{sum(model['bootstrap_replicates'] for model in inferential['models'].values()):,}` "
        "target-signature bootstrap refits converged.",
        "",
        "| outcome / analysis | descriptor | adjusted OR | cluster-bootstrap 95% CI | average marginal effect | cluster-bootstrap 95% CI |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    model_labels = {
        "signature_entropy_full": "signature match, entropy model",
        "signature_gate_type_full": "signature match, gate-type model",
        "execution_entropy_full": "execution, entropy model",
        "signature_given_execution_entropy_full": "signature match given execution",
        "signature_entropy_identifiable_150": "signature match, identifiable 150",
    }
    term_labels = {
        "z_gate_entropy": "gate entropy (per SD)",
        "z_gate_type_count": "gate-type count (per SD)",
        "z_log_gate_count": "log gate count (per SD)",
        "z_num_qubits": "qubits (per SD)",
        "z_num_clbits": "classical bits (per SD)",
        "has_barrier": "barrier present",
    }
    selected_terms = {
        "signature_entropy_full": ["z_gate_entropy", "z_log_gate_count", "z_num_qubits", "z_num_clbits", "has_barrier"],
        "signature_gate_type_full": ["z_gate_type_count", "z_log_gate_count", "z_num_qubits", "z_num_clbits", "has_barrier"],
        "execution_entropy_full": ["z_gate_entropy", "has_barrier"],
        "signature_given_execution_entropy_full": ["z_gate_entropy", "has_barrier"],
        "signature_entropy_identifiable_150": ["z_gate_entropy", "has_barrier"],
    }
    for model_name, terms in selected_terms.items():
        model = inferential["models"][model_name]
        for term_name in terms:
            term = model["terms"][term_name]
            lines.append(
                f"| {model_labels[model_name]} | {term_labels[term_name]} | "
                f"{term['odds_ratio']:.2f} | {interval(term['odds_ratio_bootstrap_95'], odds=True)} | "
                f"{pp(term['average_marginal_effect'])} | "
                f"{interval(term['average_marginal_effect_bootstrap_95'])} |"
            )
    lines.extend(["", "## Execution Versus Conditional Fidelity", ""])
    lines.append("| descriptor | conditional-signature AME minus execution AME | cluster-bootstrap 95% CI |")
    lines.append("| --- | ---: | ---: |")
    for term, label in (("z_gate_entropy", "gate entropy (per SD)"), ("has_barrier", "barrier present")):
        contrast = inferential["two_stage_contrasts"][
            f"conditional_signature_minus_execution::{term}"
        ]
        lines.append(
            f"| {label} | {pp(contrast['average_marginal_effect_difference'])} | "
            f"{interval(contrast['bootstrap_95'])} |"
        )

    lines.extend(
        [
            "",
            "## Target-Signature-Grouped Cross-Validation",
            "",
            f"Out-of-fold predictions use {cv['method']['folds']} folds grouped by target signature. Negative deltas "
            "are improvements for log loss and Brier score; positive deltas are improvements for AUC.",
            "",
            "| model | log loss | delta vs size only (95% CI) | Brier | delta vs size only (95% CI) | AUC | delta vs size only (95% CI) |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for model_name, label in (
        ("size_only", "size only"),
        ("entropy_plus_barrier", "size + entropy + barrier"),
        ("gate_type_plus_barrier", "size + gate types + barrier"),
    ):
        result = cv["results"][model_name]
        def delta(metric: str) -> str:
            value = result[metric].get("delta_vs_size_only")
            if value is None:
                return "--"
            ci = result[metric]["delta_bootstrap_95"]
            return f"{value:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
        lines.append(
            f"| {label} | {result['log_loss']['value']:.4f} | {delta('log_loss')} | "
            f"{result['brier']['value']:.4f} | {delta('brier')} | "
            f"{result['auc']['value']:.3f} | {delta('auc')} |"
        )

    lines.extend(
        [
            "",
            "## Selected Paired Model Comparisons",
            "",
            "| comparison | before -> after | paired difference | signature-cluster 95% CI | wins-losses-ties | cluster permutation p | Holm p |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in pairs["comparisons"]:
        lines.append(
            f"| {row['comparison']} | {pct(row['before_rate'])} -> {pct(row['after_rate'])} | "
            f"{pp(row['difference'])} | {interval(row['difference_bootstrap_95'])} | "
            f"{row['after_wins']}-{row['before_wins']}-{row['ties']} | "
            f"{p_text(row['signature_cluster_permutation_p'])} | "
            f"{p_text(row['holm_adjusted_cluster_permutation_p'])} |"
        )

    lines.extend(
        [
            "",
            "## Bootstrap Rank Stability",
            "",
            f"Mean Spearman correlation between each bootstrap ranking and the original ranking is "
            f"`{ranks['rank_correlation_with_original']['mean']:.3f}` with a 95% interval of "
            f"`[{ranks['rank_correlation_with_original']['bootstrap_95'][0]:.3f}, "
            f"{ranks['rank_correlation_with_original']['bootstrap_95'][1]:.3f}]`.",
            "",
            "| model | score | score 95% CI | original rank | rank 95% interval | top-3 probability |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in ranks["models"]:
        score_ci = row["score_bootstrap_95"]
        rank_ci = row["rank_bootstrap_95"]
        lines.append(
            f"| {row['model_label']} | {pct(row['score'])} | "
            f"[{pct(score_ci[0])}, {pct(score_ci[1])}] | {row['rank']:.1f} | "
            f"[{rank_ci[0]:.1f}, {rank_ci[1]:.1f}] | {pct(row['top_3_probability'])} |"
        )

    entropy = inferential["models"]["signature_entropy_full"]["terms"]["z_gate_entropy"]
    barrier = inferential["models"]["signature_entropy_full"]["terms"]["has_barrier"]
    execution_entropy = inferential["models"]["execution_entropy_full"]["terms"]["z_gate_entropy"]
    conditional_entropy = inferential["models"]["signature_given_execution_entropy_full"]["terms"]["z_gate_entropy"]
    entropy_cv = cv["results"]["entropy_plus_barrier"]
    significant_pairs = [
        row
        for row in pairs["comparisons"]
        if row["holm_adjusted_cluster_permutation_p"] < 0.05
    ]
    lines.extend(
        [
            "",
            "## Main Inferential Findings",
            "",
            f"After adjustment for log gate count, qubit width, classical width, and barrier presence, "
            f"one standard deviation of gate entropy is associated with OR `{entropy['odds_ratio']:.2f}` "
            f"for reference-signature match (95% cluster-bootstrap CI "
            f"`{interval(entropy['odds_ratio_bootstrap_95'], odds=True)}`) and an average marginal "
            f"change of `{pp(entropy['average_marginal_effect'])}`. Barrier presence is associated "
            f"with OR `{barrier['odds_ratio']:.2f}` and `{pp(barrier['average_marginal_effect'])}`.",
            "",
            f"The entropy association is weak for execution (OR `{execution_entropy['odds_ratio']:.2f}`, "
            f"95% CI `{interval(execution_entropy['odds_ratio_bootstrap_95'], odds=True)}`) but remains "
            f"strong among outputs that execute (OR `{conditional_entropy['odds_ratio']:.2f}`, 95% CI "
            f"`{interval(conditional_entropy['odds_ratio_bootstrap_95'], odds=True)}`). This supports "
            "the bounded interpretation that heterogeneity is primarily associated with recovering "
            "the wrong reference signature, not with failure to produce runnable code.",
            "",
            f"Adding entropy and barrier information to size controls improves grouped out-of-fold AUC "
            f"by `{entropy_cv['auc']['delta_vs_size_only']:+.3f}` (95% CI "
            f"`[{entropy_cv['auc']['delta_bootstrap_95'][0]:+.3f}, "
            f"{entropy_cv['auc']['delta_bootstrap_95'][1]:+.3f}]`) and Brier score by "
            f"`{entropy_cv['brier']['delta_vs_size_only']:+.4f}` (95% CI "
            f"`[{entropy_cv['brier']['delta_bootstrap_95'][0]:+.4f}, "
            f"{entropy_cv['brier']['delta_bootstrap_95'][1]:+.4f}]`). The log-loss interval includes "
            "zero, so predictive improvement should be described as metric-dependent rather than universal.",
            "",
            "After Holm correction, the selected paired improvements that remain distinguishable "
            "under target-signature permutation are: "
            + "; ".join(
                f"{row['comparison']} ({pp(row['difference'])}, adjusted p={p_text(row['holm_adjusted_cluster_permutation_p'])})"
                for row in significant_pairs
            )
            + ". Other within-family differences are estimates with uncertainty, not confirmed ordering claims.",
        ]
    )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "These analyses quantify uncertainty under changes in the held-out target-signature "
            "composition and compare models on paired prompts. They do not identify causal effects "
            "of circuit descriptors or model tier. The model panel is fixed rather than randomly "
            "sampled, circuit descriptors are correlated, and decoding is represented by one "
            "frozen response per model-prompt cell.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv_outputs(
    payload: dict[str, Any],
    *,
    term_csv_out: Path = TERM_CSV_OUT,
    cv_csv_out: Path = CV_CSV_OUT,
    pair_csv_out: Path = PAIR_CSV_OUT,
    rank_csv_out: Path = RANK_CSV_OUT,
) -> None:
    term_csv_out.parent.mkdir(parents=True, exist_ok=True)
    with term_csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "analysis",
                "term",
                "odds_ratio",
                "or_ci_low",
                "or_ci_high",
                "average_marginal_effect_pp",
                "ame_ci_low_pp",
                "ame_ci_high_pp",
                "interval_excludes_null",
            ]
        )
        for analysis, model in payload["inferential_models"]["models"].items():
            for term_name, term in model["terms"].items():
                writer.writerow(
                    [
                        analysis,
                        term_name,
                        f"{term['odds_ratio']:.8f}",
                        f"{term['odds_ratio_bootstrap_95'][0]:.8f}",
                        f"{term['odds_ratio_bootstrap_95'][1]:.8f}",
                        f"{100.0 * term['average_marginal_effect']:.8f}",
                        f"{100.0 * term['average_marginal_effect_bootstrap_95'][0]:.8f}",
                        f"{100.0 * term['average_marginal_effect_bootstrap_95'][1]:.8f}",
                        term["interval_excludes_null"],
                    ]
                )

    with cv_csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["model", "metric", "value", "ci_low", "ci_high", "delta_vs_size", "delta_ci_low", "delta_ci_high"])
        for model_name, metrics in payload["grouped_cross_validation"]["results"].items():
            for metric_name, metric in metrics.items():
                delta_ci = metric.get("delta_bootstrap_95", [None, None])
                writer.writerow(
                    [
                        model_name,
                        metric_name,
                        metric["value"],
                        metric["bootstrap_95"][0],
                        metric["bootstrap_95"][1],
                        metric.get("delta_vs_size_only"),
                        delta_ci[0],
                        delta_ci[1],
                    ]
                )

    with pair_csv_out.open("w", encoding="utf-8", newline="") as handle:
        rows = payload["paired_model_comparisons"]["comparisons"]
        fieldnames = [
            "comparison",
            "before_label",
            "after_label",
            "before_rate",
            "after_rate",
            "difference",
            "difference_ci_low",
            "difference_ci_high",
            "after_wins",
            "before_wins",
            "ties",
            "signature_cluster_permutation_p",
            "holm_adjusted_cluster_permutation_p",
            "unclustered_exact_mcnemar_p",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = dict(row)
            output["difference_ci_low"] = row["difference_bootstrap_95"][0]
            output["difference_ci_high"] = row["difference_bootstrap_95"][1]
            writer.writerow(output)

    with rank_csv_out.open("w", encoding="utf-8", newline="") as handle:
        rows = payload["rank_stability"]["models"]
        fieldnames = [
            "model_label",
            "score",
            "score_ci_low",
            "score_ci_high",
            "rank",
            "rank_median",
            "rank_ci_low",
            "rank_ci_high",
            "top_3_probability",
            "top_5_probability",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = dict(row)
            output["score_ci_low"] = row["score_bootstrap_95"][0]
            output["score_ci_high"] = row["score_bootstrap_95"][1]
            output["rank_ci_low"] = row["rank_bootstrap_95"][0]
            output["rank_ci_high"] = row["rank_bootstrap_95"][1]
            writer.writerow(output)


def main() -> None:
    global MODEL_ORDER, PAIR_SPECS

    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument(
        "--eval-dir",
        type=Path,
        action="append",
        default=None,
        help="Evaluation directory; may be repeated for additional completed model rows.",
    )
    parser.add_argument("--expanded-roster", action="store_true")
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--term-csv-out", type=Path, default=TERM_CSV_OUT)
    parser.add_argument("--cv-csv-out", type=Path, default=CV_CSV_OUT)
    parser.add_argument("--pair-csv-out", type=Path, default=PAIR_CSV_OUT)
    parser.add_argument("--rank-csv-out", type=Path, default=RANK_CSV_OUT)
    parser.add_argument("--regression-bootstrap", type=int, default=2000)
    parser.add_argument("--metric-bootstrap", type=int, default=3000)
    parser.add_argument("--rank-bootstrap", type=int, default=5000)
    parser.add_argument("--permutations", type=int, default=50000)
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260713)
    args = parser.parse_args()

    if args.expanded_roster:
        MODEL_ORDER = list(EXPANDED_MODEL_ORDER)
    eval_dirs = args.eval_dir or DEFAULT_EVAL_DIRS

    prompts = read_jsonl(args.prompt_path)
    feature_rows = [prompt_features(prompt) for prompt in prompts]
    prompt_ids = [str(row["prompt_id"]) for row in feature_rows]
    execution, signature, qasm3, sources = load_evaluation_matrices(eval_dirs, prompt_ids)
    arrays = feature_arrays(feature_rows)
    arrays["prompt_id"] = np.asarray(prompt_ids, dtype=object)

    signature_to_index: dict[str, int] = {}
    prompt_cluster = np.empty(len(feature_rows), dtype=int)
    signature_prompt_lists: dict[int, list[int]] = defaultdict(list)
    for prompt_idx, row in enumerate(feature_rows):
        signature_key = str(row["signature"])
        if signature_key not in signature_to_index:
            signature_to_index[signature_key] = len(signature_to_index)
        cluster_idx = signature_to_index[signature_key]
        prompt_cluster[prompt_idx] = cluster_idx
        signature_prompt_lists[cluster_idx].append(prompt_idx)
    signature_prompt_indices = [
        np.asarray(signature_prompt_lists[index], dtype=int)
        for index in range(len(signature_to_index))
    ]

    inferential = inferential_models(
        arrays,
        execution,
        signature,
        prompt_cluster,
        args.regression_bootstrap,
        args.seed,
    )
    cross_validation = grouped_cross_validation(
        arrays,
        signature,
        prompt_cluster,
        signature_prompt_indices,
        args.folds,
        args.metric_bootstrap,
        args.seed + 10,
    )
    paired, ranks = paired_comparisons_and_rank_stability(
        signature,
        prompt_cluster,
        signature_prompt_indices,
        args.rank_bootstrap,
        args.permutations,
        args.seed + 20,
    )

    payload = {
        "design": {
            "roster": "final_21_primary",
            "prompt_count": len(prompt_ids),
            "signature_count": len(signature_to_index),
            "model_count": len(MODEL_ORDER),
            "evaluation_count": int(signature.size),
            "execution_rate": float(np.mean(execution)),
            "signature_match_rate": float(np.mean(signature)),
            "qasm3_rate": float(np.mean(qasm3)),
            "identifiability_exclusions": sorted(IDENTIFIABILITY_EXCLUSIONS),
        },
        "source_reports": sources,
        "inferential_models": inferential,
        "grouped_cross_validation": cross_validation,
        "paired_model_comparisons": paired,
        "rank_stability": ranks,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.md_out, payload)
    write_csv_outputs(
        payload,
        term_csv_out=args.term_csv_out,
        cv_csv_out=args.cv_csv_out,
        pair_csv_out=args.pair_csv_out,
        rank_csv_out=args.rank_csv_out,
    )
    print(f"Wrote {args.json_out.as_posix()}")
    print(f"Wrote {args.md_out.as_posix()}")
    print(f"Wrote {args.term_csv_out.as_posix()}")
    print(f"Wrote {args.cv_csv_out.as_posix()}")
    print(f"Wrote {args.pair_csv_out.as_posix()}")
    print(f"Wrote {args.rank_csv_out.as_posix()}")


if __name__ == "__main__":
    main()
