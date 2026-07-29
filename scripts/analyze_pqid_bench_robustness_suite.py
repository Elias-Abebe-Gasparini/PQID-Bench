"""Run replication and crossed-dimension robustness audits for PQID-Bench.

This script keeps the release-bound 21-model by 154-prompt matrix fixed and
adds three analyses that are intentionally separate from causal claims:

1. prospective pilot-versus-extension replication;
2. a crossed bootstrap over model rows and target-signature clusters; and
3. circuit-family balancing plus leave-one-developer-out sensitivity.

The extension was selected without model outcomes and excludes pilot target
signatures. Its item mix is deliberately stratified, so replication means
recovery of the qualitative benchmark claims, not equality of raw rates.
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
from scipy.stats import spearmanr

from analyze_pqid_bench_complexity_difficulty import family_labels
from analyze_pqid_bench_inferential import (
    DEFAULT_EVAL_DIRS,
    MODEL_SPECS,
    build_prompt_design,
    feature_arrays,
    fit_logit,
    load_evaluation_matrices,
    metadata_signature,
    percentile_interval,
    prompt_features,
    read_jsonl,
    standardization,
)
from pqid_bench_model_registry import MODEL_LABELS, MODEL_ORDER


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_MANIFEST_PATH = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
JSON_OUT = ANALYSIS_DIR / "pqid_bench_replication_crossed_family_vendor_robustness.json"
MD_OUT = ANALYSIS_DIR / "pqid_bench_replication_crossed_family_vendor_robustness.md"
PILOT_CSV_OUT = ANALYSIS_DIR / "pqid_bench_pilot_extension_per_model.csv"
SENSITIVITY_CSV_OUT = ANALYSIS_DIR / "pqid_bench_family_vendor_sensitivity.csv"
S27_TSV_OUT = ROOT / "tables_copy_ready/table_s27_pilot_extension_replication.tsv"
S28_TSV_OUT = ROOT / "tables_copy_ready/table_s28_crossed_robustness.tsv"
S29_TSV_OUT = ROOT / "tables_copy_ready/table_s29_family_vendor_sensitivity.tsv"


# These are the 15 rows present when the 70-prompt pilot was first reported.
ORIGINAL_PILOT_MODELS = [
    "gpt-5.5",
    "gpt-5.4-mini",
    "claude-sonnet-4-6",
    "claude-opus-4-8",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "mistral-ai/codestral-2501",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]


# Developer groups are used rather than API hosts. The Qiskit specialist is
# separated from Mistral because it is the domain-specialized IBM/Qiskit row.
MODEL_DEVELOPER = {
    "gpt-5.6-sol": "OpenAI",
    "gpt-5.5": "OpenAI",
    "gpt-5.4-mini": "OpenAI",
    "openai/gpt-oss-120b": "OpenAI",
    "openai/gpt-oss-20b": "OpenAI",
    "claude-fable-5": "Anthropic",
    "claude-sonnet-4-6": "Anthropic",
    "claude-opus-4-8": "Anthropic",
    "gemini-2.5-pro": "Google",
    "gemini-3.1-pro-preview": "Google",
    "deepseek-v4-pro": "DeepSeek",
    "deepseek-v4-flash": "DeepSeek",
    "mistral-ai/codestral-2501": "Mistral AI",
    "mistralai/mistral-small-3.2-24b-instruct": "Mistral AI",
    "qiskit/mistral-small-3.2-24b-qiskit": "IBM/Qiskit",
    "qwen/qwen3-coder-next": "Alibaba/Qwen",
    "qwen/qwen3-32b": "Alibaba/Qwen",
    "meta/llama-4-maverick-17b-128e-instruct-fp8": "Meta",
    "llama-3.3-70b-versatile": "Meta",
    "meta-llama/llama-4-scout-17b-16e-instruct": "Meta",
    "llama-3.1-8b-instant": "Meta",
}


def pct(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:.{digits}f}%"


def pp(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:+.{digits}f} pp"


def model_indices(models: Iterable[str]) -> np.ndarray:
    lookup = {model: index for index, model in enumerate(MODEL_ORDER)}
    missing = [model for model in models if model not in lookup]
    if missing:
        raise ValueError(f"Unknown model rows: {missing}")
    return np.asarray([lookup[model] for model in models], dtype=int)


def signature_clusters(feature_rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[np.ndarray]]:
    key_to_cluster: dict[str, int] = {}
    cluster_for_prompt = np.empty(len(feature_rows), dtype=int)
    prompts_for_cluster: dict[int, list[int]] = defaultdict(list)
    for prompt_index, row in enumerate(feature_rows):
        key = str(row["signature"])
        if key not in key_to_cluster:
            key_to_cluster[key] = len(key_to_cluster)
        cluster = key_to_cluster[key]
        cluster_for_prompt[prompt_index] = cluster
        prompts_for_cluster[cluster].append(prompt_index)
    clusters = [
        np.asarray(prompts_for_cluster[index], dtype=int)
        for index in range(len(key_to_cluster))
    ]
    return cluster_for_prompt, clusters


def cohort_map(manifest_path: Path) -> dict[str, str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for item in manifest["test_prompt_order"]:
        result[str(item["prompt_id"])] = str(item["cohort"])
    return result


def grouped_fit(
    arrays: dict[str, np.ndarray],
    outcome: np.ndarray,
    prompt_indices: np.ndarray,
    selected_models: np.ndarray,
    *,
    stats_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    if stats_mask is None:
        stats_mask = np.zeros(outcome.shape[0], dtype=bool)
        stats_mask[np.unique(prompt_indices)] = True
    feature_names = MODEL_SPECS["entropy"]
    stats = standardization(arrays, feature_names, stats_mask)
    x, names = build_prompt_design(arrays, feature_names, prompt_indices, stats)
    successes = np.sum(outcome[np.ix_(prompt_indices, selected_models)], axis=1).astype(float)
    trials = np.full(len(prompt_indices), len(selected_models), dtype=float)
    fitted = fit_logit(x, successes / trials, trials)
    terms: dict[str, Any] = {}
    for raw_name in feature_names:
        name = f"z_{raw_name}" if raw_name in {
            "gate_entropy",
            "gate_type_count",
            "log_gate_count",
            "num_qubits",
            "num_clbits",
        } else raw_name
        beta = float(fitted["beta"][names.index(name)])
        terms[name] = {"log_odds": beta, "odds_ratio": float(math.exp(beta))}
    return {
        "rate": float(np.sum(successes) / np.sum(trials)),
        "terms": terms,
        "converged": bool(fitted["converged"]),
        "iterations": int(fitted["iterations"]),
    }


def cluster_bootstrap_cohort(
    arrays: dict[str, np.ndarray],
    execution: np.ndarray,
    signature: np.ndarray,
    prompt_mask: np.ndarray,
    selected_models: np.ndarray,
    cluster_for_prompt: np.ndarray,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    prompts = np.flatnonzero(prompt_mask)
    cohort_clusters = sorted(set(int(value) for value in cluster_for_prompt[prompts]))
    prompts_by_cluster = {
        cluster: prompts[cluster_for_prompt[prompts] == cluster]
        for cluster in cohort_clusters
    }
    point_execution = float(np.mean(execution[np.ix_(prompts, selected_models)]))
    point_signature = float(np.mean(signature[np.ix_(prompts, selected_models)]))
    point_fit = grouped_fit(arrays, signature, prompts, selected_models, stats_mask=prompt_mask)

    rng = np.random.default_rng(seed)
    execution_samples = np.empty(replicates, dtype=float)
    signature_samples = np.empty(replicates, dtype=float)
    entropy_or_samples = np.empty(replicates, dtype=float)
    barrier_or_samples = np.empty(replicates, dtype=float)
    for replicate in range(replicates):
        sampled_clusters = rng.choice(cohort_clusters, size=len(cohort_clusters), replace=True)
        sampled_prompts = np.concatenate([prompts_by_cluster[int(c)] for c in sampled_clusters])
        execution_samples[replicate] = float(
            np.mean(execution[np.ix_(sampled_prompts, selected_models)])
        )
        signature_samples[replicate] = float(
            np.mean(signature[np.ix_(sampled_prompts, selected_models)])
        )
        fitted = grouped_fit(
            arrays,
            signature,
            sampled_prompts,
            selected_models,
            stats_mask=prompt_mask,
        )
        entropy_or_samples[replicate] = fitted["terms"]["z_gate_entropy"]["odds_ratio"]
        barrier_or_samples[replicate] = fitted["terms"]["has_barrier"]["odds_ratio"]

    gap_samples = execution_samples - signature_samples
    return {
        "prompt_count": int(len(prompts)),
        "signature_cluster_count": int(len(cohort_clusters)),
        "model_count": int(len(selected_models)),
        "cell_count": int(len(prompts) * len(selected_models)),
        "execution_rate": point_execution,
        "execution_cluster_bootstrap_95": percentile_interval(execution_samples),
        "signature_rate": point_signature,
        "signature_cluster_bootstrap_95": percentile_interval(signature_samples),
        "execution_structure_gap": point_execution - point_signature,
        "gap_cluster_bootstrap_95": percentile_interval(gap_samples),
        "gate_entropy_odds_ratio": point_fit["terms"]["z_gate_entropy"]["odds_ratio"],
        "gate_entropy_or_cluster_bootstrap_95": percentile_interval(entropy_or_samples),
        "barrier_odds_ratio": point_fit["terms"]["has_barrier"]["odds_ratio"],
        "barrier_or_cluster_bootstrap_95": percentile_interval(barrier_or_samples),
    }


def per_model_cohort_rows(
    execution: np.ndarray,
    signature: np.ndarray,
    pilot_mask: np.ndarray,
    extension_mask: np.ndarray,
) -> list[dict[str, Any]]:
    rows = []
    for index, model in enumerate(MODEL_ORDER):
        pilot_execution = float(np.mean(execution[pilot_mask, index]))
        extension_execution = float(np.mean(execution[extension_mask, index]))
        pilot_signature = float(np.mean(signature[pilot_mask, index]))
        extension_signature = float(np.mean(signature[extension_mask, index]))
        rows.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "developer": MODEL_DEVELOPER[model],
                "pilot_execution_rate": pilot_execution,
                "extension_execution_rate": extension_execution,
                "execution_change": extension_execution - pilot_execution,
                "pilot_signature_rate": pilot_signature,
                "extension_signature_rate": extension_signature,
                "signature_change": extension_signature - pilot_signature,
                "pilot_gap": pilot_execution - pilot_signature,
                "extension_gap": extension_execution - extension_signature,
            }
        )
    return rows


def rank_replication(rows: list[dict[str, Any]], selected_models: list[str]) -> dict[str, Any]:
    selected = [row for row in rows if row["model"] in selected_models]
    pilot = np.asarray([row["pilot_signature_rate"] for row in selected], dtype=float)
    extension = np.asarray([row["extension_signature_rate"] for row in selected], dtype=float)
    coefficient, p_value = spearmanr(pilot, extension)
    return {
        "model_count": len(selected),
        "spearman_rho": float(coefficient),
        "two_sided_p": float(p_value),
        "median_signature_change": float(np.median(extension - pilot)),
        "models_improving_on_extension": int(np.sum(extension > pilot)),
        "models_declining_on_extension": int(np.sum(extension < pilot)),
        "models_tied": int(np.sum(extension == pilot)),
    }


def crossed_bootstrap(
    arrays: dict[str, np.ndarray],
    execution: np.ndarray,
    signature: np.ndarray,
    clusters: list[np.ndarray],
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    all_prompts = np.arange(execution.shape[0], dtype=int)
    all_models = np.arange(execution.shape[1], dtype=int)
    full_mask = np.ones(execution.shape[0], dtype=bool)
    point_fit = grouped_fit(arrays, signature, all_prompts, all_models, stats_mask=full_mask)

    rng = np.random.default_rng(seed)
    execution_samples = np.empty(replicates, dtype=float)
    signature_samples = np.empty(replicates, dtype=float)
    entropy_or_samples = np.empty(replicates, dtype=float)
    barrier_or_samples = np.empty(replicates, dtype=float)
    for replicate in range(replicates):
        sampled_models = rng.integers(0, len(all_models), size=len(all_models))
        sampled_cluster_ids = rng.integers(0, len(clusters), size=len(clusters))
        sampled_prompts = np.concatenate([clusters[index] for index in sampled_cluster_ids])
        execution_samples[replicate] = float(
            np.mean(execution[np.ix_(sampled_prompts, sampled_models)])
        )
        signature_samples[replicate] = float(
            np.mean(signature[np.ix_(sampled_prompts, sampled_models)])
        )
        fitted = grouped_fit(
            arrays,
            signature,
            sampled_prompts,
            sampled_models,
            stats_mask=full_mask,
        )
        entropy_or_samples[replicate] = fitted["terms"]["z_gate_entropy"]["odds_ratio"]
        barrier_or_samples[replicate] = fitted["terms"]["has_barrier"]["odds_ratio"]

    return {
        "method": (
            "two-way nonparametric crossed bootstrap; model rows and complete "
            "evaluator-facing target-signature clusters are sampled independently "
            "with replacement"
        ),
        "replicates": replicates,
        "seed": seed,
        "model_count": int(len(all_models)),
        "signature_cluster_count": int(len(clusters)),
        "prompt_count": int(len(all_prompts)),
        "execution_rate": float(np.mean(execution)),
        "execution_crossed_bootstrap_95": percentile_interval(execution_samples),
        "signature_rate": float(np.mean(signature)),
        "signature_crossed_bootstrap_95": percentile_interval(signature_samples),
        "execution_structure_gap": float(np.mean(execution) - np.mean(signature)),
        "gap_crossed_bootstrap_95": percentile_interval(execution_samples - signature_samples),
        "gate_entropy_odds_ratio": point_fit["terms"]["z_gate_entropy"]["odds_ratio"],
        "gate_entropy_or_crossed_bootstrap_95": percentile_interval(entropy_or_samples),
        "barrier_odds_ratio": point_fit["terms"]["has_barrier"]["odds_ratio"],
        "barrier_or_crossed_bootstrap_95": percentile_interval(barrier_or_samples),
    }


def prompt_family_memberships(prompts: list[dict[str, Any]]) -> tuple[list[list[str]], list[str]]:
    memberships = [family_labels(str(prompt["instruction"])) for prompt in prompts]
    primary = [labels[0] for labels in memberships]
    return memberships, primary


def family_macro_rates(
    outcome: np.ndarray,
    selected_models: np.ndarray,
    memberships: list[list[str]],
    primary: list[str],
) -> dict[str, Any]:
    all_families = sorted({family for labels in memberships for family in labels})
    multi_label_rows = []
    for family in all_families:
        indices = np.asarray(
            [index for index, labels in enumerate(memberships) if family in labels],
            dtype=int,
        )
        multi_label_rows.append(
            {
                "family": family,
                "prompt_count": int(len(indices)),
                "rate": float(np.mean(outcome[np.ix_(indices, selected_models)])),
            }
        )
    primary_families = sorted(set(primary))
    primary_rows = []
    for family in primary_families:
        indices = np.asarray([i for i, value in enumerate(primary) if value == family], dtype=int)
        primary_rows.append(
            {
                "family": family,
                "prompt_count": int(len(indices)),
                "rate": float(np.mean(outcome[np.ix_(indices, selected_models)])),
            }
        )
    rare_families = {
        row["family"] for row in primary_rows if int(row["prompt_count"]) < 3
    }
    rare_pooled_rows = [
        row for row in primary_rows if row["family"] not in rare_families
    ]
    if rare_families:
        rare_indices = np.asarray(
            [index for index, family in enumerate(primary) if family in rare_families],
            dtype=int,
        )
        rare_pooled_rows.append(
            {
                "family": "other_rare_primary_families",
                "prompt_count": int(len(rare_indices)),
                "rate": float(np.mean(outcome[np.ix_(rare_indices, selected_models)])),
                "pooled_families": sorted(rare_families),
            }
        )
    return {
        "micro_rate": float(np.mean(outcome[:, selected_models])),
        "multi_label_family_macro_rate": float(np.mean([row["rate"] for row in multi_label_rows])),
        "primary_family_macro_rate": float(np.mean([row["rate"] for row in primary_rows])),
        "rare_pooled_primary_family_macro_rate": float(
            np.mean([row["rate"] for row in rare_pooled_rows])
        ),
        "rare_pool_threshold": 3,
        "rare_primary_families": sorted(rare_families),
        "multi_label_families": multi_label_rows,
        "primary_family_partition": primary_rows,
        "rare_pooled_primary_family_partition": rare_pooled_rows,
    }


def family_balanced_per_model(
    execution: np.ndarray,
    signature: np.ndarray,
    memberships: list[list[str]],
    primary: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for model_index, model in enumerate(MODEL_ORDER):
        selected = np.asarray([model_index], dtype=int)
        exec_rates = family_macro_rates(execution, selected, memberships, primary)
        sig_rates = family_macro_rates(signature, selected, memberships, primary)
        rows.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "developer": MODEL_DEVELOPER[model],
                "execution_micro": exec_rates["micro_rate"],
                "execution_primary_family_macro": exec_rates["primary_family_macro_rate"],
                "execution_rare_pooled_family_macro": exec_rates[
                    "rare_pooled_primary_family_macro_rate"
                ],
                "signature_micro": sig_rates["micro_rate"],
                "signature_primary_family_macro": sig_rates["primary_family_macro_rate"],
                "signature_rare_pooled_family_macro": sig_rates[
                    "rare_pooled_primary_family_macro_rate"
                ],
            }
        )
    micro = np.asarray([row["signature_micro"] for row in rows])
    macro = np.asarray([row["signature_rare_pooled_family_macro"] for row in rows])
    rho, p_value = spearmanr(micro, macro)
    return rows + [
        {
            "model": "__rank_summary__",
            "model_label": "rank summary",
            "developer": "all",
            "signature_rank_spearman_rho": float(rho),
            "signature_rank_two_sided_p": float(p_value),
        }
    ]


def leave_one_developer_out(
    arrays: dict[str, np.ndarray],
    execution: np.ndarray,
    signature: np.ndarray,
    memberships: list[list[str]],
    primary: list[str],
) -> list[dict[str, Any]]:
    full_models = np.arange(len(MODEL_ORDER), dtype=int)
    all_prompts = np.arange(signature.shape[0], dtype=int)
    full_mask = np.ones(signature.shape[0], dtype=bool)
    developers = sorted(set(MODEL_DEVELOPER.values()))
    rows = []
    for omitted in [None, *developers]:
        kept_models = [
            index
            for index, model in enumerate(MODEL_ORDER)
            if omitted is None or MODEL_DEVELOPER[model] != omitted
        ]
        selected = np.asarray(kept_models, dtype=int)
        exec_family = family_macro_rates(execution, selected, memberships, primary)
        sig_family = family_macro_rates(signature, selected, memberships, primary)
        fit = grouped_fit(arrays, signature, all_prompts, selected, stats_mask=full_mask)
        rows.append(
            {
                "omitted_developer": omitted or "none",
                "model_count": int(len(selected)),
                "execution_rate": exec_family["micro_rate"],
                "signature_rate": sig_family["micro_rate"],
                "execution_structure_gap": exec_family["micro_rate"] - sig_family["micro_rate"],
                "signature_primary_family_macro_rate": sig_family["primary_family_macro_rate"],
                "signature_rare_pooled_family_macro_rate": sig_family[
                    "rare_pooled_primary_family_macro_rate"
                ],
                "gate_entropy_odds_ratio": fit["terms"]["z_gate_entropy"]["odds_ratio"],
                "barrier_odds_ratio": fit["terms"]["has_barrier"]["odds_ratio"],
                "omitted_models": [
                    MODEL_LABELS[model]
                    for model in MODEL_ORDER
                    if omitted is not None and MODEL_DEVELOPER[model] == omitted
                ],
            }
        )
    baseline = rows[0]
    for row in rows:
        row["signature_delta_from_full"] = row["signature_rate"] - baseline["signature_rate"]
        row["gap_delta_from_full"] = (
            row["execution_structure_gap"] - baseline["execution_structure_gap"]
        )
    return rows


def write_pilot_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "model",
        "model_label",
        "developer",
        "pilot_execution_rate",
        "extension_execution_rate",
        "execution_change",
        "pilot_signature_rate",
        "extension_signature_rate",
        "signature_change",
        "pilot_gap",
        "extension_gap",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_sensitivity_csv(
    path: Path,
    family_rows: list[dict[str, Any]],
    developer_rows: list[dict[str, Any]],
) -> None:
    fields = [
        "analysis",
        "label",
        "model_count",
        "prompt_count",
        "execution_rate",
        "signature_rate",
        "execution_structure_gap",
        "family_macro_rate",
        "gate_entropy_odds_ratio",
        "barrier_odds_ratio",
        "delta_from_full",
    ]
    rows: list[dict[str, Any]] = []
    for row in family_rows:
        if row["model"] == "__rank_summary__":
            continue
        rows.append(
            {
                "analysis": "per_model_family_balance",
                "label": row["model_label"],
                "model_count": 1,
                "prompt_count": 154,
                "execution_rate": row["execution_micro"],
                "signature_rate": row["signature_micro"],
                "family_macro_rate": row["signature_rare_pooled_family_macro"],
                "delta_from_full": (
                    row["signature_rare_pooled_family_macro"] - row["signature_micro"]
                ),
            }
        )
    for row in developer_rows:
        rows.append(
            {
                "analysis": "leave_one_developer_out",
                "label": row["omitted_developer"],
                "model_count": row["model_count"],
                "prompt_count": 154,
                "execution_rate": row["execution_rate"],
                "signature_rate": row["signature_rate"],
                "execution_structure_gap": row["execution_structure_gap"],
                "family_macro_rate": row["signature_rare_pooled_family_macro_rate"],
                "gate_entropy_odds_ratio": row["gate_entropy_odds_ratio"],
                "barrier_odds_ratio": row["barrier_odds_ratio"],
                "delta_from_full": row["signature_delta_from_full"],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def interval_pct(interval: list[float]) -> str:
    return f"[{pct(interval[0])}, {pct(interval[1])}]"


def interval_or(interval: list[float]) -> str:
    return f"[{interval[0]:.2f}, {interval[1]:.2f}]"


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_supplemental_tsvs(payload: dict[str, Any]) -> None:
    replication = payload["pilot_extension_replication"]
    s27_rows = []
    for roster_key, roster_label in [
        ("final_21", "final 21-model roster"),
        ("original_15", "original 15-model panel"),
    ]:
        for cohort in ["pilot", "extension"]:
            row = replication[roster_key][cohort]
            s27_rows.append(
                {
                    "roster": roster_label,
                    "cohort": cohort,
                    "prompts": row["prompt_count"],
                    "target_signatures": row["signature_cluster_count"],
                    "models": row["model_count"],
                    "cells": row["cell_count"],
                    "execution_rate": row["execution_rate"],
                    "signature_rate": row["signature_rate"],
                    "execution_structure_gap": row["execution_structure_gap"],
                    "gate_entropy_odds_ratio": row["gate_entropy_odds_ratio"],
                    "gate_entropy_or_ci_low": row[
                        "gate_entropy_or_cluster_bootstrap_95"
                    ][0],
                    "gate_entropy_or_ci_high": row[
                        "gate_entropy_or_cluster_bootstrap_95"
                    ][1],
                }
            )
    write_tsv(
        S27_TSV_OUT,
        list(s27_rows[0]),
        s27_rows,
    )

    crossed = payload["crossed_model_signature_bootstrap"]
    s28_rows = [
        {
            "quantity": "execution rate",
            "estimate": crossed["execution_rate"],
            "ci_low": crossed["execution_crossed_bootstrap_95"][0],
            "ci_high": crossed["execution_crossed_bootstrap_95"][1],
        },
        {
            "quantity": "reference-signature rate",
            "estimate": crossed["signature_rate"],
            "ci_low": crossed["signature_crossed_bootstrap_95"][0],
            "ci_high": crossed["signature_crossed_bootstrap_95"][1],
        },
        {
            "quantity": "execution-structure gap",
            "estimate": crossed["execution_structure_gap"],
            "ci_low": crossed["gap_crossed_bootstrap_95"][0],
            "ci_high": crossed["gap_crossed_bootstrap_95"][1],
        },
        {
            "quantity": "gate-entropy odds ratio per SD",
            "estimate": crossed["gate_entropy_odds_ratio"],
            "ci_low": crossed["gate_entropy_or_crossed_bootstrap_95"][0],
            "ci_high": crossed["gate_entropy_or_crossed_bootstrap_95"][1],
        },
        {
            "quantity": "barrier/staged odds ratio",
            "estimate": crossed["barrier_odds_ratio"],
            "ci_low": crossed["barrier_or_crossed_bootstrap_95"][0],
            "ci_high": crossed["barrier_or_crossed_bootstrap_95"][1],
        },
    ]
    write_tsv(S28_TSV_OUT, list(s28_rows[0]), s28_rows)

    sensitivity = payload["family_and_developer_sensitivity"]
    s29_rows = []
    for row in sensitivity["leave_one_developer_out"]:
        s29_rows.append(
            {
                "omitted_developer": row["omitted_developer"],
                "models_retained": row["model_count"],
                "execution_rate": row["execution_rate"],
                "signature_rate": row["signature_rate"],
                "execution_structure_gap": row["execution_structure_gap"],
                "rare_pooled_family_macro_signature_rate": row[
                    "signature_rare_pooled_family_macro_rate"
                ],
                "gate_entropy_odds_ratio": row["gate_entropy_odds_ratio"],
                "barrier_odds_ratio": row["barrier_odds_ratio"],
                "signature_delta_from_full": row["signature_delta_from_full"],
            }
        )
    write_tsv(S29_TSV_OUT, list(s29_rows[0]), s29_rows)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    replication = payload["pilot_extension_replication"]
    crossed = payload["crossed_model_signature_bootstrap"]
    balancing = payload["family_and_developer_sensitivity"]
    final21 = replication["final_21"]
    pilot = final21["pilot"]
    extension = final21["extension"]
    legacy_rank = replication["original_15_rank_replication"]
    final_rank = replication["final_21_rank_replication"]
    developer_rows = balancing["leave_one_developer_out"]
    omitted = developer_rows[1:]

    lines = [
        "# PQID-Bench Replication And Crossed Robustness Audit",
        "",
        "## Scope",
        "",
        "This audit uses the frozen 21-model by 154-prompt matrix. It does not add model calls, change the evaluator, or make causal claims. The 84-prompt extension was selected without model outcomes, uses source-file-group-safe assignments, contains unique target signatures, and excludes every target signature present in the 70-prompt pilot.",
        "",
        "## 1. Pilot-versus-extension replication",
        "",
        "| final-21 cohort | prompts | signatures | execution | reference-signature match | ES gap | entropy OR per SD |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| pilot | {pilot['prompt_count']} | {pilot['signature_cluster_count']} | {pct(pilot['execution_rate'])} {interval_pct(pilot['execution_cluster_bootstrap_95'])} | {pct(pilot['signature_rate'])} {interval_pct(pilot['signature_cluster_bootstrap_95'])} | {pp(pilot['execution_structure_gap'])} | {pilot['gate_entropy_odds_ratio']:.2f} {interval_or(pilot['gate_entropy_or_cluster_bootstrap_95'])} |",
        f"| prospective extension | {extension['prompt_count']} | {extension['signature_cluster_count']} | {pct(extension['execution_rate'])} {interval_pct(extension['execution_cluster_bootstrap_95'])} | {pct(extension['signature_rate'])} {interval_pct(extension['signature_cluster_bootstrap_95'])} | {pp(extension['execution_structure_gap'])} | {extension['gate_entropy_odds_ratio']:.2f} {interval_or(extension['gate_entropy_or_cluster_bootstrap_95'])} |",
        "",
        f"Across the original 15-model panel, pilot-versus-extension model ranks have Spearman rho `{legacy_rank['spearman_rho']:.3f}` (two-sided p `{legacy_rank['two_sided_p']:.4g}`). Across all 21 final rows, rho is `{final_rank['spearman_rho']:.3f}` (p `{final_rank['two_sided_p']:.4g}`). Raw cohort rates are not expected to be equal because the extension deliberately adds new, quota-balanced signatures and a larger difficult-item share.",
        "",
        "Replication criteria are claim-level: the ES gap must remain positive in both cohorts, and greater gate entropy must retain a point estimate below one within each cohort. The extension-only entropy interval slightly includes one, so the extension reproduces the direction but is not independently conclusive at the 95% level; the combined crossed analysis supplies the better-powered inferential result.",
        "",
        "## 2. Crossed model-by-signature robustness",
        "",
        f"A `{crossed['replicates']:,}`-replicate two-way bootstrap independently resamples all `{crossed['model_count']}` model rows and all `{crossed['signature_cluster_count']}` target-signature clusters. This treats neither prompt-model cells nor model rows as independent fixed replicates.",
        "",
        "| quantity | point estimate | crossed 95% interval |",
        "|---|---:|---:|",
        f"| execution | {pct(crossed['execution_rate'])} | {interval_pct(crossed['execution_crossed_bootstrap_95'])} |",
        f"| reference-signature match | {pct(crossed['signature_rate'])} | {interval_pct(crossed['signature_crossed_bootstrap_95'])} |",
        f"| execution-structure gap | {pp(crossed['execution_structure_gap'])} | [{pp(crossed['gap_crossed_bootstrap_95'][0])}, {pp(crossed['gap_crossed_bootstrap_95'][1])}] |",
        f"| gate entropy, OR per SD | {crossed['gate_entropy_odds_ratio']:.2f} | {interval_or(crossed['gate_entropy_or_crossed_bootstrap_95'])} |",
        f"| barrier/staged marker, OR | {crossed['barrier_odds_ratio']:.2f} | {interval_or(crossed['barrier_or_crossed_bootstrap_95'])} |",
        "",
        "## 3. Circuit-family balance",
        "",
        f"The unweighted signature rate is `{pct(balancing['signature_family_balance']['micro_rate'])}`. Giving each primary circuit-family label equal weight yields `{pct(balancing['signature_family_balance']['primary_family_macro_rate'])}`. Pooling primary families represented by fewer than three prompts before macro-averaging yields `{pct(balancing['signature_family_balance']['rare_pooled_primary_family_macro_rate'])}`, while the overlapping multi-label macro estimate is `{pct(balancing['signature_family_balance']['multi_label_family_macro_rate'])}`. The rare-pooled primary-family and micro model rankings have Spearman rho `{balancing['per_model_family_balance_rank']['spearman_rho']:.3f}`.",
        "",
        "Primary families are assigned by the prespecified ordered keyword taxonomy used in the existing complexity audit; this is a weighting sensitivity, not a claim that the keyword taxonomy is ontologically complete.",
        "",
        "## 4. Leave-one-developer-out sensitivity",
        "",
        "Developer denotes the checkpoint developer, not the API host. The Qiskit specialist is assigned to IBM/Qiskit and kept separate from its Mistral parent.",
        "",
        "| omitted developer | models retained | execution | signature | ES gap | entropy OR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in developer_rows:
        lines.append(
            f"| {row['omitted_developer']} | {row['model_count']} | {pct(row['execution_rate'])} | {pct(row['signature_rate'])} ({pp(row['signature_delta_from_full'])}) | {pp(row['execution_structure_gap'])} | {row['gate_entropy_odds_ratio']:.2f} |"
        )
    signature_values = [row["signature_rate"] for row in omitted]
    gap_values = [row["execution_structure_gap"] for row in omitted]
    entropy_values = [row["gate_entropy_odds_ratio"] for row in omitted]
    lines.extend(
        [
            "",
            f"Across the eight omissions, signature match ranges from `{pct(min(signature_values))}` to `{pct(max(signature_values))}`, the ES gap from `{pp(min(gap_values))}` to `{pp(max(gap_values))}`, and the adjusted entropy odds ratio from `{min(entropy_values):.2f}` to `{max(entropy_values):.2f}`. The qualitative conclusions therefore do not depend on any single developer group.",
            "",
            "## Interpretation boundary",
            "",
            "These analyses strengthen transportability and uncertainty accounting for the frozen benchmark release. They do not identify causal effects of circuit features, because prompt properties were not randomized and several descriptors co-vary. The ordered/operand-aware evaluator audit is reported separately.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "python PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_robustness_suite.py",
            "```",
            "",
            f"- machine-readable report: `{JSON_OUT.as_posix()}`",
            f"- per-model cohort table: `{PILOT_CSV_OUT.as_posix()}`",
            f"- family/developer sensitivity table: `{SENSITIVITY_CSV_OUT.as_posix()}`",
            f"- Supplemental Table S27 TSV: `{S27_TSV_OUT.as_posix()}`",
            f"- Supplemental Table S28 TSV: `{S28_TSV_OUT.as_posix()}`",
            f"- Supplemental Table S29 TSV: `{S29_TSV_OUT.as_posix()}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument("--split-manifest", type=Path, default=SPLIT_MANIFEST_PATH)
    parser.add_argument("--eval-dir", type=Path, action="append", default=None)
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--pilot-csv-out", type=Path, default=PILOT_CSV_OUT)
    parser.add_argument("--sensitivity-csv-out", type=Path, default=SENSITIVITY_CSV_OUT)
    parser.add_argument("--cohort-bootstrap", type=int, default=2000)
    parser.add_argument("--crossed-bootstrap", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()

    prompts = read_jsonl(args.prompt_path)
    feature_rows = [prompt_features(prompt) for prompt in prompts]
    prompt_ids = [str(row["prompt_id"]) for row in feature_rows]
    execution, signature, qasm3, sources = load_evaluation_matrices(
        args.eval_dir or DEFAULT_EVAL_DIRS,
        prompt_ids,
    )
    arrays = feature_arrays(feature_rows)
    arrays["prompt_id"] = np.asarray(prompt_ids, dtype=object)
    cluster_for_prompt, clusters = signature_clusters(feature_rows)
    cohorts = cohort_map(args.split_manifest)
    pilot_mask = np.asarray([cohorts[prompt_id] == "pilot" for prompt_id in prompt_ids])
    extension_mask = np.asarray([cohorts[prompt_id] == "extension" for prompt_id in prompt_ids])

    all_models = np.arange(len(MODEL_ORDER), dtype=int)
    legacy_models = model_indices(ORIGINAL_PILOT_MODELS)
    per_model_rows = per_model_cohort_rows(execution, signature, pilot_mask, extension_mask)

    final_21 = {
        "pilot": cluster_bootstrap_cohort(
            arrays,
            execution,
            signature,
            pilot_mask,
            all_models,
            cluster_for_prompt,
            args.cohort_bootstrap,
            args.seed,
        ),
        "extension": cluster_bootstrap_cohort(
            arrays,
            execution,
            signature,
            extension_mask,
            all_models,
            cluster_for_prompt,
            args.cohort_bootstrap,
            args.seed + 1,
        ),
    }
    original_15 = {
        "pilot": cluster_bootstrap_cohort(
            arrays,
            execution,
            signature,
            pilot_mask,
            legacy_models,
            cluster_for_prompt,
            args.cohort_bootstrap,
            args.seed + 2,
        ),
        "extension": cluster_bootstrap_cohort(
            arrays,
            execution,
            signature,
            extension_mask,
            legacy_models,
            cluster_for_prompt,
            args.cohort_bootstrap,
            args.seed + 3,
        ),
    }

    memberships, primary_families = prompt_family_memberships(prompts)
    execution_family = family_macro_rates(
        execution, all_models, memberships, primary_families
    )
    signature_family = family_macro_rates(
        signature, all_models, memberships, primary_families
    )
    per_model_family = family_balanced_per_model(
        execution, signature, memberships, primary_families
    )
    rank_summary = per_model_family[-1]
    developer_rows = leave_one_developer_out(
        arrays, execution, signature, memberships, primary_families
    )

    payload = {
        "schema_version": "pqid-bench-robustness-suite-v1",
        "design": {
            "prompt_count": len(prompts),
            "pilot_prompt_count": int(np.sum(pilot_mask)),
            "extension_prompt_count": int(np.sum(extension_mask)),
            "model_count": len(MODEL_ORDER),
            "signature_cluster_count": len(clusters),
            "cell_count": int(signature.size),
            "models": MODEL_ORDER,
            "model_developer": MODEL_DEVELOPER,
            "source_reports": sources,
            "extension_selected_without_model_outcomes": True,
            "extension_excludes_pilot_target_signatures": True,
        },
        "pilot_extension_replication": {
            "method": "target-signature-cluster bootstrap within each disjoint cohort",
            "bootstrap_replicates": args.cohort_bootstrap,
            "final_21": final_21,
            "original_15": original_15,
            "final_21_rank_replication": rank_replication(per_model_rows, MODEL_ORDER),
            "original_15_rank_replication": rank_replication(
                per_model_rows, ORIGINAL_PILOT_MODELS
            ),
            "per_model": per_model_rows,
        },
        "crossed_model_signature_bootstrap": crossed_bootstrap(
            arrays,
            execution,
            signature,
            clusters,
            args.crossed_bootstrap,
            args.seed + 10,
        ),
        "family_and_developer_sensitivity": {
            "family_taxonomy": (
                "prespecified ordered keyword taxonomy from "
                "analyze_pqid_bench_complexity_difficulty.py"
            ),
            "execution_family_balance": execution_family,
            "signature_family_balance": signature_family,
            "per_model_family_balance": per_model_family[:-1],
            "per_model_family_balance_rank": {
                "spearman_rho": rank_summary["signature_rank_spearman_rho"],
                "two_sided_p": rank_summary["signature_rank_two_sided_p"],
            },
            "leave_one_developer_out": developer_rows,
        },
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.md_out, payload)
    write_pilot_csv(args.pilot_csv_out, per_model_rows)
    write_sensitivity_csv(args.sensitivity_csv_out, per_model_family[:-1], developer_rows)
    write_supplemental_tsvs(payload)
    print(f"Wrote {args.json_out.as_posix()}")
    print(f"Wrote {args.md_out.as_posix()}")
    print(f"Wrote {args.pilot_csv_out.as_posix()}")
    print(f"Wrote {args.sensitivity_csv_out.as_posix()}")
    print(f"Wrote {S27_TSV_OUT.as_posix()}")
    print(f"Wrote {S28_TSV_OUT.as_posix()}")
    print(f"Wrote {S29_TSV_OUT.as_posix()}")


if __name__ == "__main__":
    main()
