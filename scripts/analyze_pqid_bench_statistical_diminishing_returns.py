"""Statistical summaries for PQID-Bench diminishing-return claims.

The analysis is intentionally dependency-free and conservative. It treats the
154 held-out prompts as the main units for complexity relationships, because
the 21 model outputs per prompt are repeated measurements of the same target.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from pqid_bench_model_registry import model_from_report_dir


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
SUMMARY_PATH = ROOT / "artifacts/external_model_batches_154/pqid_bench_external_model_results_summary.json"
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
JSON_OUT = ROOT / "artifacts/analysis_154/pqid_bench_statistical_diminishing_returns.json"
MD_OUT = ROOT / "artifacts/analysis_154/pqid_bench_statistical_diminishing_returns.md"

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


MODEL_TIERS = [
    {
        "tier": "retrieval-copy lower bound",
        "kind": "baseline",
        "models": ["word_tfidf_train_instruction_copy"],
    },
    {
        "tier": "low / experimental hosted",
        "kind": "external",
        "models": [
            "qwen/qwen3-32b",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ],
    },
    {
        "tier": "strong hosted open/code",
        "kind": "external",
        "models": [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "mistral-ai/codestral-2501",
            "qwen/qwen3-coder-next",
            "meta/llama-4-maverick-17b-128e-instruct-fp8",
            "mistralai/mistral-small-3.2-24b-instruct",
            "qiskit/mistral-small-3.2-24b-qiskit",
        ],
    },
    {
        "tier": "frontier APIs",
        "kind": "external",
        "models": [
            "gpt-5.6-sol",
            "gpt-5.5",
            "gpt-5.4-mini",
            "claude-fable-5",
            "claude-sonnet-4-6",
            "claude-opus-4-8",
            "gemini-2.5-pro",
            "gemini-3.1-pro-preview",
            "deepseek-v4-pro",
            "deepseek-v4-flash",
        ],
    },
]

EXTERNAL_MODEL_ORDER = [
    model
    for tier in MODEL_TIERS
    if tier["kind"] == "external"
    for model in tier["models"]
]

UPGRADE_PAIRS = [
    ("llama-3.1-8b-instant", "llama-3.3-70b-versatile", "Llama 8B -> 70B"),
    (
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "Llama 4 Scout -> Maverick",
    ),
    ("openai/gpt-oss-20b", "openai/gpt-oss-120b", "GPT-OSS 20B -> 120B"),
    ("gemini-2.5-pro", "gemini-3.1-pro-preview", "Gemini 2.5 Pro -> 3.1 Pro Preview"),
    ("claude-sonnet-4-6", "claude-opus-4-8", "Claude Sonnet 4.6 -> Opus 4.8"),
    ("deepseek-v4-flash", "deepseek-v4-pro", "DeepSeek V4 Flash -> Pro"),
    (
        "mistralai/mistral-small-3.2-24b-instruct",
        "qiskit/mistral-small-3.2-24b-qiskit",
        "Mistral parent -> Qiskit specialist",
    ),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f}"


def gate_entropy(gate_types: dict[str, int]) -> float:
    total = sum(gate_types.values())
    if total == 0:
        return 0.0
    result = 0.0
    for count in gate_types.values():
        p = count / total
        result -= p * math.log(p)
    return result


def prompt_features(prompt: dict[str, Any]) -> dict[str, Any]:
    metadata = prompt["target_metadata"]
    gates = {str(k): int(v) for k, v in metadata["gate_types"].items()}
    names = set(gates)
    gate_count = int(metadata["gate_count"])
    gate_type_count = len(gates)
    return {
        "prompt_id": prompt["prompt_id"],
        "label": prompt["label"],
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "gate_count": gate_count,
        "gate_type_count": gate_type_count,
        "gate_entropy": gate_entropy(gates),
        "has_measure": "measure" in names,
        "has_barrier": "barrier" in names,
        "has_controlled_or_entangling": bool(names & CONTROLLED_OR_ENTANGLING_GATES),
        "has_rotation": bool(names & ROTATION_GATES),
        "high_gate_count": gate_count >= 13,
        "high_gate_diversity": gate_type_count >= 5,
        "low_gate_diversity": gate_type_count <= 2,
    }


def load_evaluations(eval_dirs: Path | list[Path]) -> list[dict[str, Any]]:
    rows = []
    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            planned_model = planned_model_from_report_dir(report_path.parent.name)
            if planned_model not in EXTERNAL_MODEL_ORDER:
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
            for record in report.get("records", []):
                execution = record.get("execution", {})
                checks = record.get("structural_checks") or {}
                circuit_found = bool(execution.get("circuit_found"))
                rows.append(
                    {
                        "prompt_id": record["prompt_id"],
                        "provider": record.get("provider"),
                        "model": record.get("model"),
                        "planned_model": planned_model,
                        "execution_success": bool(execution.get("execution_success")) and circuit_found,
                        "structural_all_match": bool(checks.get("all_match")),
                        "gate_types_match": bool(checks.get("gate_types_match")),
                        "gate_count_match": bool(checks.get("gate_count_match")),
                        "num_qubits_match": bool(checks.get("num_qubits_match")),
                        "num_clbits_match": bool(checks.get("num_clbits_match")),
                        "qasm3_success": bool((execution.get("qasm3_export") or {}).get("success")),
                    }
                )
    return rows


def planned_model_from_report_dir(name: str) -> str:
    return model_from_report_dir(name)


def prompt_rate_rows(prompts: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = {row["prompt_id"]: prompt_features(row) for row in prompts}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        grouped[row["prompt_id"]].append(row)
    output = []
    for prompt_id, rows in sorted(grouped.items()):
        item = dict(features[prompt_id])
        item["models"] = len(rows)
        for key in [
            "execution_success",
            "structural_all_match",
            "gate_types_match",
            "gate_count_match",
            "num_qubits_match",
            "num_clbits_match",
            "qasm3_success",
        ]:
            item[f"{key}_rate"] = sum(row[key] for row in rows) / len(rows)
        output.append(item)
    return output


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    xbar = mean(xs)
    ybar = mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xden = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    yden = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    if xden == 0 or yden == 0:
        return None
    return numerator / (xden * yden)


def ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    out = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            out[indexed[k][0]] = rank
        i = j + 1
    return out


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(ranks(xs), ranks(ys))


def permutation_p_value(xs: list[float], ys: list[float], observed: float | None, trials: int, seed: int) -> float | None:
    if observed is None:
        return None
    rng = random.Random(seed)
    count = 0
    shuffled = list(ys)
    for _ in range(trials):
        rng.shuffle(shuffled)
        value = spearman(xs, shuffled)
        if value is not None and abs(value) >= abs(observed):
            count += 1
    return (count + 1) / (trials + 1)


def linear_slope(xs: list[float], ys: list[float]) -> float | None:
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def quantiles(values: list[float], probs: list[float]) -> list[float]:
    values = sorted(values)
    result = []
    for p in probs:
        if not values:
            result.append(float("nan"))
            continue
        idx = p * (len(values) - 1)
        low = math.floor(idx)
        high = math.ceil(idx)
        if low == high:
            result.append(values[low])
        else:
            frac = idx - low
            result.append(values[low] * (1 - frac) + values[high] * frac)
    return result


def bootstrap_mean_ci(values: list[float], trials: int, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    if not values:
        return (float("nan"), float("nan"))
    samples = []
    for _ in range(trials):
        samples.append(mean(rng.choice(values) for _ in values))
    low, high = quantiles(samples, [0.025, 0.975])
    return low, high


def bootstrap_difference_ci(a: list[float], b: list[float], trials: int, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    if not a or not b:
        return (float("nan"), float("nan"))
    samples = []
    for _ in range(trials):
        aval = mean(rng.choice(a) for _ in a)
        bval = mean(rng.choice(b) for _ in b)
        samples.append(aval - bval)
    low, high = quantiles(samples, [0.025, 0.975])
    return low, high


def metric_summary(values: list[float], trials: int, seed: int) -> dict[str, Any]:
    low, high = bootstrap_mean_ci(values, trials, seed)
    return {"n_prompts": len(values), "mean": mean(values), "median": median(values), "ci_low": low, "ci_high": high}


def contrast(prompt_rows: list[dict[str, Any]], feature: str, trials: int, seed: int) -> dict[str, Any]:
    yes = [row["structural_all_match_rate"] for row in prompt_rows if row[feature]]
    no = [row["structural_all_match_rate"] for row in prompt_rows if not row[feature]]
    low, high = bootstrap_difference_ci(yes, no, trials, seed)
    return {
        "feature": feature,
        "yes": metric_summary(yes, trials, seed + 1),
        "no": metric_summary(no, trials, seed + 2),
        "difference_yes_minus_no": mean(yes) - mean(no),
        "difference_ci_low": low,
        "difference_ci_high": high,
    }


def load_model_rows(summary_path: Path, eval_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        grouped[row["planned_model"]].append(row)
    rows: dict[str, dict[str, Any]] = {}
    for model, records in grouped.items():
        rows[model] = {
            "planned_model": model,
            "provider": records[0].get("provider"),
            "execution": mean(record["execution_success"] for record in records),
            "structural": mean(record["structural_all_match"] for record in records),
            "gate_types": mean(record["gate_types_match"] for record in records),
            "gate_count": mean(record["gate_count_match"] for record in records),
            "qubits": mean(record["num_qubits_match"] for record in records),
            "clbits": mean(record["num_clbits_match"] for record in records),
            "qasm3": mean(record["qasm3_success"] for record in records),
        }
    lower = summary["lower_bound"]
    rows["word_tfidf_train_instruction_copy"] = {
        "planned_model": "word_tfidf_train_instruction_copy",
        "provider": "retrieval-copy",
        "execution": lower["execution_success"],
        "structural": lower["structural_all_match"],
        "gate_types": lower["gate_types_match"],
        "gate_count": lower["gate_count_match"],
        "qubits": lower["num_qubits_match"],
        "clbits": None,
        "qasm3": lower["qasm3_export_success"],
    }
    return rows


def average_model_metrics(models: list[str], model_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    available = [model_rows[model] for model in models if model in model_rows]
    out: dict[str, Any] = {"models": [row["planned_model"] for row in available], "n_models": len(available)}
    for metric in ["execution", "structural", "gate_types", "gate_count", "qubits", "clbits", "qasm3"]:
        values = [row[metric] for row in available if row[metric] is not None]
        out[metric] = mean(values) if values else None
    if out["execution"] is not None and out["structural"] is not None:
        out["execution_structure_gap"] = out["execution"] - out["structural"]
    return out


def model_tier_table(model_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    previous: dict[str, Any] | None = None
    for tier in MODEL_TIERS:
        item = average_model_metrics(tier["models"], model_rows)
        item["tier"] = tier["tier"]
        item["kind"] = tier["kind"]
        if previous is None:
            item["delta_execution"] = None
            item["delta_structural"] = None
        else:
            item["delta_execution"] = item["execution"] - previous["execution"]
            item["delta_structural"] = item["structural"] - previous["structural"]
        previous = item
        rows.append(item)
    return rows


def upgrade_table(model_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for before, after, label in UPGRADE_PAIRS:
        if before not in model_rows or after not in model_rows:
            continue
        b = model_rows[before]
        a = model_rows[after]
        rows.append(
            {
                "comparison": label,
                "before": before,
                "after": after,
                "execution_before": b["execution"],
                "execution_after": a["execution"],
                "structural_before": b["structural"],
                "structural_after": a["structural"],
                "delta_execution": a["execution"] - b["execution"],
                "delta_structural": a["structural"] - b["structural"],
                "delta_gate_types": a["gate_types"] - b["gate_types"],
                "delta_gate_count": a["gate_count"] - b["gate_count"],
                "delta_qasm3": a["qasm3"] - b["qasm3"],
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument(
        "--eval-dir",
        type=Path,
        action="append",
        default=None,
        help="Evaluation directory; may be repeated for additional completed model rows.",
    )
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--bootstrap-trials", type=int, default=5000)
    parser.add_argument("--permutation-trials", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260618)
    args = parser.parse_args()

    prompts = read_jsonl(args.prompt_path)
    eval_dirs = args.eval_dir or DEFAULT_EVAL_DIRS
    eval_rows = load_evaluations(eval_dirs)
    prompt_rows = prompt_rate_rows(prompts, eval_rows)
    model_rows = load_model_rows(args.summary_path, eval_rows)

    y = [row["structural_all_match_rate"] for row in prompt_rows]
    correlations = []
    for index, metric in enumerate(["num_qubits", "num_clbits", "gate_count", "gate_type_count", "gate_entropy"]):
        xs = [float(row[metric]) for row in prompt_rows]
        pearson_r = pearson(xs, y)
        spearman_r = spearman(xs, y)
        p_value = permutation_p_value(xs, y, spearman_r, args.permutation_trials, args.seed + index)
        slope = linear_slope(xs, y)
        correlations.append(
            {
                "descriptor": metric,
                "pearson_r": pearson_r,
                "spearman_r": spearman_r,
                "spearman_permutation_p": p_value,
                "linear_slope_per_unit": slope,
            }
        )

    contrasts = [
        contrast(prompt_rows, "high_gate_diversity", args.bootstrap_trials, args.seed + 10),
        contrast(prompt_rows, "high_gate_count", args.bootstrap_trials, args.seed + 20),
        contrast(prompt_rows, "has_barrier", args.bootstrap_trials, args.seed + 30),
        contrast(prompt_rows, "has_controlled_or_entangling", args.bootstrap_trials, args.seed + 40),
        contrast(prompt_rows, "has_rotation", args.bootstrap_trials, args.seed + 50),
        contrast(prompt_rows, "has_measure", args.bootstrap_trials, args.seed + 60),
    ]

    tier_rows = model_tier_table(model_rows)
    upgrades = upgrade_table(model_rows)

    result = {
        "prompt_count": len(prompt_rows),
        "model_count": len({row["planned_model"] for row in eval_rows}),
        "evaluation_count": len(eval_rows),
        "correlations": correlations,
        "prompt_level_contrasts": contrasts,
        "model_tiers": tier_rows,
        "upgrade_pairs": upgrades,
        "notes": [
            "Complexity correlations use one row per prompt, with structural rate averaged over completed models.",
            "Bootstrap intervals resample prompts within each group.",
            "Permutation p-values are two-sided and descriptive; they are not a substitute for a preregistered inferential design.",
        ],
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    lines: list[str] = []
    lines.append("# PQID-Bench Statistical Diminishing-Returns Analysis")
    lines.append("")
    lines.append(f"- prompts: `{result['prompt_count']}`")
    lines.append(f"- completed external models: `{result['model_count']}`")
    lines.append(f"- prompt-model evaluations: `{result['evaluation_count']}`")
    lines.append("- unit for complexity correlations: prompt-level mean structural rate across completed models")
    lines.append("- confidence intervals: prompt-cluster bootstrap, 5,000 resamples")
    lines.append("")
    lines.append("## Complexity Correlations")
    lines.append("")
    lines.append("| descriptor | Pearson r | Spearman rho | permutation p | slope per unit |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for row in correlations:
        lines.append(
            "| `{descriptor}` | {pearson} | {spearman} | {pval} | {slope} pp |".format(
                descriptor=row["descriptor"],
                pearson="n/a" if row["pearson_r"] is None else f"{row['pearson_r']:.3f}",
                spearman="n/a" if row["spearman_r"] is None else f"{row['spearman_r']:.3f}",
                pval="n/a" if row["spearman_permutation_p"] is None else f"{row['spearman_permutation_p']:.4f}",
                slope="n/a" if row["linear_slope_per_unit"] is None else f"{100.0 * row['linear_slope_per_unit']:.2f}",
            )
        )
    lines.append("")
    lines.append("## Prompt-Level Structural Contrasts")
    lines.append("")
    lines.append("| contrast | no mean | yes mean | yes - no | 95% CI |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for row in contrasts:
        lines.append(
            "| `{feature}` | {no_mean} | {yes_mean} | {diff} pp | [{low}, {high}] pp |".format(
                feature=row["feature"],
                no_mean=pct(row["no"]["mean"]),
                yes_mean=pct(row["yes"]["mean"]),
                diff=pp(row["difference_yes_minus_no"]),
                low=f"{100.0 * row['difference_ci_low']:.2f}",
                high=f"{100.0 * row['difference_ci_high']:.2f}",
            )
        )
    lines.append("")
    lines.append("## Model-Side Returns By Descriptive Tier")
    lines.append("")
    lines.append("| tier | models | execution | structural | exec-structure gap | delta execution | delta structural |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in tier_rows:
        lines.append(
            "| {tier} | {n} | {execution} | {structural} | {gap} | {de} | {ds} |".format(
                tier=row["tier"],
                n=row["n_models"],
                execution=pct(row["execution"]),
                structural=pct(row["structural"]),
                gap=pct(row["execution_structure_gap"]),
                de="--" if row["delta_execution"] is None else f"{100.0 * row['delta_execution']:+.2f} pp",
                ds="--" if row["delta_structural"] is None else f"{100.0 * row['delta_structural']:+.2f} pp",
            )
        )
    lines.append("")
    lines.append("## Paired Upgrade Comparisons")
    lines.append("")
    lines.append("| comparison | execution before -> after | structural before -> after | delta execution | delta structural | delta gate types | delta gate count |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in upgrades:
        lines.append(
            "| {comparison} | {eb} -> {ea} | {sb} -> {sa} | {de} pp | {ds} pp | {dgt} pp | {dgc} pp |".format(
                comparison=row["comparison"],
                eb=pct(row["execution_before"]),
                ea=pct(row["execution_after"]),
                sb=pct(row["structural_before"]),
                sa=pct(row["structural_after"]),
                de=pp(row["delta_execution"]),
                ds=pp(row["delta_structural"]),
                dgt=pp(row["delta_gate_types"]),
                dgc=pp(row["delta_gate_count"]),
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The statistical summaries support a cautious diminishing-returns claim. On the task side, reference-signature success decreases most strongly with gate-type count and gate entropy, while raw qubit count has almost no relationship with prompt-level signature-match rate in this split. On the model side, stronger systems rapidly approach high execution and QASM3 rates, while reference-signature match improves more slowly and clusters in a narrower high-50% to low-60% range for frontier APIs. Most paired upgrades improve signature match in the final 21-model matrix, but the gains are uneven and are generally smaller than the largest execution improvements; the matched Mistral parent-specialist comparison is reported separately and does not improve on this split. This pattern suggests that additional capability improves executable formatting and partial circuit recovery without closing the stricter source-signature gap."
    )
    lines.append("")
    lines.append("Caveat: these are descriptive statistics over the final 154-prompt held-out split. They are useful release-bound evidence, not universal scaling laws.")
    lines.append("")
    args.md_out.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
