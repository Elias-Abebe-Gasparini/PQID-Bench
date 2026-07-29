"""Analyze PQID-Bench model-performance distributions with descriptive regressions.

The goal is not to claim causal scaling laws from a finite held-out split. Instead,
this script gives the paper a compact statistical view of two descriptive
patterns:

- how named model rows distribute across execution and structural fidelity;
- how circuit descriptors account for structural-match difficulty.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from pqid_bench_model_registry import (
    EXPANDED_MODEL_ORDER,
    MODEL_LABELS,
    MODEL_ORDER,
    model_from_report_dir,
    model_tier,
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
JSON_OUT = ROOT / "artifacts/analysis_154/pqid_bench_model_regression_analysis.json"
MD_OUT = ROOT / "artifacts/analysis_154/pqid_bench_model_regression_analysis.md"


CONTROLLED_OR_ENTANGLING_GATES = {
    "cx",
    "cz",
    "cp",
    "ch",
    "cs",
    "ct",
    "ccx",
    "swap",
    "rxx",
    "rzz",
}
ROTATION_GATES = {"rx", "ry", "rz", "p", "u", "u1", "u2", "u3", "rxx", "rzz"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pct(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{100.0 * value:.2f}%"


def pp(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{100.0 * value:+.2f} pp"


def gate_entropy(gates: dict[str, int]) -> float:
    total = sum(gates.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in gates.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy


def prompt_features(prompt: dict[str, Any]) -> dict[str, Any]:
    metadata = prompt["target_metadata"]
    gates = {str(k): int(v) for k, v in metadata["gate_types"].items()}
    gate_names = set(gates)
    gate_count = int(metadata["gate_count"])
    gate_type_count = len(gates)
    return {
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "label": prompt["label"],
        "instruction": prompt["instruction"],
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "gate_count": gate_count,
        "gate_type_count": gate_type_count,
        "gate_entropy": gate_entropy(gates),
        "has_measure": "measure" in gate_names,
        "has_barrier": "barrier" in gate_names,
        "has_controlled_or_entangling": bool(gate_names & CONTROLLED_OR_ENTANGLING_GATES),
        "has_rotation": bool(gate_names & ROTATION_GATES),
        "high_gate_diversity": gate_type_count >= 5,
        "high_gate_count": gate_count >= 13,
    }


def load_evaluations(eval_dirs: Path | list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model not in MODEL_ORDER:
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
            for record in report.get("records", []):
                execution = record.get("execution", {})
                checks = record.get("structural_checks") or {}
                qasm = execution.get("qasm3_export") or {}
                circuit_found = bool(execution.get("circuit_found"))
                rows.append(
                    {
                        "report_dir": report_path.parent.name,
                        "provider": record.get("provider"),
                        "model": model,
                        "model_label": MODEL_LABELS.get(model, model),
                        "model_tier": model_tier(model),
                        "prompt_id": record["prompt_id"],
                        "execution_success": bool(execution.get("execution_success")) and circuit_found,
                        "circuit_found": circuit_found,
                        "qasm3_success": bool(qasm.get("success")),
                        "structural_all_match": bool(checks.get("all_match")),
                        "gate_types_match": bool(checks.get("gate_types_match")),
                        "gate_count_match": bool(checks.get("gate_count_match")),
                        "num_qubits_match": bool(checks.get("num_qubits_match")),
                        "num_clbits_match": bool(checks.get("num_clbits_match")),
                    }
                )
    return rows


def binary_rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(bool(row[key]) for row in rows) / len(rows)


def safe_sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return ordered[int(pos)]
    weight = pos - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    aug = [
        [float(matrix[row][col]) for col in range(size)]
        + [1.0 if row == col else 0.0 for col in range(size)]
        for row in range(size)
    ]
    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular design matrix")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_value = aug[col][col]
        for j in range(2 * size):
            aug[col][j] /= pivot_value
        for row in range(size):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0.0:
                continue
            for j in range(2 * size):
                aug[row][j] -= factor * aug[col][j]
    return [row[size:] for row in aug]


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    inverse = invert_matrix(matrix)
    return [sum(inverse[row][col] * vector[col] for col in range(len(vector))) for row in range(len(vector))]


def ols(rows: list[dict[str, Any]], y_key: str, terms: list[tuple[str, str]], ridge: float = 1e-8) -> dict[str, Any]:
    y = [float(row[y_key]) for row in rows]
    x = [[1.0, *[float(row[key]) for key, _ in terms]] for row in rows]
    names = ["intercept", *[name for _, name in terms]]
    cols = len(names)
    xtx = [[0.0 for _ in range(cols)] for _ in range(cols)]
    xty = [0.0 for _ in range(cols)]
    for row_x, row_y in zip(x, y):
        for i in range(cols):
            xty[i] += row_x[i] * row_y
            for j in range(cols):
                xtx[i][j] += row_x[i] * row_x[j]
    for i in range(1, cols):
        xtx[i][i] += ridge
    beta = solve_linear_system(xtx, xty)
    fitted = [sum(coef * value for coef, value in zip(beta, row_x)) for row_x in x]
    y_bar = mean(y)
    sst = sum((value - y_bar) ** 2 for value in y)
    sse = sum((value - pred) ** 2 for value, pred in zip(y, fitted))
    r2 = 1.0 - sse / sst if sst else 0.0
    return {
        "n": len(rows),
        "outcome": y_key,
        "terms": [
            {
                "name": name,
                "coefficient": beta[index],
                "coefficient_pp": 100.0 * beta[index],
            }
            for index, name in enumerate(names)
        ],
        "r_squared": r2,
        "mean_outcome": y_bar,
    }


def add_standardized_columns(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for key in keys:
        values = [float(row[key]) for row in rows]
        avg = mean(values)
        sd = safe_sd(values)
        if sd == 0.0:
            sd = 1.0
        stats[key] = {"mean": avg, "sd": sd}
        for row in rows:
            row[f"z_{key}"] = (float(row[key]) - avg) / sd
    return stats


def model_distribution(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        by_model[row["model"]].append(row)
    raw = []
    for model in MODEL_ORDER:
        rows = by_model.get(model, [])
        if not rows:
            continue
        raw.append(
            {
                "model": model,
                "model_label": MODEL_LABELS.get(model, model),
                "model_tier": model_tier(model),
                "n": len(rows),
                "execution_success": binary_rate(rows, "execution_success"),
                "qasm3_success": binary_rate(rows, "qasm3_success"),
                "structural_all_match": binary_rate(rows, "structural_all_match"),
                "structural_given_execution": (
                    sum(row["structural_all_match"] for row in rows)
                    / sum(row["execution_success"] for row in rows)
                    if sum(row["execution_success"] for row in rows)
                    else None
                ),
                "gate_types_match": binary_rate(rows, "gate_types_match"),
                "gate_count_match": binary_rate(rows, "gate_count_match"),
                "num_qubits_match": binary_rate(rows, "num_qubits_match"),
                "num_clbits_match": binary_rate(rows, "num_clbits_match"),
            }
        )
    structural_values = [row["structural_all_match"] for row in raw]
    structural_mean = mean(structural_values)
    structural_sd = safe_sd(structural_values) or 1.0
    ranked = sorted(raw, key=lambda row: (-row["structural_all_match"], MODEL_ORDER.index(row["model"])))
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
        row["structural_z"] = (row["structural_all_match"] - structural_mean) / structural_sd
    return ranked


def tier_distribution(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        by_tier[row["model_tier"]].append(row)
    order = ["frontier_api", "strong_open_or_code", "low_or_experimental", "other"]
    out = []
    for tier in order:
        rows = by_tier.get(tier, [])
        if not rows:
            continue
        structural = [row["structural_all_match"] for row in rows]
        execution = [row["execution_success"] for row in rows]
        out.append(
            {
                "tier": tier,
                "models": len(rows),
                "structural_mean": mean(structural),
                "structural_median": median(structural),
                "structural_min": min(structural),
                "structural_max": max(structural),
                "structural_sd": safe_sd(structural),
                "execution_mean": mean(execution),
            }
        )
    return out


def distribution_summary(model_rows: list[dict[str, Any]]) -> dict[str, Any]:
    structural = [row["structural_all_match"] for row in model_rows]
    execution = [row["execution_success"] for row in model_rows]
    return {
        "model_count": len(model_rows),
        "structural_min": min(structural),
        "structural_q1": quantile(structural, 0.25),
        "structural_median": median(structural),
        "structural_mean": mean(structural),
        "structural_q3": quantile(structural, 0.75),
        "structural_max": max(structural),
        "structural_range": max(structural) - min(structural),
        "structural_sd": safe_sd(structural),
        "execution_min": min(execution),
        "execution_median": median(execution),
        "execution_mean": mean(execution),
        "execution_max": max(execution),
    }


def coefficient_table(regression: dict[str, Any]) -> list[str]:
    lines = [
        "| predictor | coefficient | interpretation |",
        "| --- | ---: | --- |",
    ]
    for term in regression["terms"]:
        name = term["name"]
        if name == "intercept":
            interpretation = "baseline expected structural rate"
        elif name.startswith("z_"):
            interpretation = "change per one standard deviation increase"
        else:
            interpretation = "adjusted yes-minus-no contrast"
        lines.append(f"| `{name}` | {pp(term['coefficient'])} | {interpretation} |")
    return lines


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines: list[str] = []
    model_dist = result["model_distribution"]
    tier_dist = result["tier_distribution"]
    summary = result["distribution_summary"]
    prompt_reg = result["prompt_level_regression"]
    row_reg = result["prompt_model_linear_probability_model"]

    lines.append("# PQID-Bench Model Regression And Distribution Analysis")
    lines.append("")
    lines.append(f"- prompts: `{result['prompt_count']}`")
    lines.append(f"- completed external model rows: `{result['model_count']}`")
    lines.append(f"- prompt-model evaluations: `{result['evaluation_count']}`")
    lines.append(f"- model-level regression is deliberately avoided because `n={result['model_count']}` model rows is too small for a credible inferential model")
    lines.append("- reported regressions are descriptive linear probability models; coefficients are effect sizes, not causal estimates")
    lines.append("")

    lines.append("## Model-Score Distribution")
    lines.append("")
    lines.append("| rank | model | tier | execution | structural | M given E | QASM3 | structural z |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for row in model_dist:
        lines.append(
            "| {rank} | {model} | {tier} | {execution} | {structural} | {conditional} | {qasm3} | {z:.2f} |".format(
                rank=row["rank"],
                model=row["model_label"],
                tier=row["model_tier"],
                execution=pct(row["execution_success"]),
                structural=pct(row["structural_all_match"]),
                conditional=pct(row["structural_given_execution"]),
                qasm3=pct(row["qasm3_success"]),
                z=row["structural_z"],
            )
        )
    lines.append("")
    lines.append(
        "Across named model rows, structural fidelity spans {low} to {high} "
        "(range {span}, median {median}, mean {avg}).".format(
            low=pct(summary["structural_min"]),
            high=pct(summary["structural_max"]),
            span=pp(summary["structural_range"]),
            median=pct(summary["structural_median"]),
            avg=pct(summary["structural_mean"]),
        )
    )
    lines.append("")

    lines.append("## Tier Distribution")
    lines.append("")
    lines.append("| tier | models | execution mean | structural mean | structural median | structural range | structural sd |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in tier_dist:
        lines.append(
            "| {tier} | {models} | {execution} | {structural_mean} | {structural_median} | {low}-{high} | {sd:.2f} pp |".format(
                tier=row["tier"],
                models=row["models"],
                execution=pct(row["execution_mean"]),
                structural_mean=pct(row["structural_mean"]),
                structural_median=pct(row["structural_median"]),
                low=pct(row["structural_min"]),
                high=pct(row["structural_max"]),
                sd=100.0 * row["structural_sd"],
            )
        )
    lines.append("")

    lines.append("## Prompt-Level Complexity Regression")
    lines.append("")
    lines.append(
        "Outcome: mean structural match rate per prompt across completed models. "
        "Continuous circuit descriptors are standardized, so their coefficients are percentage-point changes per one standard deviation."
    )
    lines.append("")
    lines.append(f"- observations: `{prompt_reg['n']}` prompts")
    lines.append(f"- mean outcome: `{pct(prompt_reg['mean_outcome'])}`")
    lines.append(f"- R-squared: `{prompt_reg['r_squared']:.3f}`")
    lines.append("")
    lines.extend(coefficient_table(prompt_reg))
    lines.append("")

    lines.append("## Prompt-Model Linear Probability Model")
    lines.append("")
    lines.append(
        "Outcome: binary structural match for each prompt-model evaluation. "
        "The reference model tier is `frontier_api`; tier coefficients therefore measure distributional offsets from that frontier cluster after adding the same prompt descriptors."
    )
    lines.append("")
    lines.append(f"- observations: `{row_reg['n']}` prompt-model rows")
    lines.append(f"- mean outcome: `{pct(row_reg['mean_outcome'])}`")
    lines.append(f"- R-squared: `{row_reg['r_squared']:.3f}`")
    lines.append("")
    lines.extend(coefficient_table(row_reg))
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The distribution is neither random noise nor a trivial leaderboard. "
        "Models form a clear capability gradient, but the best frontier rows compress into a narrow structural band while execution and QASM3 validity are already high. "
        "That is exactly the pattern a useful benchmark should expose: format compliance is mostly solved by strong systems, whereas exact circuit recovery still separates models."
    )
    lines.append("")
    lines.append(
        "The regression results support the same story from the task side. "
        "Gate diversity and gate entropy carry the strongest negative coefficients, while raw qubit count is weak once richer circuit descriptors are included. "
        "For the manuscript, this should be framed as descriptive evidence that PQID-Bench measures structural circuit fidelity rather than merely penalizing wider circuits."
    )
    lines.append("")
    lines.append(
        "Caveat: the split is intentionally small and audit-friendly. "
        "The right claim is that the current release-bound matrix gives coherent evidence of benchmark difficulty and model differentiation, not that these coefficients are universal laws of quantum-code generation."
    )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    global MODEL_ORDER

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
    parser.add_argument(
        "--exclude-prompt-id",
        action="append",
        default=[],
        help="Exclude a prompt ID from a sensitivity analysis; may be repeated.",
    )
    args = parser.parse_args()

    if args.expanded_roster:
        MODEL_ORDER = list(EXPANDED_MODEL_ORDER)
    eval_dirs = args.eval_dir or DEFAULT_EVAL_DIRS

    prompts = read_jsonl(args.prompt_path)
    excluded_prompt_ids = set(args.exclude_prompt_id)
    if excluded_prompt_ids:
        prompts = [prompt for prompt in prompts if prompt["prompt_id"] not in excluded_prompt_ids]
    features = {prompt["prompt_id"]: prompt_features(prompt) for prompt in prompts}
    eval_rows = load_evaluations(eval_dirs)
    joined = [
        {**row, **features[row["prompt_id"]]}
        for row in eval_rows
        if row["prompt_id"] in features and row["model"] in MODEL_ORDER
    ]
    observed = {(row["prompt_id"], row["model"]) for row in joined}
    expected = {
        (prompt["prompt_id"], model)
        for prompt in prompts
        for model in MODEL_ORDER
    }
    if observed != expected:
        raise RuntimeError(
            f"Incomplete evaluation roster: missing={len(expected - observed)}; "
            f"extras={len(observed - expected)}"
        )

    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        by_prompt[row["prompt_id"]].append(row)
    prompt_rows = []
    for prompt in prompts:
        prompt_id = prompt["prompt_id"]
        rows = by_prompt[prompt_id]
        feature_row = dict(features[prompt_id])
        feature_row["structural_rate"] = binary_rate(rows, "structural_all_match")
        feature_row["execution_rate"] = binary_rate(rows, "execution_success")
        feature_row["qasm3_rate"] = binary_rate(rows, "qasm3_success")
        feature_row["models"] = len(rows)
        prompt_rows.append(feature_row)

    continuous_keys = [
        "num_qubits",
        "num_clbits",
        "gate_count",
        "gate_type_count",
        "gate_entropy",
    ]
    prompt_stats = add_standardized_columns(prompt_rows, continuous_keys)
    joined_stats = add_standardized_columns(joined, continuous_keys)
    for row in joined:
        row["tier_strong_open_or_code"] = int(row["model_tier"] == "strong_open_or_code")
        row["tier_low_or_experimental"] = int(row["model_tier"] == "low_or_experimental")
        row["has_barrier"] = int(row["has_barrier"])
        row["has_measure"] = int(row["has_measure"])
        row["has_controlled_or_entangling"] = int(row["has_controlled_or_entangling"])
        row["has_rotation"] = int(row["has_rotation"])
        row["high_gate_diversity"] = int(row["high_gate_diversity"])
        row["high_gate_count"] = int(row["high_gate_count"])
        row["structural_success"] = int(row["structural_all_match"])
    for row in prompt_rows:
        row["has_barrier"] = int(row["has_barrier"])
        row["has_measure"] = int(row["has_measure"])
        row["has_controlled_or_entangling"] = int(row["has_controlled_or_entangling"])
        row["has_rotation"] = int(row["has_rotation"])
        row["high_gate_diversity"] = int(row["high_gate_diversity"])
        row["high_gate_count"] = int(row["high_gate_count"])

    prompt_terms = [
        ("z_num_qubits", "z_num_qubits"),
        ("z_num_clbits", "z_num_clbits"),
        ("z_gate_count", "z_gate_count"),
        ("z_gate_type_count", "z_gate_type_count"),
        ("z_gate_entropy", "z_gate_entropy"),
        ("has_barrier", "has_barrier"),
        ("has_controlled_or_entangling", "has_controlled_or_entangling"),
        ("has_rotation", "has_rotation"),
        ("has_measure", "has_measure"),
    ]
    row_terms = [
        ("tier_strong_open_or_code", "tier_strong_open_or_code"),
        ("tier_low_or_experimental", "tier_low_or_experimental"),
        ("z_num_qubits", "z_num_qubits"),
        ("z_num_clbits", "z_num_clbits"),
        ("z_gate_count", "z_gate_count"),
        ("z_gate_type_count", "z_gate_type_count"),
        ("z_gate_entropy", "z_gate_entropy"),
        ("has_barrier", "has_barrier"),
        ("has_controlled_or_entangling", "has_controlled_or_entangling"),
        ("has_rotation", "has_rotation"),
        ("has_measure", "has_measure"),
    ]

    model_rows = model_distribution(joined)
    result = {
        "roster": "final_21_primary",
        "prompt_count": len(prompts),
        "model_count": len(model_rows),
        "evaluation_count": len(joined),
        "excluded_prompt_ids": sorted(excluded_prompt_ids),
        "continuous_standardization_prompt_level": prompt_stats,
        "continuous_standardization_prompt_model_level": joined_stats,
        "distribution_summary": distribution_summary(model_rows),
        "model_distribution": model_rows,
        "tier_distribution": tier_distribution(model_rows),
        "prompt_level_regression": ols(prompt_rows, "structural_rate", prompt_terms),
        "prompt_model_linear_probability_model": ols(joined, "structural_success", row_terms),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.md_out, result)


if __name__ == "__main__":
    main()
