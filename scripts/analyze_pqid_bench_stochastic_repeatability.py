"""Analyze three-run stochastic repeatability for a frozen PQID-Bench panel."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import binomtest, chi2, kendalltau, spearmanr

from pqid_bench_model_registry import (
    FRONTIER_MODELS,
    MODEL_LABELS,
    PRIMARY_MODEL_ORDER,
    model_from_report_dir,
)


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x36"
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
BOOTSTRAP_SEED = 20260715
BOOTSTRAP_REPLICATES = 5000
SCHEMA_VERSION = "pqid-bench-stochastic-repeatability-analysis-v4"
ENDPOINTS = {
    "execution": "Execution",
    "signature": "Reference-signature match",
    "runnable_wrong": "Executable reference-signature disagreement",
    "qasm3": "QASM3 export",
}
PRIMARY_ENDPOINTS = ("execution", "signature", "runnable_wrong")
RUN_PAIRS = ((0, 1), (0, 2), (1, 2))
FULL_GATE_BIN_COUNTS = {"1-2": 42, "3-4": 85, "5+": 27}
TOP_K = 5
EXPECTED_PANEL_SHA256 = "a607d5cd17abb8728acfc857d7bcc6aa122f71945a4f4072808a4c52079dab61"
EXPECTED_PROTOCOL_SHA256 = "29b5026427df975eda8de75fb2c32de958270bb64f3aa1d3c64f1b0efdc4d577"
EXPECTED_AMENDMENTS_SHA256 = "8ca6d47ab24b590609d34e4e1a82abe066ec86452fc2f1722c5d174528b3066d"
ANALYSIS_PROTOCOL_FROZEN_AT = "2026-07-15T18:01:15+09:00"
ANALYSIS_PROTOCOL_AMENDED_AT = "2026-07-15T19:16:40+09:00"
INCREMENTAL_API_CALLS: int | None = None


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def verify_protocol_freeze(root: Path) -> dict[str, str]:
    checks = {
        "protocol": (root / "PRESPECIFIED_PROTOCOL.md", EXPECTED_PROTOCOL_SHA256),
        "amendments": (root / "PROTOCOL_AMENDMENTS.md", EXPECTED_AMENDMENTS_SHA256),
    }
    verified: dict[str, str] = {}
    for label, (path, expected) in checks.items():
        observed = sha256_file(path)
        if observed != expected:
            raise AssertionError(
                f"Frozen {label} hash changed: expected {expected}, found {observed}"
            )
        verified[f"{label}_path"] = display_path(path)
        verified[f"{label}_sha256"] = observed
    return verified


def strip_outer_code_fence(text: str) -> str:
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and re.fullmatch(r"\s*```(?:python|py)?\s*", lines[0], flags=re.IGNORECASE):
        lines.pop(0)
        if lines and re.fullmatch(r"\s*```\s*", lines[-1]):
            lines.pop()
    return "\n".join(lines)


def normalize_code_text(value: Any) -> str:
    """Apply the frozen minimal text normalization contract."""

    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = strip_outer_code_fence(text)
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        normalized.append("" if is_blank else line)
        previous_blank = is_blank
    return "\n".join(normalized)


def ast_canonical_form(code: str) -> str:
    if not code:
        return ""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, TypeError):
        return ""
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else ""


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def canonical_responses(path: Path) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for line_number, row in enumerate(iter_jsonl(path), start=1):
        prompt_id = str(row.get("prompt_id") or "")
        if not prompt_id:
            raise ValueError(f"Missing prompt_id on response row {line_number} of {path}")
        if prompt_id in mapped:
            raise ValueError(
                f"Duplicate response for {prompt_id} in {path}; the repeatability audit "
                "does not permit last-row-wins canonicalization"
            )
        mapped[prompt_id] = row
    return mapped


def panel_metadata(root: Path) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, Any]]:
    manifest_path = root / "panel" / "pqid_bench_stochastic_repeatability_panel.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared_sha256 = str(
        manifest.get("panel_sha256")
        or manifest.get("augmentation_panel_sha256")
        or ""
    )
    if declared_sha256 != EXPECTED_PANEL_SHA256:
        raise AssertionError(
            f"Frozen panel hash changed: expected {EXPECTED_PANEL_SHA256}, found {declared_sha256}"
        )
    panel_filename = Path(
        str(
            manifest.get("panel_file")
            or manifest.get("augmentation_panel_file")
            or ""
        )
    ).name
    panel_path = root / "panel" / panel_filename
    observed_sha256 = sha256_file(panel_path)
    if observed_sha256 != EXPECTED_PANEL_SHA256:
        raise AssertionError(
            f"Frozen panel file failed SHA-256 verification: {observed_sha256}"
        )
    records = manifest["selected_prompts"]
    prompt_ids = [str(row["prompt_id"]) for row in records]
    panel_rows = iter_jsonl(panel_path)
    panel_row_map = {str(row["prompt_id"]): row for row in panel_rows}
    if len(panel_row_map) != len(panel_rows) or set(panel_row_map) != set(prompt_ids):
        raise AssertionError("Frozen panel prompt rows do not match the panel manifest")
    for record in records:
        prompt_id = str(record["prompt_id"])
        reference = record["reference_signature"]
        if sha256_json(reference) != str(record["reference_signature_sha256"]):
            raise AssertionError(f"Reference-signature hash failed for {prompt_id}")
        if panel_row_map[prompt_id].get("target_metadata") != reference:
            raise AssertionError(f"Panel target metadata differs from its manifest for {prompt_id}")
    return prompt_ids, {str(row["prompt_id"]): row for row in records}, manifest


def load_cell_rows(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt_ids, prompt_meta, panel_manifest = panel_metadata(root)
    expected_prompts = set(prompt_ids)
    cells: list[dict[str, Any]] = []
    evaluator_versions: set[str] = set()
    predicate_versions: set[str] = set()

    for run_number in (1, 2, 3):
        evaluation_root = root / f"run_{run_number}" / "evaluations"
        report_paths = sorted(evaluation_root.glob(f"*/{REPORT_NAME}"))
        if len(report_paths) != len(PRIMARY_MODEL_ORDER):
            raise ValueError(
                f"Run {run_number} has {len(report_paths)} reports; expected {len(PRIMARY_MODEL_ORDER)}"
            )
        observed_models: set[str] = set()
        for report_path in report_paths:
            slug = report_path.parent.name
            model = model_from_report_dir(slug)
            if model not in PRIMARY_MODEL_ORDER:
                raise ValueError(f"Unregistered report directory: {slug}")
            observed_models.add(model)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            evaluator_versions.add(str(report.get("evaluator_version") or ""))
            predicate_versions.add(str(report.get("structural_predicate_version") or ""))
            records = report.get("records") or []
            record_map = {str(row["prompt_id"]): row for row in records}
            if len(record_map) != len(records):
                raise ValueError(
                    f"Run {run_number} {slug} contains duplicate report prompt IDs"
                )
            if set(record_map) != expected_prompts:
                raise ValueError(f"Run {run_number} {slug} does not match the frozen panel")

            response_path = root / f"run_{run_number}" / "responses" / f"{slug}_responses.jsonl"
            responses = canonical_responses(response_path)
            if set(responses) != expected_prompts:
                raise ValueError(f"Run {run_number} {slug} response log does not match the panel")

            for prompt_id in prompt_ids:
                record = record_map[prompt_id]
                response = responses[prompt_id]
                target_metadata = record.get("target_metadata") or {}
                expected_target = prompt_meta[prompt_id]["reference_signature"]
                if target_metadata != expected_target:
                    raise AssertionError(
                        f"Frozen target metadata changed for {model} {prompt_id} run {run_number}"
                    )
                if sha256_json(target_metadata) != str(
                    prompt_meta[prompt_id]["reference_signature_sha256"]
                ):
                    raise AssertionError(
                        f"Frozen target signature hash changed for {model} {prompt_id} run {run_number}"
                    )
                execution = bool((record.get("execution") or {}).get("execution_success"))
                checks = record.get("structural_checks") or {}
                signature = bool(
                    execution
                    and checks.get("num_qubits_match")
                    and checks.get("num_clbits_match")
                    and checks.get("gate_types_match")
                )
                stored_all_match = bool(checks.get("all_match"))
                if signature != stored_all_match:
                    raise AssertionError(
                        "The frozen count-map invariant T=>G was violated for "
                        f"{model} {prompt_id}: QKT={signature}, stored all_match={stored_all_match}"
                    )
                qasm3 = bool(
                    (((record.get("execution") or {}).get("qasm3_export") or {}).get("success"))
                )
                if signature and not execution:
                    raise AssertionError(f"Signature match without execution: {model} {prompt_id}")
                finish_reason = str(response.get("finish_reason") or "")
                provider_metadata = response.get("provider_metadata") or {}
                provider_error = finish_reason == "error" or bool(provider_metadata.get("error_type"))
                attempt_trace = provider_metadata.get("attempt_trace")
                attempt_trace_recorded = bool(
                    isinstance(attempt_trace, list)
                    and attempt_trace
                    and provider_metadata.get("attempt_count") == len(attempt_trace)
                )
                attempt_count = (
                    int(provider_metadata["attempt_count"])
                    if attempt_trace_recorded
                    else None
                )
                recovered = (
                    bool(provider_metadata.get("recovered_after_transport_error"))
                    if attempt_trace_recorded
                    else None
                )
                initial_attempt_success = (
                    bool(provider_metadata.get("initial_attempt_success"))
                    if attempt_trace_recorded
                    else None
                )
                transport_affected = bool(
                    provider_error
                    or (
                        attempt_trace_recorded
                        and (bool(recovered) or not bool(initial_attempt_success))
                    )
                )
                code = normalize_code_text(response.get("generated_code"))
                canonical_ast = ast_canonical_form(code)
                cells.append(
                    {
                        "run": run_number,
                        "model": model,
                        "model_label": MODEL_LABELS[model],
                        "model_order": PRIMARY_MODEL_ORDER.index(model) + 1,
                        "slug": slug,
                        "provider": str(response.get("provider") or ""),
                        "prompt_id": prompt_id,
                        "cohort": prompt_meta[prompt_id]["cohort"],
                        "gate_type_bin": prompt_meta[prompt_id]["gate_type_bin"],
                        "has_barrier": bool(prompt_meta[prompt_id]["has_barrier"]),
                        "execution": int(execution),
                        "signature": int(signature),
                        "runnable_wrong": int(execution and not signature),
                        "qasm3": int(qasm3),
                        "gate_count_diagnostic": int(bool(checks.get("gate_count_match"))),
                        "finish_reason": finish_reason,
                        "provider_error": int(provider_error),
                        "transport_affected": int(transport_affected),
                        "attempt_trace_recorded": int(attempt_trace_recorded),
                        "attempt_count": attempt_count,
                        "initial_attempt_success": (
                            int(initial_attempt_success)
                            if initial_attempt_success is not None
                            else None
                        ),
                        "recovered_after_transport_error": (
                            int(recovered) if recovered is not None else None
                        ),
                        "created_at_utc": str(response.get("created_at_utc") or ""),
                        "request_sha256": str(response.get("request_sha256") or ""),
                        "response_sha256": sha256_json(response),
                        "normalized_text_sha256": sha256_text(code),
                        "ast_sha256": sha256_text(canonical_ast),
                        "ast_parse_success": int(bool(canonical_ast)),
                    }
                )
        if observed_models != set(PRIMARY_MODEL_ORDER):
            raise ValueError(f"Run {run_number} model roster differs from the frozen 21-model roster")

    expected_cell_count = 3 * len(PRIMARY_MODEL_ORDER) * len(prompt_ids)
    if len(cells) != expected_cell_count:
        raise AssertionError(f"Expected {expected_cell_count} outcome rows, found {len(cells)}")
    request_hashes: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in cells:
        request_hash = str(row["request_sha256"])
        if not request_hash:
            raise AssertionError(
                f"Missing request hash for {row['model']} {row['prompt_id']} run {row['run']}"
            )
        request_hashes[(str(row["model"]), str(row["prompt_id"]))].add(request_hash)
    changed_requests = [key for key, hashes in request_hashes.items() if len(hashes) != 1]
    if changed_requests:
        raise AssertionError(
            "Provider request identity changed across runs for: "
            + ", ".join(f"{model}/{prompt}" for model, prompt in changed_requests[:5])
        )
    if "" in evaluator_versions or len(evaluator_versions) != 1:
        raise AssertionError(
            f"Expected one nonempty evaluator version across all runs, found {sorted(evaluator_versions)}"
        )
    if "" in predicate_versions or len(predicate_versions) != 1:
        raise AssertionError(
            "Expected one nonempty stored predicate version across all runs, found "
            f"{sorted(predicate_versions)}"
        )
    metadata = {
        "panel_manifest": panel_manifest,
        "evaluator_versions": sorted(evaluator_versions),
        "predicate_versions": sorted(predicate_versions),
        "request_identity_verified": True,
        "verified_model_prompt_requests": len(request_hashes),
        "target_identity_verified": True,
        "verified_scored_cells": len(cells),
        "canonical_completeness": {
            "expected_cells": expected_cell_count,
            "observed_cells": len(cells),
            "missing_cells": 0,
            "duplicate_keys": 0,
            "unexpected_keys": 0,
            "request_hash_mismatches": 0,
            "target_metadata_mismatches": 0,
        },
    }
    return cells, metadata


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:.2f} pp"


def endpoint_triples(
    rows: list[dict[str, Any]], endpoint: str, *, complete_only: bool = False
) -> list[tuple[int, int, int]]:
    values: dict[tuple[str, str], dict[int, int]] = defaultdict(dict)
    errors: dict[tuple[str, str], dict[int, int]] = defaultdict(dict)
    for row in rows:
        key = (str(row["model"]), str(row["prompt_id"]))
        values[key][int(row["run"])] = int(row[endpoint])
        errors[key][int(row["run"])] = int(row["transport_affected"])
    triples: list[tuple[int, int, int]] = []
    for key in sorted(values):
        if set(values[key]) != {1, 2, 3}:
            raise AssertionError(f"Incomplete run triple: {key}")
        if complete_only and any(errors[key].values()):
            continue
        triples.append(tuple(values[key][run] for run in (1, 2, 3)))
    return triples


def agreement_stats(triples: list[tuple[int, int, int]]) -> dict[str, float | int]:
    if not triples:
        return {
            "items": 0,
            "unanimous_items": 0,
            "unanimous_rate": math.nan,
            "any_flip_rate": math.nan,
            "pairwise_agreement": math.nan,
            "pairwise_flip_rate": math.nan,
            "gwet_ac1": math.nan,
        }
    unanimous = sum(len(set(values)) == 1 for values in triples)
    agreeing_pairs = sum(
        int(values[0] == values[1])
        + int(values[0] == values[2])
        + int(values[1] == values[2])
        for values in triples
    )
    pairwise_agreement = agreeing_pairs / (3 * len(triples))
    positive_rate = sum(sum(values) for values in triples) / (3 * len(triples))
    chance_agreement = 2 * positive_rate * (1 - positive_rate)
    ac1 = (
        (pairwise_agreement - chance_agreement) / (1 - chance_agreement)
        if chance_agreement < 1
        else 1.0
    )
    return {
        "items": len(triples),
        "unanimous_items": unanimous,
        "unanimous_rate": unanimous / len(triples),
        "any_flip_rate": 1 - unanimous / len(triples),
        "pairwise_agreement": pairwise_agreement,
        "pairwise_flip_rate": 1 - pairwise_agreement,
        "gwet_ac1": ac1,
    }


def outcome_cube(rows: list[dict[str, Any]], endpoint: str) -> tuple[np.ndarray, list[str]]:
    prompts = sorted({str(row["prompt_id"]) for row in rows})
    prompt_index = {prompt_id: index for index, prompt_id in enumerate(prompts)}
    model_index = {model: index for index, model in enumerate(PRIMARY_MODEL_ORDER)}
    cube = np.full((len(PRIMARY_MODEL_ORDER), len(prompts), 3), -1, dtype=np.int8)
    for row in rows:
        cube[
            model_index[str(row["model"])],
            prompt_index[str(row["prompt_id"])],
            int(row["run"]) - 1,
        ] = int(row[endpoint])
    if np.any(cube < 0):
        raise AssertionError(f"Incomplete outcome cube for {endpoint}")
    return cube, prompts


def array_agreement_metrics(values: np.ndarray) -> dict[str, float]:
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("Agreement input must have shape (items, 3)")
    unanimous = np.all(values == values[:, [0]], axis=1)
    pair_equal = np.column_stack(
        (values[:, 0] == values[:, 1], values[:, 0] == values[:, 2], values[:, 1] == values[:, 2])
    )
    pairwise_agreement = float(pair_equal.mean())
    positive_rate = float(values.mean())
    chance_agreement = 2 * positive_rate * (1 - positive_rate)
    gwet = (
        (pairwise_agreement - chance_agreement) / (1 - chance_agreement)
        if chance_agreement < 1
        else 1.0
    )
    metrics = {
        "unanimous_rate": float(unanimous.mean()),
        "any_flip_rate": float(1 - unanimous.mean()),
        "pairwise_agreement": pairwise_agreement,
        "gwet_ac1": float(gwet),
    }
    for first, second in RUN_PAIRS:
        left = values[:, first]
        right = values[:, second]
        agreement = float(np.mean(left == right))
        marginal = float(np.mean(np.concatenate((left, right))))
        chance = 2 * marginal * (1 - marginal)
        key = f"pair_{first + 1}_{second + 1}"
        metrics[f"{key}_agreement"] = agreement
        metrics[f"{key}_gwet_ac1"] = (
            float((agreement - chance) / (1 - chance)) if chance < 1 else 1.0
        )
        metrics[f"{key}_flip_rate"] = float(np.mean(left != right))
        metrics[f"{key}_loss_rate"] = float(np.mean((left == 1) & (right == 0)))
        metrics[f"{key}_gain_rate"] = float(np.mean((left == 0) & (right == 1)))
        metrics[f"{key}_delta"] = float(right.mean() - left.mean())
    for run_index in range(3):
        metrics[f"run_rate_{run_index + 1}"] = float(values[:, run_index].mean())
    return metrics


def bootstrap_metric_samples(
    rows: list[dict[str, Any]], endpoint: str, *, resample_models: bool
) -> dict[str, list[float]]:
    """Resample prompt signatures and, for crossed inference, model rows independently."""

    cube, _ = outcome_cube(rows, endpoint)
    seed_offset = sum(ord(char) for char in endpoint) + (100_000 if resample_models else 0)
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    estimates: dict[str, list[float]] = defaultdict(list)
    model_count, prompt_count, _ = cube.shape
    fixed_models = np.arange(model_count)
    for _ in range(BOOTSTRAP_REPLICATES):
        model_sample = (
            rng.integers(0, model_count, size=model_count) if resample_models else fixed_models
        )
        prompt_sample = rng.integers(0, prompt_count, size=prompt_count)
        sampled = cube[model_sample][:, prompt_sample, :].reshape(-1, 3)
        for name, value in array_agreement_metrics(sampled).items():
            estimates[name].append(value)
    return dict(estimates)


def pairwise_agreement_stats(triples: list[tuple[int, int, int]]) -> list[dict[str, Any]]:
    matrix = np.asarray(triples, dtype=np.int8)
    output: list[dict[str, Any]] = []
    for first, second in RUN_PAIRS:
        left = matrix[:, first]
        right = matrix[:, second]
        agreement = float(np.mean(left == right))
        marginal = float(np.mean(np.concatenate((left, right))))
        chance = 2 * marginal * (1 - marginal)
        output.append(
            {
                "run_pair": f"{first + 1}-{second + 1}",
                "agreement": agreement,
                "gwet_ac1": float((agreement - chance) / (1 - chance)) if chance < 1 else 1.0,
                "flip_rate": float(np.mean(left != right)),
                "loss_rate": float(np.mean((left == 1) & (right == 0))),
                "gain_rate": float(np.mean((left == 0) & (right == 1))),
                "rate_delta_pp": float(100 * (right.mean() - left.mean())),
            }
        )
    return output


def interval(values: list[float]) -> dict[str, float]:
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if not finite.size:
        return {"low": math.nan, "high": math.nan}
    return {
        "low": float(np.quantile(finite, 0.025)),
        "high": float(np.quantile(finite, 0.975)),
    }


def cochran_q(triples: list[tuple[int, int, int]]) -> dict[str, float | int]:
    matrix = np.asarray(triples, dtype=float)
    k = matrix.shape[1]
    column_totals = matrix.sum(axis=0)
    row_totals = matrix.sum(axis=1)
    total = float(column_totals.sum())
    denominator = k * total - float(np.square(row_totals).sum())
    if denominator <= 0:
        return {"q": 0.0, "df": k - 1, "p_value": 1.0}
    q_value = (k - 1) * (
        k * float(np.square(column_totals).sum()) - total**2
    ) / denominator
    return {"q": float(q_value), "df": k - 1, "p_value": float(chi2.sf(q_value, k - 1))}


def holm_adjust(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * p_values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def mcnemar_tests(triples: list[tuple[int, int, int]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_p: list[float] = []
    for first, second in RUN_PAIRS:
        b = sum(values[first] == 1 and values[second] == 0 for values in triples)
        c = sum(values[first] == 0 and values[second] == 1 for values in triples)
        discordant = b + c
        p_value = (
            float(binomtest(min(b, c), discordant, 0.5, alternative="two-sided").pvalue)
            if discordant
            else 1.0
        )
        first_rate = sum(values[first] for values in triples) / len(triples)
        second_rate = sum(values[second] for values in triples) / len(triples)
        rows.append(
            {
                "run_pair": f"{first + 1}-{second + 1}",
                "losses": b,
                "gains": c,
                "discordant": discordant,
                "rate_delta_pp": 100 * (second_rate - first_rate),
                "p_value": p_value,
            }
        )
        raw_p.append(p_value)
    for row, adjusted in zip(rows, holm_adjust(raw_p), strict=True):
        row["holm_p_value"] = adjusted
    return rows


def clustered_meat(scores: np.ndarray, labels: list[Any]) -> np.ndarray:
    groups: dict[Any, np.ndarray] = {}
    for index, label in enumerate(labels):
        if label not in groups:
            groups[label] = np.zeros(scores.shape[1], dtype=float)
        groups[label] += scores[index]
    meat = sum((np.outer(value, value) for value in groups.values()), start=np.zeros((scores.shape[1], scores.shape[1])))
    group_count = len(groups)
    observation_count, parameter_count = scores.shape
    if group_count > 1 and observation_count > parameter_count:
        meat *= (group_count / (group_count - 1)) * (
            (observation_count - 1) / (observation_count - parameter_count)
        )
    return meat


def two_way_fixed_effect_run_model(
    rows: list[dict[str, Any]], endpoint: str, crossed_samples: dict[str, list[float]]
) -> dict[str, Any]:
    """Estimate direct run-rate effects with crossed fixed effects and uncertainty."""

    ordered = sorted(
        rows,
        key=lambda row: (
            int(row["run"]),
            PRIMARY_MODEL_ORDER.index(str(row["model"])),
            str(row["prompt_id"]),
        ),
    )
    prompts = sorted({str(row["prompt_id"]) for row in ordered})
    model_dummy = {model: index for index, model in enumerate(PRIMARY_MODEL_ORDER[1:])}
    prompt_dummy = {prompt: index for index, prompt in enumerate(prompts[1:])}
    parameter_count = 3 + len(model_dummy) + len(prompt_dummy)
    design = np.zeros((len(ordered), parameter_count), dtype=float)
    outcome = np.asarray([int(row[endpoint]) for row in ordered], dtype=float)
    design[:, 0] = 1.0
    model_offset = 3
    prompt_offset = model_offset + len(model_dummy)
    for index, row in enumerate(ordered):
        run_number = int(row["run"])
        if run_number == 2:
            design[index, 1] = 1.0
        elif run_number == 3:
            design[index, 2] = 1.0
        model = str(row["model"])
        prompt = str(row["prompt_id"])
        if model in model_dummy:
            design[index, model_offset + model_dummy[model]] = 1.0
        if prompt in prompt_dummy:
            design[index, prompt_offset + prompt_dummy[prompt]] = 1.0

    bread = np.linalg.pinv(design.T @ design, rcond=1e-12)
    beta = bread @ design.T @ outcome
    residuals = outcome - design @ beta
    scores = residuals[:, None] * design
    model_labels = [str(row["model"]) for row in ordered]
    prompt_labels = [str(row["prompt_id"]) for row in ordered]
    cell_labels = list(zip(model_labels, prompt_labels, strict=True))
    meat = (
        clustered_meat(scores, model_labels)
        + clustered_meat(scores, prompt_labels)
        - clustered_meat(scores, cell_labels)
    )
    covariance = bread @ meat @ bread
    covariance = (covariance + covariance.T) / 2

    contrast_specs = [
        ("run 2 vs run 1", 1, "pair_1_2_delta"),
        ("run 3 vs run 1", 2, "pair_1_3_delta"),
        ("run 3 vs run 2", None, "pair_2_3_delta"),
    ]
    contrasts: list[dict[str, Any]] = []
    for label, coefficient_index, sample_key in contrast_specs:
        contrast = np.zeros(parameter_count)
        if coefficient_index is None:
            contrast[2] = 1
            contrast[1] = -1
        else:
            contrast[coefficient_index] = 1
        estimate = float(contrast @ beta)
        if abs(estimate) < 1e-12:
            estimate = 0.0
        variance = float(contrast @ covariance @ contrast)
        cluster_se = math.sqrt(variance) if variance > 0 else 0.0
        samples = np.asarray(crossed_samples[sample_key], dtype=float)
        centered = samples - float(samples.mean())
        exceedances = int(np.count_nonzero(np.abs(centered) >= abs(estimate)))
        bootstrap_p = (exceedances + 1) / (len(centered) + 1)
        contrasts.append(
            {
                "contrast": label,
                "rate_delta": estimate,
                "rate_delta_pp": 100 * estimate,
                "two_way_cluster_standard_error": cluster_se,
                "two_way_cluster_wald_ci": {
                    "low": estimate - 1.96 * cluster_se,
                    "high": estimate + 1.96 * cluster_se,
                },
                "crossed_bootstrap_ci": interval(samples.tolist()),
                "crossed_bootstrap_p_value": bootstrap_p,
            }
        )

    run_beta = np.asarray([contrasts[0]["rate_delta"], contrasts[1]["rate_delta"]])
    bootstrap_vectors = np.column_stack(
        (crossed_samples["pair_1_2_delta"], crossed_samples["pair_1_3_delta"])
    )
    centered_vectors = bootstrap_vectors - bootstrap_vectors.mean(axis=0, keepdims=True)
    observed_joint_statistic = float(np.linalg.norm(run_beta, ord=2))
    null_joint_statistics = np.linalg.norm(centered_vectors, axis=1, ord=2)
    joint_exceedances = int(
        np.count_nonzero(null_joint_statistics >= observed_joint_statistic)
    )
    joint_p_value = (joint_exceedances + 1) / (len(null_joint_statistics) + 1)
    return {
        "endpoint": endpoint,
        "method": "linear-probability run-effect model with model and prompt fixed effects; crossed model-prompt bootstrap is primary and Cameron-Gelbach-Miller covariance is a sensitivity",
        "observations": len(ordered),
        "parameters": parameter_count,
        "model_clusters": len(set(model_labels)),
        "prompt_clusters": len(set(prompt_labels)),
        "covariance_min_eigenvalue": float(np.linalg.eigvalsh(covariance).min()),
        "contrasts": contrasts,
        "joint_run_effect_test": "empirical centered crossed-bootstrap L2 test of the Run 2 and Run 3 coefficient vector",
        "joint_run_effect_statistic": observed_joint_statistic,
        "joint_run_effect_p_value": joint_p_value,
    }


def per_model_mcnemar(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for endpoint in PRIMARY_ENDPOINTS:
        for model in PRIMARY_MODEL_ORDER:
            subset = [row for row in rows if str(row["model"]) == model]
            for comparison in mcnemar_tests(endpoint_triples(subset, endpoint)):
                output.append(
                    {
                        "endpoint": endpoint,
                        "model": model,
                        "model_label": MODEL_LABELS[model],
                        **comparison,
                    }
                )
    return output


def run_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for run_number in (1, 2, 3):
        subset = [row for row in rows if int(row["run"]) == run_number]
        n = len(subset)
        execution_count = sum(int(row["execution"]) for row in subset)
        signature_count = sum(int(row["signature"]) for row in subset)
        runnable_wrong_count = sum(int(row["runnable_wrong"]) for row in subset)
        qasm_count = sum(int(row["qasm3"]) for row in subset)
        gap_count = execution_count - signature_count
        if runnable_wrong_count != gap_count:
            raise AssertionError("R=E-M identity failed in run summary")
        summaries.append(
            {
                "run": run_number,
                "n": n,
                "execution_count": execution_count,
                "execution_rate": execution_count / n,
                "signature_count": signature_count,
                "signature_rate": signature_count / n,
                "qasm3_count": qasm_count,
                "qasm3_rate": qasm_count / n,
                "es_gap_count": gap_count,
                "es_gap_rate": gap_count / n,
                "runnable_wrong_count": runnable_wrong_count,
                "runnable_wrong_rate": runnable_wrong_count / n,
                "signature_wrong_given_execution": (
                    gap_count / execution_count if execution_count else math.nan
                ),
                "provider_error_count": sum(int(row["provider_error"]) for row in subset),
            }
        )
    return summaries


def recorded_transport_unaffected_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    affected_keys = {
        (str(row["model"]), str(row["prompt_id"]))
        for row in rows
        if int(row["transport_affected"])
    }
    subset = [
        row
        for row in rows
        if (str(row["model"]), str(row["prompt_id"])) not in affected_keys
    ]
    expected_per_run = len(subset) // 3
    if expected_per_run == 0 or len(subset) != 3 * expected_per_run:
        raise AssertionError("Recorded-transport-unaffected rows are not run-balanced")
    if any(
        sum(int(row["run"]) == run_number for row in subset) != expected_per_run
        for run_number in (1, 2, 3)
    ):
        raise AssertionError("Recorded-transport-unaffected denominators differ by run")
    return subset


def gate_bin_standardized_bootstrap(
    rows: list[dict[str, Any]], endpoint: str
) -> dict[str, list[float]]:
    cube, prompts = outcome_cube(rows, endpoint)
    prompt_bins = {
        str(row["prompt_id"]): str(row["gate_type_bin"])
        for row in rows
        if int(row["run"]) == 1 and str(row["model"]) == PRIMARY_MODEL_ORDER[0]
    }
    indices_by_bin = {
        gate_bin: np.asarray(
            [index for index, prompt_id in enumerate(prompts) if prompt_bins[prompt_id] == gate_bin],
            dtype=int,
        )
        for gate_bin in FULL_GATE_BIN_COUNTS
    }
    panel_bin_counts = {gate_bin: len(indices) for gate_bin, indices in indices_by_bin.items()}
    if any(count == 0 for count in panel_bin_counts.values()):
        raise AssertionError(
            f"The gate-bin-standardized audit is missing a prespecified gate bin: {panel_bin_counts}"
        )
    if len(set(panel_bin_counts.values())) != 1:
        raise AssertionError(
            "The gate-bin-standardized audit requires equal panel counts across gate bins; "
            f"observed {panel_bin_counts}"
        )
    total = sum(FULL_GATE_BIN_COUNTS.values())
    weights = {gate_bin: count / total for gate_bin, count in FULL_GATE_BIN_COUNTS.items()}
    rng = np.random.default_rng(
        BOOTSTRAP_SEED + 300_000 + sum(ord(char) for char in endpoint)
    )
    estimates = {f"run_rate_{run}": [] for run in (1, 2, 3)}
    model_count = cube.shape[0]
    for _ in range(BOOTSTRAP_REPLICATES):
        model_sample = rng.integers(0, model_count, size=model_count)
        weighted_rates = np.zeros(3, dtype=float)
        for gate_bin, indices in indices_by_bin.items():
            prompt_sample = rng.choice(indices, size=len(indices), replace=True)
            weighted_rates += weights[gate_bin] * cube[model_sample][:, prompt_sample, :].mean(
                axis=(0, 1)
            )
        for run_index, value in enumerate(weighted_rates, start=1):
            estimates[f"run_rate_{run_index}"].append(float(value))
    return estimates


def gate_bin_standardized_run_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(FULL_GATE_BIN_COUNTS.values())
    weights = {gate_bin: count / total for gate_bin, count in FULL_GATE_BIN_COUNTS.items()}
    bootstraps = {
        endpoint: gate_bin_standardized_bootstrap(rows, endpoint)
        for endpoint in PRIMARY_ENDPOINTS
    }
    output: list[dict[str, Any]] = []
    for run_number in (1, 2, 3):
        rates: dict[str, float] = {}
        stratum_rates: dict[str, dict[str, float]] = {}
        for endpoint in PRIMARY_ENDPOINTS:
            by_bin: dict[str, float] = {}
            for gate_bin in FULL_GATE_BIN_COUNTS:
                subset = [
                    row
                    for row in rows
                    if int(row["run"]) == run_number and str(row["gate_type_bin"]) == gate_bin
                ]
                by_bin[gate_bin] = sum(int(row[endpoint]) for row in subset) / len(subset)
            stratum_rates[endpoint] = by_bin
            rates[endpoint] = sum(weights[gate_bin] * by_bin[gate_bin] for gate_bin in weights)
        if not math.isclose(rates["runnable_wrong"], rates["execution"] - rates["signature"], abs_tol=1e-12):
            raise AssertionError("Gate-bin-standardized R=E-M identity failed")
        output.append(
            {
                "run": run_number,
                "weights": weights,
                "execution_rate": rates["execution"],
                "signature_rate": rates["signature"],
                "es_gap_rate": rates["runnable_wrong"],
                "execution_ci": interval(bootstraps["execution"][f"run_rate_{run_number}"]),
                "signature_ci": interval(bootstraps["signature"][f"run_rate_{run_number}"]),
                "es_gap_ci": interval(bootstraps["runnable_wrong"][f"run_rate_{run_number}"]),
                "stratum_rates": stratum_rates,
            }
        )
    return output


def stability_patterns(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for endpoint in PRIMARY_ENDPOINTS:
        triples = endpoint_triples(rows, endpoint)
        patterns = Counter("".join(str(value) for value in triple) for triple in triples)
        output[endpoint] = {
            "items": len(triples),
            "patterns": {pattern: patterns.get(pattern, 0) for pattern in [
                "000", "001", "010", "011", "100", "101", "110", "111"
            ]},
            "always_negative": patterns.get("000", 0),
            "always_positive": patterns.get("111", 0),
            "one_positive_run": sum(patterns.get(pattern, 0) for pattern in ("001", "010", "100")),
            "one_negative_run": sum(patterns.get(pattern, 0) for pattern in ("011", "101", "110")),
            "unanimous_rate": (patterns.get("000", 0) + patterns.get("111", 0)) / len(triples),
        }
    return output


def provider_attempt_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for run_number in (1, 2, 3):
        subset = [row for row in rows if int(row["run"]) == run_number]
        output.append(
            {
                "run": run_number,
                "trials": len(subset),
                "attempt_trace_covered_trials": sum(
                    int(row["attempt_trace_recorded"]) for row in subset
                ),
                "recorded_transport_attempts": sum(
                    int(row["attempt_count"])
                    for row in subset
                    if int(row["attempt_trace_recorded"])
                ),
                "first_attempt_transport_successes": sum(
                    int(row["initial_attempt_success"])
                    for row in subset
                    if int(row["attempt_trace_recorded"])
                ),
                "recovered_after_transport_error": sum(
                    int(row["recovered_after_transport_error"] or 0) for row in subset
                ),
                "terminal_provider_errors": sum(int(row["provider_error"]) for row in subset),
                "transport_affected_trials": sum(int(row["transport_affected"]) for row in subset),
            }
        )
    return output


def model_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for model in PRIMARY_MODEL_ORDER:
        model_rows = [row for row in rows if row["model"] == model]
        rates: dict[int, float] = {}
        execution_rates: dict[int, float] = {}
        for run_number in (1, 2, 3):
            subset = [row for row in model_rows if int(row["run"]) == run_number]
            rates[run_number] = sum(int(row["signature"]) for row in subset) / len(subset)
            execution_rates[run_number] = sum(int(row["execution"]) for row in subset) / len(subset)
        structural_triples = endpoint_triples(model_rows, "signature")
        execution_triples = endpoint_triples(model_rows, "execution")
        structural_agreement = agreement_stats(structural_triples)
        execution_agreement = agreement_stats(execution_triples)
        output.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "run_1_signature_rate": rates[1],
                "run_2_signature_rate": rates[2],
                "run_3_signature_rate": rates[3],
                "mean_signature_rate": float(np.mean(list(rates.values()))),
                "signature_range_pp": 100 * (max(rates.values()) - min(rates.values())),
                "run_1_execution_rate": execution_rates[1],
                "run_2_execution_rate": execution_rates[2],
                "run_3_execution_rate": execution_rates[3],
                "signature_any_flip_rate": structural_agreement["any_flip_rate"],
                "signature_gwet_ac1": structural_agreement["gwet_ac1"],
                "execution_any_flip_rate": execution_agreement["any_flip_rate"],
                "execution_gwet_ac1": execution_agreement["gwet_ac1"],
                "provider_errors": sum(int(row["provider_error"]) for row in model_rows),
            }
        )
    return output


def rank_stability(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rate_by_run = {
        run: [
            next(row for row in model_rows if row["model"] == model)[f"run_{run}_signature_rate"]
            for model in PRIMARY_MODEL_ORDER
        ]
        for run in (1, 2, 3)
    }
    output: list[dict[str, Any]] = []
    for first, second in ((1, 2), (1, 3), (2, 3)):
        spearman = spearmanr(rate_by_run[first], rate_by_run[second])
        kendall = kendalltau(rate_by_run[first], rate_by_run[second])
        first_map = dict(zip(PRIMARY_MODEL_ORDER, rate_by_run[first], strict=True))
        second_map = dict(zip(PRIMARY_MODEL_ORDER, rate_by_run[second], strict=True))

        def tie_inclusive_top_k(rate_map: dict[str, float]) -> set[str]:
            threshold = sorted(rate_map.values(), reverse=True)[TOP_K - 1]
            return {model for model, rate in rate_map.items() if rate >= threshold}

        first_top = tie_inclusive_top_k(first_map)
        second_top = tie_inclusive_top_k(second_map)
        union = first_top | second_top
        frontier = [model for model in PRIMARY_MODEL_ORDER if model in FRONTIER_MODELS]
        nonfrontier = [model for model in PRIMARY_MODEL_ORDER if model not in FRONTIER_MODELS]
        output.append(
            {
                "run_pair": f"{first}-{second}",
                "spearman_rho": float(spearman.statistic),
                "spearman_p_value": float(spearman.pvalue),
                "kendall_tau_b": float(kendall.statistic),
                "kendall_p_value": float(kendall.pvalue),
                "top_k_nominal": TOP_K,
                "run_first_top_tie_inclusive": sorted(first_top),
                "run_second_top_tie_inclusive": sorted(second_top),
                "top_k_jaccard": len(first_top & second_top) / len(union) if union else 1.0,
                "frontier_mean_first": float(np.mean([first_map[model] for model in frontier])),
                "frontier_mean_second": float(np.mean([second_map[model] for model in frontier])),
                "nonfrontier_mean_first": float(
                    np.mean([first_map[model] for model in nonfrontier])
                ),
                "nonfrontier_mean_second": float(
                    np.mean([second_map[model] for model in nonfrontier])
                ),
            }
        )
    return output


def majority_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_item: dict[tuple[str, str], dict[int, dict[str, int]]] = defaultdict(dict)
    for row in rows:
        by_item[(str(row["model"]), str(row["prompt_id"]))][int(row["run"])] = {
            endpoint: int(row[endpoint]) for endpoint in ENDPOINTS
        }
    majority: list[dict[str, Any]] = []
    for (model, prompt_id), by_run in sorted(by_item.items()):
        execution_majority = int(
            sum(by_run[run]["execution"] for run in (1, 2, 3)) >= 2
        )
        signature_majority = int(
            sum(by_run[run]["signature"] for run in (1, 2, 3)) >= 2
        )
        if signature_majority > execution_majority:
            raise AssertionError("Majority signature match cannot exceed majority execution")
        majority.append(
            {
                "model": model,
                "prompt_id": prompt_id,
                "execution": execution_majority,
                "signature": signature_majority,
                "runnable_wrong": execution_majority - signature_majority,
                "runwise_runnable_wrong_majority": int(
                    sum(by_run[run]["runnable_wrong"] for run in (1, 2, 3)) >= 2
                ),
                "qasm3": int(sum(by_run[run]["qasm3"] for run in (1, 2, 3)) >= 2),
            }
        )
    n = len(majority)
    execution_count = sum(row["execution"] for row in majority)
    signature_count = sum(row["signature"] for row in majority)
    runnable_wrong_count = sum(row["runnable_wrong"] for row in majority)
    runwise_runnable_wrong_majority_count = sum(
        row["runwise_runnable_wrong_majority"] for row in majority
    )
    if runnable_wrong_count != execution_count - signature_count:
        raise AssertionError("Majority R=E-M identity failed")
    run1 = next(row for row in run_summaries(rows) if row["run"] == 1)
    prompt_count = len({str(row["prompt_id"]) for row in majority})
    if prompt_count <= 0:
        raise AssertionError("Majority summary has no prompt rows")
    majority_model_rates = [
        sum(row["signature"] for row in majority if row["model"] == model)
        / prompt_count
        for model in PRIMARY_MODEL_ORDER
    ]
    run1_model_rates = [
        sum(
            int(row["signature"])
            for row in rows
            if row["model"] == model and int(row["run"]) == 1
        )
        / prompt_count
        for model in PRIMARY_MODEL_ORDER
    ]
    rank = spearmanr(run1_model_rates, majority_model_rates)
    return {
        "n": n,
        "execution_count": execution_count,
        "execution_rate": execution_count / n,
        "signature_count": signature_count,
        "signature_rate": signature_count / n,
        "es_gap_count": runnable_wrong_count,
        "es_gap_rate": runnable_wrong_count / n,
        "runwise_runnable_wrong_majority_count": runwise_runnable_wrong_majority_count,
        "runwise_runnable_wrong_majority_rate": runwise_runnable_wrong_majority_count / n,
        "signature_delta_from_run_1_pp": 100 * (signature_count / n - run1["signature_rate"]),
        "execution_delta_from_run_1_pp": 100 * (execution_count / n - run1["execution_rate"]),
        "model_rank_spearman_vs_run_1": float(rank.statistic),
        "model_rank_spearman_p_value": float(rank.pvalue),
    }


def stratum_agreement(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specifications = [
        ("cohort", ["pilot", "extension"]),
        ("gate_type_bin", ["1-2", "3-4", "5+"]),
        ("has_barrier", [False, True]),
    ]
    output: list[dict[str, Any]] = []
    for field, levels in specifications:
        for level in levels:
            subset = [row for row in rows if row[field] == level]
            for endpoint in PRIMARY_ENDPOINTS:
                stats = agreement_stats(endpoint_triples(subset, endpoint))
                output.append(
                    {
                        "stratum": field,
                        "level": str(level).lower(),
                        "endpoint": endpoint,
                        **stats,
                    }
                )
    return output


def difficulty_stratum_run_rates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Report the prespecified cohort, diversity, and barrier gradients by run."""

    specifications = [
        ("cohort", ["pilot", "extension"]),
        ("gate_type_bin", ["1-2", "3-4", "5+"]),
        ("has_barrier", [False, True]),
    ]
    output: list[dict[str, Any]] = []
    for field, levels in specifications:
        for level in levels:
            record: dict[str, Any] = {
                "stratum": field,
                "level": str(level).lower(),
            }
            for run_number in (1, 2, 3):
                subset = [
                    row
                    for row in rows
                    if int(row["run"]) == run_number and row[field] == level
                ]
                record[f"run_{run_number}_n"] = len(subset)
                for endpoint in PRIMARY_ENDPOINTS:
                    record[f"run_{run_number}_{endpoint}_rate"] = (
                        sum(int(row[endpoint]) for row in subset) / len(subset)
                    )
            output.append(record)
    return output


def sequential_replication_summary(
    rows: list[dict[str, Any]], panel_manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    """Compare the frozen original and confirmatory halves when available."""

    if not panel_manifest.get("selection_is_sequential_augmentation"):
        return []

    source_keys = (
        ("original_36", "source_original_manifest"),
        ("confirmatory_36", "source_augmentation_manifest"),
    )
    layer_ids: dict[str, set[str]] = {}
    for layer, key in source_keys:
        source_path = SUBMISSION_DIR / str(panel_manifest.get(key) or "")
        if not source_path.is_file():
            raise FileNotFoundError(f"Sequential-replication manifest missing: {source_path}")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        ids = {str(record["prompt_id"]) for record in source["selected_prompts"]}
        if len(ids) != len(source["selected_prompts"]):
            raise AssertionError(f"Duplicate prompt IDs in {layer} manifest")
        layer_ids[layer] = ids

    if layer_ids["original_36"] & layer_ids["confirmatory_36"]:
        raise AssertionError("Original and confirmatory prompt panels overlap")
    observed_ids = {str(row["prompt_id"]) for row in rows}
    if layer_ids["original_36"] | layer_ids["confirmatory_36"] != observed_ids:
        raise AssertionError("Sequential panel manifests do not partition the pooled panel")

    layers = [
        ("original 36", layer_ids["original_36"]),
        ("confirmatory 36", layer_ids["confirmatory_36"]),
        ("pooled 72", observed_ids),
    ]
    output: list[dict[str, Any]] = []
    for label, prompt_ids in layers:
        subset = [row for row in rows if str(row["prompt_id"]) in prompt_ids]
        full_runs = run_summaries(subset)
        unaffected = recorded_transport_unaffected_rows(subset)
        unaffected_runs = run_summaries(unaffected)

        def mean_pairwise_agreement(endpoint: str) -> float:
            triples = endpoint_triples(unaffected, endpoint)
            equal_pairs = sum(
                int(values[0] == values[1])
                + int(values[0] == values[2])
                + int(values[1] == values[2])
                for values in triples
            )
            return equal_pairs / (3 * len(triples))

        gate_bins: dict[str, list[float]] = {}
        for gate_bin in ("1-2", "3-4", "5+"):
            gate_bins[gate_bin] = []
            for run_number in (1, 2, 3):
                bin_rows = [
                    row
                    for row in subset
                    if int(row["run"]) == run_number
                    and str(row["gate_type_bin"]) == gate_bin
                ]
                if not bin_rows:
                    raise AssertionError(f"Empty {gate_bin} stratum in {label}")
                gate_bins[gate_bin].append(
                    sum(int(row["signature"]) for row in bin_rows) / len(bin_rows)
                )

        output.append(
            {
                "evidence_layer": label,
                "prompts": len(prompt_ids),
                "cells_per_run": len(subset) // 3,
                "full_run_execution_rates": [row["execution_rate"] for row in full_runs],
                "full_run_signature_rates": [row["signature_rate"] for row in full_runs],
                "full_run_es_gap_rates": [row["es_gap_rate"] for row in full_runs],
                "common_cells_per_run": len(unaffected) // 3,
                "common_execution_range": [
                    min(row["execution_rate"] for row in unaffected_runs),
                    max(row["execution_rate"] for row in unaffected_runs),
                ],
                "common_signature_range": [
                    min(row["signature_rate"] for row in unaffected_runs),
                    max(row["signature_rate"] for row in unaffected_runs),
                ],
                "common_es_gap_range": [
                    min(row["es_gap_rate"] for row in unaffected_runs),
                    max(row["es_gap_rate"] for row in unaffected_runs),
                ],
                "common_execution_pairwise_agreement": mean_pairwise_agreement("execution"),
                "common_signature_pairwise_agreement": mean_pairwise_agreement("signature"),
                "gate_bin_signature_rates": gate_bins,
            }
        )
    return output


def exact_code_agreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    text_hashes: dict[tuple[str, str], dict[int, str]] = defaultdict(dict)
    ast_hashes: dict[tuple[str, str], dict[int, str]] = defaultdict(dict)
    for row in rows:
        key = (str(row["model"]), str(row["prompt_id"]))
        text_hashes[key][int(row["run"])] = str(row["normalized_text_sha256"])
        ast_hashes[key][int(row["run"])] = str(row["ast_sha256"])

    def equality_summary(
        hashes: dict[tuple[str, str], dict[int, str]]
    ) -> dict[str, Any]:
        by_item = list(hashes.values())
        complete = [
            tuple(by_run[run] for run in (1, 2, 3))
            for by_run in by_item
            if all(by_run.get(run) for run in (1, 2, 3))
        ]
        all_equal = sum(len(set(values)) == 1 for values in complete)
        pair_equal = sum(
            int(values[0] == values[1])
            + int(values[0] == values[2])
            + int(values[1] == values[2])
            for values in complete
        )
        pairwise_rates: dict[str, float] = {}
        pairwise_denominators: dict[str, int] = {}
        for first, second in RUN_PAIRS:
            first_run = first + 1
            second_run = second + 1
            eligible = [
                by_run
                for by_run in by_item
                if by_run.get(first_run) and by_run.get(second_run)
            ]
            label = f"{first_run}-{second_run}"
            pairwise_denominators[label] = len(eligible)
            pairwise_rates[label] = (
                sum(by_run[first_run] == by_run[second_run] for by_run in eligible)
                / len(eligible)
                if eligible
                else math.nan
            )
        return {
            "nonempty_three_run_items": len(complete),
            "all_three_equal_rate": all_equal / len(complete) if complete else math.nan,
            "pairwise_equal_rate": pair_equal / (3 * len(complete)) if complete else math.nan,
            "pairwise_equal_rates": pairwise_rates,
            "pairwise_denominators": pairwise_denominators,
        }

    return {
        "normalized_text": equality_summary(text_hashes),
        "canonical_ast": equality_summary(ast_hashes),
        "normalization_contract": {
            "normalized_text": [
                "convert CRLF/CR to LF",
                "remove one outer Markdown Python code fence",
                "strip leading and trailing blank lines",
                "strip trailing whitespace",
                "collapse consecutive blank lines",
                "preserve comments, identifiers, literals, statement order, indentation, and interior token spacing",
            ],
            "canonical_ast": [
                "parse normalized text with Python ast.parse",
                "serialize ast.dump with annotate_fields=True and include_attributes=False",
                "preserve identifiers, literal values, operand structure, and statement order",
                "do not canonicalize variable renaming or reorder statements",
            ],
        },
        "ast_parse_successful_outputs": sum(int(row["ast_parse_success"]) for row in rows),
        "total_outputs": len(rows),
    }


def provenance_manifest(root: Path, analysis_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or analysis_dir in path.parents:
            continue
        files.append(
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": "pqid-bench-stochastic-repeatability-file-manifest-v1",
        "file_count": len(files),
        "files": files,
    }


def plot_figure(output_dir: Path, run_rows: list[dict[str, Any]], model_rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 9,
            "svg.fonttype": "none",
        }
    )
    colors = {"execution": "#147D73", "signature": "#315DA8", "gap": "#C35B0B"}
    fig = plt.figure(figsize=(10.8, 9.2), constrained_layout=False)
    grid = fig.add_gridspec(2, 1, height_ratios=[1.0, 3.3], hspace=0.34)

    ax_top = fig.add_subplot(grid[0])
    runs = [row["run"] for row in run_rows]
    execution = [100 * row["execution_rate"] for row in run_rows]
    signature = [100 * row["signature_rate"] for row in run_rows]
    gap = [100 * row["es_gap_rate"] for row in run_rows]
    ax_top.plot(runs, execution, marker="o", linewidth=2.1, color=colors["execution"], label="Execution")
    ax_top.plot(runs, signature, marker="s", linewidth=2.1, color=colors["signature"], label="Reference-signature match")
    ax_top.plot(runs, gap, marker="D", linewidth=1.8, color=colors["gap"], label="ES-Gap (pp)")
    ax_top.set_xticks(runs, [f"Run {run}" for run in runs])
    ax_top.set_ylabel("Rate (%) or difference (pp)")
    ax_top.set_ylim(0, 100)
    ax_top.grid(axis="y", color="#D7DEE8", linewidth=0.7)
    ax_top.spines[["top", "right"]].set_visible(False)
    ax_top.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    ax_top.text(-0.055, 1.05, "A", transform=ax_top.transAxes, fontweight="bold", fontsize=12)

    ax_bottom = fig.add_subplot(grid[1])
    ordered = sorted(model_rows, key=lambda row: row["mean_signature_rate"])
    y = np.arange(len(ordered))
    for index, row in enumerate(ordered):
        rates = [100 * row[f"run_{run}_signature_rate"] for run in (1, 2, 3)]
        ax_bottom.hlines(index, min(rates), max(rates), color="#9AA8B8", linewidth=2.2, zorder=1)
        ax_bottom.scatter(rates, [index] * 3, color=["#147D73", "#315DA8", "#C35B0B"], s=26, zorder=2)
    ax_bottom.set_yticks(y, [row["model_label"] for row in ordered])
    ax_bottom.set_xlabel("Reference-signature match (%)")
    ax_bottom.set_xlim(0, 100)
    ax_bottom.grid(axis="x", color="#E0E5EC", linewidth=0.7)
    ax_bottom.spines[["top", "right", "left"]].set_visible(False)
    ax_bottom.tick_params(axis="y", length=0)
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=color, label=f"Run {run}")
        for run, color in zip((1, 2, 3), ("#147D73", "#315DA8", "#C35B0B"), strict=True)
    ]
    ax_bottom.legend(handles=handles, frameon=False, ncol=3, loc="lower right")
    ax_bottom.text(-0.055, 1.02, "B", transform=ax_bottom.transAxes, fontweight="bold", fontsize=12)
    fig.subplots_adjust(left=0.24, right=0.985, top=0.945, bottom=0.07)
    for suffix in ("svg", "png"):
        fig.savefig(output_dir / f"pqid_bench_stochastic_repeatability_panel.{suffix}", dpi=300)
    plt.close(fig)


def write_markdown(path: Path, analysis: dict[str, Any]) -> None:
    def ci_pct(ci: dict[str, float]) -> str:
        return f"[{pct(ci['low'])}, {pct(ci['high'])}]"

    def ci_pp(ci: dict[str, float]) -> str:
        return f"[{100 * ci['low']:.2f}, {100 * ci['high']:.2f}] pp"

    prompt_count = int(analysis["design"]["prompts"])
    rate_resolution = 100 / prompt_count
    lines = [
        "# PQID-Bench Stochastic Repeatability Audit",
        "",
        "Run 1 is the frozen canonical benchmark output. Runs 2 and 3 are two new",
        f"single-generation invocations on an outcome-blind, signature-unique {prompt_count}-prompt",
        "panel. The provider route, model identifier, provider request body, evaluator,",
        "and target are held fixed. Runs 2--3 estimate short-window API repeatability;",
        "Run 1 comparisons additionally include temporal deployment drift.",
        f"Stored request hashes are identical across all three runs for all `{analysis['request_identity_audit']['model_prompt_requests']}` model-prompt pairs.",
        f"The frozen panel hash and report target metadata are verified for all `{analysis['target_identity_audit']['scored_cells']}` scored cells.",
        (
            "Canonical completeness: expected `{expected}` cells; observed `{observed}`; "
            "missing `{missing}`; duplicate keys `{duplicates}`; unexpected keys "
            "`{unexpected}`; request-hash mismatches `{request_mismatches}`; "
            "target-metadata mismatches `{target_mismatches}`."
        ).format(
            expected=analysis["canonical_completeness"]["expected_cells"],
            observed=analysis["canonical_completeness"]["observed_cells"],
            missing=analysis["canonical_completeness"]["missing_cells"],
            duplicates=analysis["canonical_completeness"]["duplicate_keys"],
            unexpected=analysis["canonical_completeness"]["unexpected_keys"],
            request_mismatches=analysis["canonical_completeness"]["request_hash_mismatches"],
            target_mismatches=analysis["canonical_completeness"]["target_metadata_mismatches"],
        ),
        "",
        "The scored endpoint is the nonredundant predicate",
        "`M = Q AND K AND T`, where each component is execution-gated and `T` is complete operation-type count-map equality.",
        "Scalar gate-count agreement `G` remains a diagnostic; the analyzer asserts the",
        "frozen count-map invariant `T => G` for every evaluated output.",
        "Historical artifact fields `gate_types`, `gate_type_bin`, and `gate_entropy` encode",
        "the evaluator-visible operation vocabulary, including barriers and measurements.",
        "",
    ]
    if analysis["sequential_replication"]:
        lines.extend(
            [
                "## Sequential Replication Comparison",
                "",
                "The original and confirmatory halves are signature-disjoint; the confirmatory panel was frozen before transmission.",
                "Full-panel entries give Runs 1/2/3. Common-cell ranges and agreement use one denominator with no recorded transport disturbance in any run within each evidence layer.",
                "Agreement is the mean of the three pairwise equality rates (Runs 1--2, 1--3, and 2--3) on that same common set; it is distinct from unanimous three-run agreement.",
                "",
                "| evidence layer | full execution R1/R2/R3 | full signature R1/R2/R3 | full ES-Gap R1/R2/R3 (pp) | common cells/run | common execution range | common signature range | common ES-Gap range (pp) | execution agreement | signature agreement |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in analysis["sequential_replication"]:
            rates = lambda values: "/".join(pct(value) for value in values)
            gaps = lambda values: "/".join(pp(value) for value in values)
            ranges = lambda values: f"{pct(values[0])}--{pct(values[1])}"
            gap_range = lambda values: f"{100 * values[0]:.2f}--{100 * values[1]:.2f} pp"
            lines.append(
                f"| {row['evidence_layer']} | {rates(row['full_run_execution_rates'])} | "
                f"{rates(row['full_run_signature_rates'])} | {gaps(row['full_run_es_gap_rates'])} | "
                f"{row['common_cells_per_run']} | {ranges(row['common_execution_range'])} | "
                f"{ranges(row['common_signature_range'])} | {gap_range(row['common_es_gap_range'])} | "
                f"{pct(row['common_execution_pairwise_agreement'])} | "
                f"{pct(row['common_signature_pairwise_agreement'])} |"
            )
        lines.extend(
            [
                "",
                "| evidence layer | 1--2 types, R1/R2/R3 | 3--4 types, R1/R2/R3 | 5+ types, R1/R2/R3 |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for row in analysis["sequential_replication"]:
            rates = lambda values: "/".join(pct(value) for value in values)
            lines.append(
                f"| {row['evidence_layer']} | {rates(row['gate_bin_signature_rates']['1-2'])} | "
                f"{rates(row['gate_bin_signature_rates']['3-4'])} | "
                f"{rates(row['gate_bin_signature_rates']['5+'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Panel-Unweighted Outcomes",
            "",
            f"Crossed intervals independently resample the 21 model rows and {prompt_count} prompt signatures.",
            "",
            "| run | cells | execution (95% CI) | signature match (95% CI) | ES-Gap (95% CI; pp) | wrong signature given execution | provider errors |",
            "| ---: | ---: | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in analysis["run_summaries"]:
        lines.append(
            f"| {row['run']} | {row['n']} | {pct(row['execution_rate'])} "
            f"{ci_pct(row['execution_crossed_ci'])} | {pct(row['signature_rate'])} "
            f"{ci_pct(row['signature_crossed_ci'])} | {pp(row['es_gap_rate'])} "
            f"{ci_pp(row['es_gap_crossed_ci'])} | "
            f"{pct(row['signature_wrong_given_execution'])} | {row['provider_error_count']} |"
        )

    lines.extend(
        [
            "",
            "## Secondary Operation-Type-Bin-Standardized Panel Outcomes",
            "",
            "These sensitivities weight only the panel's three operation-diversity bands to the",
            "full 154-prompt frequencies (`42/154`, `85/154`, and `27/154`). They neither",
            "correct the panel's signature uniqueness, identifiability exclusions, cohort",
            "balance, or barrier balance nor estimate an unbiased full-population rate.",
            "They do not replace the prespecified balanced-panel analysis.",
            "",
            "| run | execution (95% CI) | signature match (95% CI) | ES-Gap (95% CI; pp) |",
            "| ---: | --- | --- | --- |",
        ]
    )
    for row in analysis["gate_bin_standardized_run_summaries"]:
        lines.append(
            f"| {row['run']} | {pct(row['execution_rate'])} {ci_pct(row['execution_ci'])} | "
            f"{pct(row['signature_rate'])} {ci_pct(row['signature_ci'])} | "
            f"{pp(row['es_gap_rate'])} {ci_pp(row['es_gap_ci'])} |"
        )

    lines.extend(
        [
            "",
            "## Difficulty-Gradient Reproducibility",
            "",
            "Rates below retain the balanced panel denominator and show whether the",
            "prespecified cohort, operation-diversity, and barrier contrasts point in the same",
            "direction across all three draws.",
            "",
            "| stratum | level | execution runs 1 / 2 / 3 | signature runs 1 / 2 / 3 | ES-Gap runs 1 / 2 / 3 (pp) |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in analysis["difficulty_stratum_run_rates"]:
        lines.append(
            f"| {row['stratum']} | {row['level']} | "
            f"{pct(row['run_1_execution_rate'])} / {pct(row['run_2_execution_rate'])} / {pct(row['run_3_execution_rate'])} | "
            f"{pct(row['run_1_signature_rate'])} / {pct(row['run_2_signature_rate'])} / {pct(row['run_3_signature_rate'])} | "
            f"{pp(row['run_1_runnable_wrong_rate'])} / {pp(row['run_2_runnable_wrong_rate'])} / {pp(row['run_3_runnable_wrong_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Primary Run-Effect Inference",
            "",
            "Each endpoint uses a linear-probability run-effect model with model and prompt",
            "fixed effects. Crossed model-prompt bootstrap intervals are primary;",
            "Cameron--Gelbach--Miller two-way clustered covariance is retained as a",
            "sensitivity. This parameterization directly estimates the prespecified",
            "percentage-point run-rate differences and avoids separation at high execution",
            "prevalence. The empirical joint crossed-bootstrap test assesses whether both",
            "later-run effects are zero and remains defined under singular covariance.",
            "",
            "| endpoint | contrast | delta pp (crossed 95% CI) | crossed p | joint run-effect p |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for endpoint, model in analysis["run_effect_models"].items():
        for index, contrast in enumerate(model["contrasts"]):
            joint_p = f"{model['joint_run_effect_p_value']:.4g}" if index == 0 else ""
            ci = contrast["crossed_bootstrap_ci"]
            lines.append(
                f"| {ENDPOINTS[endpoint]} | {contrast['contrast']} | "
                f"{contrast['rate_delta_pp']:+.2f} [{100 * ci['low']:+.2f}, "
                f"{100 * ci['high']:+.2f}] | {contrast['crossed_bootstrap_p_value']:.4g} | "
                f"{joint_p} |"
            )

    lines.extend(
        [
            "",
            "## Three-Run Endpoint Repeatability",
            "",
            "Crossed intervals are primary. Prompt-cluster intervals with the model roster",
            "held fixed are retained in the JSON artifact. Cochran's Q is descriptive only",
            "because its ordinary independence assumption does not match the crossed matrix.",
            "",
            "| endpoint | items | unanimous | any flip (crossed 95% CI) | Gwet AC1 (crossed 95% CI) | descriptive Cochran Q p |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for endpoint, row in analysis["endpoint_repeatability"].items():
        ci = row["gwet_ac1_crossed_model_prompt_ci"]
        flip_ci = row["any_flip_crossed_model_prompt_ci"]
        q = row["cochran_q_descriptive_sensitivity"]
        lines.append(
            f"| {ENDPOINTS[endpoint]} | {row['items']} | {pct(row['unanimous_rate'])} | "
            f"{pct(row['any_flip_rate'])} [{pct(flip_ci['low'])}, {pct(flip_ci['high'])}] | "
            f"{row['gwet_ac1']:.3f} [{ci['low']:.3f}, {ci['high']:.3f}] | {q['p_value']:.4g} |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Agreement And Directional Churn",
            "",
            "The 2--3 comparison is the short-window contrast. Comparisons involving Run 1",
            "also contain temporal deployment variation.",
            "",
            "| endpoint | runs | agreement (crossed 95% CI) | Gwet AC1 (crossed 95% CI) | loss | gain | total flip | delta (pp; crossed 95% CI) | exact McNemar Holm p* |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for endpoint, comparisons in analysis["paired_run_effects"].items():
        pair_lookup = {
            row["run_pair"]: row
            for row in analysis["endpoint_repeatability"][endpoint]["pairwise_run_agreement"]
        }
        for comparison in comparisons:
            pair = pair_lookup[comparison["run_pair"]]
            agreement_ci = pair["agreement_crossed_ci"]
            ac1_ci = pair["gwet_ac1_crossed_ci"]
            delta_ci = comparison["rate_delta_crossed_model_prompt_ci_pp"]
            lines.append(
                f"| {ENDPOINTS[endpoint]} | {comparison['run_pair']} | "
                f"{pct(pair['agreement'])} [{pct(agreement_ci['low'])}, {pct(agreement_ci['high'])}] | "
                f"{pair['gwet_ac1']:.3f} [{ac1_ci['low']:.3f}, {ac1_ci['high']:.3f}] | "
                f"{pct(comparison['loss_rate'])} | {pct(comparison['gain_rate'])} | "
                f"{pct(pair['flip_rate'])} | {comparison['rate_delta_pp']:+.2f} "
                f"[{delta_ci['low']:+.2f}, {delta_ci['high']:+.2f}] | "
                f"{comparison['holm_p_value']:.4g} |"
            )
    lines.extend(
        [
            "",
            "*The pooled exact McNemar result is a familiar paired-cell sensitivity, not",
            "the primary crossed-dependence test. Per-model exact McNemar results are",
            "provided as a separate CSV artifact.",
            "",
            "## Three-Run Stability Classes",
            "",
            "| endpoint | always 0 | always 1 | one positive run | one negative run | unanimous |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for endpoint, row in analysis["three_run_stability_patterns"].items():
        lines.append(
            f"| {ENDPOINTS[endpoint]} | {row['always_negative']} | {row['always_positive']} | "
            f"{row['one_positive_run']} | {row['one_negative_run']} | "
            f"{pct(row['unanimous_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Model-Level Signature Stability",
            "",
            "| model | run 1 | run 2 | run 3 | range (pp) | any flip | Gwet AC1 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in analysis["model_summaries"]:
        lines.append(
            f"| {row['model_label']} | {pct(row['run_1_signature_rate'])} | "
            f"{pct(row['run_2_signature_rate'])} | {pct(row['run_3_signature_rate'])} | "
            f"{row['signature_range_pp']:.2f} | {pct(row['signature_any_flip_rate'])} | "
            f"{row['signature_gwet_ac1']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Deployment-Level Model-Ordering Stability",
            "",
            f"Exact ranks move in {rate_resolution:.2f}-point increments on {prompt_count} prompts, so the audit reports",
            "rank correlations and tie-inclusive top-five overlap rather than treating every",
            "one-position change as substantive.",
            "These raw ranks retain provider failures and therefore describe deployment-level ordering, not a capability ranking on the common no-recorded-disturbance subset.",
            "",
            "| runs | Spearman rho | Kendall tau-b | top-five Jaccard | frontier mean first -> second |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in analysis["rank_stability"]:
        lines.append(
            f"| {row['run_pair']} | {row['spearman_rho']:.3f} | {row['kendall_tau_b']:.3f} | "
            f"{row['top_k_jaccard']:.3f} | {pct(row['frontier_mean_first'])} -> "
            f"{pct(row['frontier_mean_second'])} |"
        )

    majority = analysis["majority_vote_sensitivity"]
    code = analysis["exact_code_agreement"]
    text_code = code["normalized_text"]
    ast_code = code["canonical_ast"]
    lines.extend(
        [
            "",
            "## Ranking And Majority-Vote Sensitivities",
            "",
            f"- Majority-vote signature rate: `{pct(majority['signature_rate'])}`; change from run 1: `{majority['signature_delta_from_run_1_pp']:+.2f}` percentage points.",
            f"- Majority-vote ES-Gap, derived as `E^maj - M^maj`: `{pp(majority['es_gap_rate'])}`.",
            f"- Direct majority vote over the three runwise `R` indicators (diagnostic): `{pct(majority['runwise_runnable_wrong_majority_rate'])}`.",
            f"- Majority-vote versus run-1 model-rank Spearman correlation: `{majority['model_rank_spearman_vs_run_1']:.3f}`.",
            "- Majority vote is a three-query deployment sensitivity, not a replacement for the canonical single-draw score.",
            "",
            "## Generated-Code Reproducibility",
            "",
            f"- Formatting-normalized text equality across all three runs: `{pct(text_code['all_three_equal_rate'])}` among `{text_code['nonempty_three_run_items']}` complete cells.",
            f"- Normalized-text pairwise equality (1--2 / 1--3 / 2--3): `{pct(text_code['pairwise_equal_rates']['1-2'])}` (`n={text_code['pairwise_denominators']['1-2']}`) / `{pct(text_code['pairwise_equal_rates']['1-3'])}` (`n={text_code['pairwise_denominators']['1-3']}`) / `{pct(text_code['pairwise_equal_rates']['2-3'])}` (`n={text_code['pairwise_denominators']['2-3']}`).",
            f"- Canonical Python-AST equality across all three runs: `{pct(ast_code['all_three_equal_rate'])}` among `{ast_code['nonempty_three_run_items']}` parseable complete cells.",
            f"- Canonical-AST pairwise equality (1--2 / 1--3 / 2--3): `{pct(ast_code['pairwise_equal_rates']['1-2'])}` (`n={ast_code['pairwise_denominators']['1-2']}`) / `{pct(ast_code['pairwise_equal_rates']['1-3'])}` (`n={ast_code['pairwise_denominators']['1-3']}`) / `{pct(ast_code['pairwise_equal_rates']['2-3'])}` (`n={ast_code['pairwise_denominators']['2-3']}`).",
            f"- AST parse successes: `{code['ast_parse_successful_outputs']} / {code['total_outputs']}` outputs.",
            "- Neither normalization renames identifiers or reorders statements; AST equality remains stricter than functional equivalence.",
            "",
            "## Provider-Attempt Audit",
            "",
            "| run | trials | trace covered | recorded attempts | first-attempt success | recovered | terminal errors | known transport affected |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in analysis["provider_attempt_summary"]:
        lines.append(
            f"| {row['run']} | {row['trials']} | {row['attempt_trace_covered_trials']} | "
            f"{row['recorded_transport_attempts']} | "
            f"{row['first_attempt_transport_successes']} | {row['recovered_after_transport_error']} | "
            f"{row['terminal_provider_errors']} | {row['transport_affected_trials']} |"
        )
    unaffected_runs = analysis["recorded_transport_unaffected_run_summaries"]
    unaffected_repeatability = analysis["recorded_transport_unaffected_repeatability"]
    lines.extend(
        [
            "",
            "### Common No-Recorded-Disturbance Complete-Cell Sensitivity",
            "",
            "This secondary analysis retains only model--prompt pairs with no recorded",
            "transport disturbance in any of the three runs, giving one common denominator",
            f"of `{unaffected_runs[0]['n']}` cells per run. It separates known endpoint",
            "availability failures from outcome variation, but untraced legacy and batch",
            "rows cannot be certified as first-attempt clean.",
            "",
            "| run | cells | execution | signature match | ES-Gap (pp) | wrong signature given execution |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in unaffected_runs:
        lines.append(
            f"| {row['run']} | {row['n']} | {pct(row['execution_rate'])} | "
            f"{pct(row['signature_rate'])} | {pp(row['es_gap_rate'])} | "
            f"{pct(row['signature_wrong_given_execution'])} |"
        )
    lines.extend(
        [
            "",
            "Complete-cell three-run repeatability: execution agreement "
            f"`{pct(unaffected_repeatability['execution']['pairwise_agreement'])}` "
            f"(Gwet AC1 `{unaffected_repeatability['execution']['gwet_ac1']:.3f}`); "
            "signature agreement "
            f"`{pct(unaffected_repeatability['signature']['pairwise_agreement'])}` "
            f"(Gwet AC1 `{unaffected_repeatability['signature']['gwet_ac1']:.3f}`).",
        ]
    )
    lines.extend(
        [
            "",
            "Direct-route trials permit at most three transport attempts with 1 s and 2 s",
            "local backoff. Retry is allowed only before a valid provider response exists.",
            "Refusal, truncation, empty generation, execution failure, and signature failure",
            "are never retry triggers. The first valid response is canonical; no best-of-n",
            "selection occurs. OpenAI Batch items are submitted once and retain the provider-",
            "managed batch lifecycle rather than receiving local response-level retries.",
            "The common no-recorded-disturbance sensitivity excludes any trial with a known",
            "transport disturbance and does not replace the full analysis. Legacy or batch",
            "rows without local attempt traces remain explicitly identifiable as untraced.",
            "",
            "## Interpretation Boundary",
            "",
            "This is a repeatability audit under fixed deployed endpoints, not a claim that",
            "hosted model snapshots are permanently reproducible. High endpoint agreement",
            "supports the stability of the benchmark conclusions under repeated decoding;",
            "observed flips quantify deployment and decoding variability that must remain in",
            "the uncertainty budget. Crossed intervals condition on the three observed run",
            "occasions: they generalize over the audited model and prompt dimensions, not over",
            "an unobserved population of future API dates or common deployment shocks. The",
            "audit does not identify a causal source of a flip.",
            "",
            "## Artifacts",
            "",
            f"- Cell outcomes: `{analysis['artifact_paths']['cell_outcomes']}`",
            f"- Model summary: `{analysis['artifact_paths']['model_summary']}`",
            f"- Per-model McNemar sensitivity: `{analysis['artifact_paths']['per_model_mcnemar']}`",
            f"- File manifest: `{analysis['artifact_paths']['file_manifest']}`",
            f"- Figure: `{analysis['artifact_paths']['figure_svg']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(root: Path, output_dir: Path) -> None:
    protocol_freeze = verify_protocol_freeze(root)
    cells, metadata = load_cell_rows(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_count = len({str(row["prompt_id"]) for row in cells})
    run_rows = run_summaries(cells)
    transport_unaffected_cells = recorded_transport_unaffected_rows(cells)
    transport_unaffected_run_rows = run_summaries(transport_unaffected_cells)
    model_rows = model_summaries(cells)

    repeatability: dict[str, Any] = {}
    complete_repeatability: dict[str, Any] = {}
    paired_effects: dict[str, Any] = {}
    crossed_bootstraps: dict[str, dict[str, list[float]]] = {}
    for endpoint in ENDPOINTS:
        triples = endpoint_triples(cells, endpoint)
        stats = agreement_stats(triples)
        crossed = bootstrap_metric_samples(cells, endpoint, resample_models=True)
        prompt_fixed_roster = bootstrap_metric_samples(cells, endpoint, resample_models=False)
        crossed_bootstraps[endpoint] = crossed
        pairwise = pairwise_agreement_stats(triples)
        for row in pairwise:
            pair_key = row["run_pair"].replace("-", "_")
            row["agreement_crossed_ci"] = interval(crossed[f"pair_{pair_key}_agreement"])
            row["gwet_ac1_crossed_ci"] = interval(crossed[f"pair_{pair_key}_gwet_ac1"])
            row["flip_crossed_ci"] = interval(crossed[f"pair_{pair_key}_flip_rate"])
            row["agreement_prompt_cluster_ci"] = interval(
                prompt_fixed_roster[f"pair_{pair_key}_agreement"]
            )
            row["gwet_ac1_prompt_cluster_ci"] = interval(
                prompt_fixed_roster[f"pair_{pair_key}_gwet_ac1"]
            )
        repeatability[endpoint] = {
            **stats,
            "gwet_ac1_crossed_model_prompt_ci": interval(crossed["gwet_ac1"]),
            "any_flip_crossed_model_prompt_ci": interval(crossed["any_flip_rate"]),
            "gwet_ac1_prompt_cluster_fixed_roster_ci": interval(
                prompt_fixed_roster["gwet_ac1"]
            ),
            "any_flip_prompt_cluster_fixed_roster_ci": interval(
                prompt_fixed_roster["any_flip_rate"]
            ),
            "pairwise_run_agreement": pairwise,
            "cochran_q_descriptive_sensitivity": cochran_q(triples),
        }
        complete_repeatability[endpoint] = agreement_stats(
            endpoint_triples(cells, endpoint, complete_only=True)
        )
        comparisons = mcnemar_tests(triples)
        for row in comparisons:
            pair_key = row["run_pair"].replace("-", "_")
            delta_samples = crossed[f"pair_{pair_key}_delta"]
            row["rate_delta_crossed_model_prompt_ci_pp"] = {
                key: 100 * value for key, value in interval(delta_samples).items()
            }
            row["loss_rate"] = row["losses"] / len(triples)
            row["gain_rate"] = row["gains"] / len(triples)
            row["interpretation"] = (
                "descriptive exact paired-cell sensitivity; the crossed fixed-effects "
                "run-rate model is primary"
            )
        paired_effects[endpoint] = comparisons

    for run_row in run_rows:
        run_number = int(run_row["run"])
        run_row["execution_crossed_ci"] = interval(
            crossed_bootstraps["execution"][f"run_rate_{run_number}"]
        )
        run_row["signature_crossed_ci"] = interval(
            crossed_bootstraps["signature"][f"run_rate_{run_number}"]
        )
        run_row["es_gap_crossed_ci"] = interval(
            crossed_bootstraps["runnable_wrong"][f"run_rate_{run_number}"]
        )

    cell_path = output_dir / "pqid_bench_stochastic_repeatability_cell_outcomes.csv"
    model_path = output_dir / "pqid_bench_stochastic_repeatability_model_summary.csv"
    model_mcnemar_path = output_dir / "pqid_bench_stochastic_repeatability_per_model_mcnemar.csv"
    write_csv(cell_path, cells)
    write_csv(model_path, model_rows)
    write_csv(model_mcnemar_path, per_model_mcnemar(cells))

    manifest = provenance_manifest(root, output_dir)
    manifest_path = output_dir / "pqid_bench_stochastic_repeatability_file_manifest.json"
    write_json(manifest_path, manifest)

    analysis_path = output_dir / "pqid_bench_stochastic_repeatability_analysis.json"
    report_path = output_dir / "PQID_BENCH_STOCHASTIC_REPEATABILITY_REPORT.md"
    analysis = {
        "schema_version": SCHEMA_VERSION,
        "design": {
            "models": len(PRIMARY_MODEL_ORDER),
            "prompts": prompt_count,
            "runs": 3,
            "cells_per_run": len(PRIMARY_MODEL_ORDER) * prompt_count,
            "new_api_calls": len(PRIMARY_MODEL_ORDER) * prompt_count * 2,
            "incremental_augmentation_api_calls": INCREMENTAL_API_CALLS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "panel_sha256": EXPECTED_PANEL_SHA256,
            "outcome_blind_selection": bool(
                metadata["panel_manifest"].get("selection_is_outcome_blind", True)
            ),
            "analysis_protocol": protocol_freeze["protocol_path"],
            "analysis_protocol_sha256": protocol_freeze["protocol_sha256"],
            "protocol_amendments": protocol_freeze["amendments_path"],
            "protocol_amendments_sha256": protocol_freeze["amendments_sha256"],
            "analysis_protocol_frozen_at": ANALYSIS_PROTOCOL_FROZEN_AT,
            "analysis_protocol_amended_at": ANALYSIS_PROTOCOL_AMENDED_AT,
        },
        "evaluator_versions": metadata["evaluator_versions"],
        "structural_predicate_versions": metadata["predicate_versions"],
        "request_identity_audit": {
            "verified": metadata["request_identity_verified"],
            "model_prompt_requests": metadata["verified_model_prompt_requests"],
            "criterion": "the stored request_sha256 is identical across Runs 1, 2, and 3",
        },
        "target_identity_audit": {
            "verified": metadata["target_identity_verified"],
            "scored_cells": metadata["verified_scored_cells"],
            "panel_sha256": EXPECTED_PANEL_SHA256,
            "criterion": "every report target_metadata object equals the hash-verified frozen panel reference signature",
        },
        "canonical_completeness": metadata["canonical_completeness"],
        "sequential_replication": sequential_replication_summary(
            cells, metadata["panel_manifest"]
        ),
        "run_summaries": run_rows,
        "gate_bin_standardized_run_summaries": gate_bin_standardized_run_summaries(cells),
        "endpoint_repeatability": repeatability,
        "recorded_transport_unaffected_run_summaries": transport_unaffected_run_rows,
        "recorded_transport_unaffected_repeatability": complete_repeatability,
        "run_effect_models": {
            endpoint: two_way_fixed_effect_run_model(
                cells, endpoint, crossed_bootstraps[endpoint]
            )
            for endpoint in PRIMARY_ENDPOINTS
        },
        "paired_run_effects": paired_effects,
        "rank_stability": rank_stability(model_rows),
        "majority_vote_sensitivity": majority_summary(cells),
        "model_summaries": model_rows,
        "stratum_repeatability": stratum_agreement(cells),
        "difficulty_stratum_run_rates": difficulty_stratum_run_rates(cells),
        "three_run_stability_patterns": stability_patterns(cells),
        "exact_code_agreement": exact_code_agreement(cells),
        "provider_attempt_summary": provider_attempt_summary(cells),
        "retry_policy": {
            "canonical_trial": "first valid model response obtained within the prespecified route-specific attempt envelope",
            "direct_routes": {
                "maximum_transport_attempts": 3,
                "local_backoff_seconds": [1, 2],
                "sdk_hidden_retries": "disabled for the OpenAI-compatible runner",
                "retry_eligible": "transport, timeout, HTTP, or provider service exception before a valid response",
            },
            "openai_batch_route": {
                "submitted_items_per_model_prompt_run": 1,
                "local_response_level_retry": False,
                "lifecycle": "provider-managed batch validation, processing, and item error reporting",
            },
            "never_retry_for": [
                "valid model refusal",
                "empty valid completion",
                "truncation finish reason",
                "Python execution failure",
                "QASM3 failure",
                "reference-signature failure",
            ],
            "successful_generation_selection": "the first valid response only; no best-of-n selection",
            "out_of_band_error_recovery": "not enabled in the frozen master launcher",
        },
        "finish_reason_counts": {
            str(run): dict(
                Counter(
                    str(row["finish_reason"] or "<missing>").lower()
                    for row in cells
                    if int(row["run"]) == run
                )
            )
            for run in (1, 2, 3)
        },
        "artifact_paths": {
            "cell_outcomes": display_path(cell_path),
            "model_summary": display_path(model_path),
            "per_model_mcnemar": display_path(model_mcnemar_path),
            "file_manifest": display_path(manifest_path),
            "figure_svg": display_path(output_dir / "pqid_bench_stochastic_repeatability_panel.svg"),
            "figure_png": display_path(output_dir / "pqid_bench_stochastic_repeatability_panel.png"),
            "report": display_path(report_path),
        },
    }
    write_json(analysis_path, analysis)
    write_markdown(report_path, analysis)
    plot_figure(output_dir, run_rows, model_rows)
    print(f"Wrote {display_path(analysis_path)}")
    print(f"Wrote {display_path(report_path)}")
    print(f"Wrote {display_path(output_dir / 'pqid_bench_stochastic_repeatability_panel.svg')}")


def main() -> None:
    global ANALYSIS_PROTOCOL_AMENDED_AT
    global ANALYSIS_PROTOCOL_FROZEN_AT
    global EXPECTED_AMENDMENTS_SHA256
    global EXPECTED_PANEL_SHA256
    global EXPECTED_PROTOCOL_SHA256
    global INCREMENTAL_API_CALLS
    global SCHEMA_VERSION

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--expected-panel-sha256", default=EXPECTED_PANEL_SHA256)
    parser.add_argument("--expected-protocol-sha256", default=EXPECTED_PROTOCOL_SHA256)
    parser.add_argument("--expected-amendments-sha256", default=EXPECTED_AMENDMENTS_SHA256)
    parser.add_argument("--schema-version", default=SCHEMA_VERSION)
    parser.add_argument(
        "--protocol-frozen-at", default=ANALYSIS_PROTOCOL_FROZEN_AT
    )
    parser.add_argument(
        "--protocol-amended-at", default=ANALYSIS_PROTOCOL_AMENDED_AT
    )
    parser.add_argument("--incremental-api-calls", type=int, default=None)
    args = parser.parse_args()
    EXPECTED_PANEL_SHA256 = str(args.expected_panel_sha256).lower()
    EXPECTED_PROTOCOL_SHA256 = str(args.expected_protocol_sha256).lower()
    EXPECTED_AMENDMENTS_SHA256 = str(args.expected_amendments_sha256).lower()
    SCHEMA_VERSION = str(args.schema_version)
    ANALYSIS_PROTOCOL_FROZEN_AT = str(args.protocol_frozen_at)
    ANALYSIS_PROTOCOL_AMENDED_AT = str(args.protocol_amended_at)
    INCREMENTAL_API_CALLS = args.incremental_api_calls
    output_dir = args.output_dir or args.root / "analysis"
    analyze(args.root, output_dir)


if __name__ == "__main__":
    main()
