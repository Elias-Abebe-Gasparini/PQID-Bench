"""Build PQID-Bench item difficulty and failure-decomposition artifacts.

This script creates the next diagnostic layer for the external-model benchmark:

- model-by-prompt structural-match matrix;
- item difficulty scores;
- conditional structural fidelity among executable outputs;
- primary and component-wise failure taxonomies;
- model-tier by circuit-feature interaction summaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from pqid_bench_model_registry import (
    EXPANDED_MODEL_ORDER,
    FRONTIER_MODELS,
    LOW_EXPERIMENTAL_MODELS,
    MODEL_ORDER,
    STRONG_OPEN_CODE_MODELS,
    model_from_report_dir,
)


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
JSON_OUT = ANALYSIS_DIR / "pqid_bench_item_failure_matrix_analysis.json"
MD_OUT = ANALYSIS_DIR / "pqid_bench_item_failure_matrix_analysis.md"
CSV_OUT = ANALYSIS_DIR / "pqid_bench_model_by_prompt_structural_matrix.csv"

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

FAMILY_PATTERNS: list[tuple[str, str]] = [
    ("teleportation", r"teleport"),
    ("bell_or_superdense", r"\bbell\b|superdense"),
    ("ghz", r"\bghz\b"),
    ("fourier_qft_phase", r"qft|fourier|controlled-phase|controlled phase"),
    ("deutsch_jozsa", r"deutsch"),
    ("bernstein_vazirani", r"bernstein"),
    ("simon", r"\bsimon\b"),
    ("grover_setup", r"\bgrover\b"),
    ("error_correction", r"bit-flip|bit flip|phase-flip|phase flip|error-correction|error correction"),
    ("vqc_ansatz", r"vqc|variational|ansatz"),
    ("oracle_logic", r"oracle|x-cx-x|x.cx.x"),
    ("arithmetic_toffoli", r"half-adder|half adder|toffoli|ccx"),
    ("qkd_e91", r"\be91\b|qkd"),
    ("pauli_measurement", r"pauli|measure|measurement"),
    ("deep_mixed_rotation", r"deep gate sequence|rxx|rzz|swap"),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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


def model_tier(model: str) -> str:
    if model in FRONTIER_MODELS:
        return "frontier"
    if model in STRONG_OPEN_CODE_MODELS:
        return "strong_open_code"
    if model in LOW_EXPERIMENTAL_MODELS:
        return "low_experimental"
    return "other"


def family_labels(instruction: str) -> list[str]:
    labels = [
        label
        for label, pattern in FAMILY_PATTERNS
        if re.search(pattern, instruction, flags=re.IGNORECASE)
    ]
    return labels or ["generic_or_low_level"]


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
    names = set(gates)
    return {
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "label": prompt["label"],
        "instruction": prompt["instruction"],
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "gate_count": int(metadata["gate_count"]),
        "gate_type_count": len(gates),
        "gate_entropy": gate_entropy(gates),
        "has_measure": "measure" in names,
        "has_barrier": "barrier" in names,
        "has_controlled_or_entangling": bool(names & CONTROLLED_OR_ENTANGLING_GATES),
        "has_rotation": bool(names & ROTATION_GATES),
        "high_gate_diversity": len(gates) >= 5,
        "high_gate_count": int(metadata["gate_count"]) >= 13,
        "families": family_labels(prompt["instruction"]),
    }


def primary_failure(record: dict[str, Any]) -> str:
    execution = record["execution"]
    checks = record["checks"]
    if record["empty_generation"]:
        return "empty_generation"
    if not execution["python_execution_success"]:
        error = execution.get("execution_error_type") or "unknown"
        return f"execution_failure:{error}"
    if not execution["circuit_found"]:
        return "no_circuit_found"
    if checks.get("all_match"):
        return "structural_match"
    if not checks.get("gate_types_match"):
        return "gate_types_mismatch"
    if not checks.get("num_clbits_match"):
        return "num_clbits_mismatch"
    if not checks.get("num_qubits_match"):
        return "num_qubits_mismatch"
    if not checks.get("gate_count_match"):
        return "gate_count_mismatch"
    if not execution["qasm3_success"]:
        return "qasm3_export_failure"
    return "structural_other"


def load_evaluations(eval_dirs: Path | list[Path]) -> list[dict[str, Any]]:
    rows = []
    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            for record in report.get("records", []):
                execution = record.get("execution", {})
                checks = record.get("structural_checks") or {}
                python_execution_success = bool(execution.get("execution_success"))
                circuit_found = bool(execution.get("circuit_found"))
                row = {
                    "prompt_id": record["prompt_id"],
                    "row_id": record.get("row_id"),
                    "provider": record.get("provider"),
                    "model": model,
                    "model_tier": model_tier(model),
                    "empty_generation": bool(record.get("empty_generation")),
                    "execution": {
                        "python_execution_success": python_execution_success,
                        "execution_success": python_execution_success and circuit_found,
                        "circuit_found": circuit_found,
                        "execution_error_type": execution.get("execution_error_type"),
                        "qasm3_success": bool((execution.get("qasm3_export") or {}).get("success")),
                        "qasm3_error_type": (execution.get("qasm3_export") or {}).get("error_type"),
                    },
                    "checks": {
                        "all_match": bool(checks.get("all_match")),
                        "gate_types_match": bool(checks.get("gate_types_match")),
                        "gate_count_match": bool(checks.get("gate_count_match")),
                        "num_qubits_match": bool(checks.get("num_qubits_match")),
                        "num_clbits_match": bool(checks.get("num_clbits_match")),
                    },
                }
                row["primary_failure"] = primary_failure(row)
                rows.append(row)
    return rows


def summarize_binary(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(bool(row[key]) for row in rows) / len(rows)


def rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    execution_success = sum(row["execution"]["execution_success"] for row in rows)
    structural = sum(row["checks"]["all_match"] for row in rows)
    qasm3 = sum(row["execution"]["qasm3_success"] for row in rows)
    runnable_wrong = sum(row["execution"]["execution_success"] and not row["checks"]["all_match"] for row in rows)
    qasm_wrong = sum(row["execution"]["qasm3_success"] and not row["checks"]["all_match"] for row in rows)
    return {
        "n": len(rows),
        "execution_success": execution_success / len(rows),
        "structural_all_match": structural / len(rows),
        "qasm3_success": qasm3 / len(rows),
        "structural_given_execution": structural / execution_success if execution_success else None,
        "runnable_but_structurally_wrong": runnable_wrong / len(rows),
        "runnable_wrong_given_execution": runnable_wrong / execution_success if execution_success else None,
        "qasm3_but_structurally_wrong": qasm_wrong / len(rows),
        "gate_types_match": sum(row["checks"]["gate_types_match"] for row in rows) / len(rows),
        "gate_count_match": sum(row["checks"]["gate_count_match"] for row in rows) / len(rows),
        "num_qubits_match": sum(row["checks"]["num_qubits_match"] for row in rows) / len(rows),
        "num_clbits_match": sum(row["checks"]["num_clbits_match"] for row in rows) / len(rows),
    }


def group_rates(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    out = []
    for group, group_rows in sorted(grouped.items()):
        item = rates(group_rows)
        item["group"] = group
        out.append(item)
    return out


def write_matrix_csv(path: Path, item_rows: list[dict[str, Any]], matrix: dict[str, dict[str, int | None]]) -> None:
    fieldnames = [
        "prompt_id",
        "label",
        "solved_models",
        "difficulty",
        "num_qubits",
        "num_clbits",
        "gate_count",
        "gate_type_count",
        "families",
        *MODEL_ORDER,
        "instruction",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in item_rows:
            matrix_row = matrix[row["prompt_id"]]
            output = {
                "prompt_id": row["prompt_id"],
                "label": row["label"],
                "solved_models": row["solved_models"],
                "difficulty": f"{row['difficulty']:.6f}",
                "num_qubits": row["num_qubits"],
                "num_clbits": row["num_clbits"],
                "gate_count": row["gate_count"],
                "gate_type_count": row["gate_type_count"],
                "families": ";".join(row["families"]),
                "instruction": row["instruction"],
            }
            for model in MODEL_ORDER:
                value = matrix_row.get(model)
                output[model] = "" if value is None else value
            writer.writerow(output)


def markdown_rate_table(rows: list[dict[str, Any]], group_label: str = "group") -> list[str]:
    lines = [
        f"| {group_label} | n | execution | structural | M given E | runnable wrong | gate types | gate count | qubits | clbits |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {group} | {n} | {execution} | {structural} | {conditional} | {runnable_wrong} | {gate_types} | {gate_count} | {qubits} | {clbits} |".format(
                group=row["group"],
                n=row["n"],
                execution=pct(row.get("execution_success")),
                structural=pct(row.get("structural_all_match")),
                conditional=pct(row.get("structural_given_execution")),
                runnable_wrong=pct(row.get("runnable_but_structurally_wrong")),
                gate_types=pct(row.get("gate_types_match")),
                gate_count=pct(row.get("gate_count_match")),
                qubits=pct(row.get("num_qubits_match")),
                clbits=pct(row.get("num_clbits_match")),
            )
        )
    return lines


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
    parser.add_argument(
        "--expanded-roster",
        action="store_true",
        help="Backward-compatible alias; the final primary roster contains 21 models.",
    )
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--csv-out", type=Path, default=CSV_OUT)
    args = parser.parse_args()

    if args.expanded_roster:
        MODEL_ORDER = list(EXPANDED_MODEL_ORDER)
    eval_dirs = args.eval_dir or DEFAULT_EVAL_DIRS

    prompts = read_jsonl(args.prompt_path)
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
        missing = sorted(expected - observed)[:10]
        extras = sorted(observed - expected)[:10]
        raise RuntimeError(
            f"Incomplete evaluation roster: missing={len(expected - observed)} {missing}; "
            f"extras={len(observed - expected)} {extras}"
        )

    matrix: dict[str, dict[str, int | None]] = {
        prompt["prompt_id"]: {model: None for model in MODEL_ORDER} for prompt in prompts
    }
    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        matrix[row["prompt_id"]][row["model"]] = int(row["checks"]["all_match"])
        by_prompt[row["prompt_id"]].append(row)
        by_model[row["model"]].append(row)

    item_rows = []
    for prompt in prompts:
        prompt_id = prompt["prompt_id"]
        rows = by_prompt[prompt_id]
        solved = sum(row["checks"]["all_match"] for row in rows)
        frontier_solved = sum(row["checks"]["all_match"] for row in rows if row["model"] in FRONTIER_MODELS)
        non_frontier_solved = sum(row["checks"]["all_match"] for row in rows if row["model"] not in FRONTIER_MODELS)
        feature_row = features[prompt_id]
        item_rows.append(
            {
                **feature_row,
                "models": len(rows),
                "solved_models": solved,
                "difficulty": 1.0 - solved / len(rows) if rows else 1.0,
                "execution_rate": sum(row["execution"]["execution_success"] for row in rows) / len(rows),
                "structural_rate": solved / len(rows),
                "frontier_solved": frontier_solved,
                "non_frontier_solved": non_frontier_solved,
            }
        )
    item_rows = sorted(item_rows, key=lambda row: (-row["difficulty"], -row["gate_type_count"], -row["gate_count"], row["prompt_id"]))

    overall = rates(joined)
    by_tier = group_rates(joined, "model_tier")
    by_model_rows = []
    for model in MODEL_ORDER:
        if model in by_model:
            item = rates(by_model[model])
            item["group"] = model
            by_model_rows.append(item)

    component_mismatch_counts = Counter()
    component_mismatch_executed_counts = Counter()
    for row in joined:
        if not row["checks"]["all_match"]:
            for check in ["gate_types_match", "gate_count_match", "num_qubits_match", "num_clbits_match"]:
                if not row["checks"][check]:
                    component_mismatch_counts[check] += 1
                    if row["execution"]["execution_success"]:
                        component_mismatch_executed_counts[check] += 1

    primary_failure_counts = Counter(row["primary_failure"] for row in joined)
    item_buckets = {
        "universal_easy": [row for row in item_rows if row["solved_models"] == len(MODEL_ORDER)],
        "universal_hard": [row for row in item_rows if row["solved_models"] == 0],
        "frontier_only": [
            row
            for row in item_rows
            if row["frontier_solved"] > 0 and row["non_frontier_solved"] == 0
        ],
        "non_frontier_only": [
            row
            for row in item_rows
            if row["frontier_solved"] == 0 and row["non_frontier_solved"] > 0
        ],
        "mixed_disagreement": [
            row
            for row in item_rows
            if 0 < row["solved_models"] < len(MODEL_ORDER)
        ],
    }

    tier_feature_rows = []
    for feature in ["high_gate_diversity", "has_barrier", "has_controlled_or_entangling", "has_rotation"]:
        for tier in ["frontier", "strong_open_code", "low_experimental"]:
            for value in [False, True]:
                subset = [
                    row
                    for row in joined
                    if row["model_tier"] == tier and bool(row[feature]) == value
                ]
                item = rates(subset)
                item["feature"] = feature
                item["value"] = value
                item["tier"] = tier
                tier_feature_rows.append(item)

    result = {
        "roster": "final_21_primary",
        "prompt_count": len(prompts),
        "model_count": len(MODEL_ORDER),
        "evaluation_count": len(joined),
        "overall": overall,
        "primary_failure_counts": dict(primary_failure_counts.most_common()),
        "component_mismatch_counts_among_all_nonmatches": dict(component_mismatch_counts.most_common()),
        "component_mismatch_counts_among_executed_nonmatches": dict(component_mismatch_executed_counts.most_common()),
        "by_model_tier": by_tier,
        "by_model": by_model_rows,
        "item_bucket_counts": {key: len(value) for key, value in item_buckets.items()},
        "hardest_items": item_rows[:15],
        "easiest_items": sorted(item_rows, key=lambda row: (row["difficulty"], row["gate_count"], row["prompt_id"]))[:15],
        "frontier_only_items": item_buckets["frontier_only"][:15],
        "non_frontier_only_items": item_buckets["non_frontier_only"][:15],
        "tier_feature_interactions": tier_feature_rows,
        "matrix_csv": str(args.csv_out),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_matrix_csv(args.csv_out, item_rows, matrix)

    lines: list[str] = []
    lines.append("# PQID-Bench Item Difficulty And Failure Matrix")
    lines.append("")
    lines.append(f"- prompts: `{len(prompts)}`")
    lines.append(f"- models: `{len(MODEL_ORDER)}`")
    lines.append(f"- prompt-model evaluations: `{len(joined)}`")
    lines.append(f"- structural matrix CSV: `{args.csv_out}`")
    lines.append("")
    lines.append("## Conditional Fidelity")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("| --- | ---: |")
    lines.append(f"| execution success | {pct(overall['execution_success'])} |")
    lines.append(f"| structural match | {pct(overall['structural_all_match'])} |")
    lines.append(f"| structural match given execution, P(M=1 given E=1) | {pct(overall['structural_given_execution'])} |")
    lines.append(f"| runnable but structurally wrong | {pct(overall['runnable_but_structurally_wrong'])} |")
    lines.append(f"| runnable wrong among executable outputs | {pct(overall['runnable_wrong_given_execution'])} |")
    lines.append(f"| QASM3-exportable but structurally wrong | {pct(overall['qasm3_but_structurally_wrong'])} |")
    lines.append("")
    lines.append("## Primary Failure Taxonomy")
    lines.append("")
    lines.append("| primary outcome/failure | count | share |")
    lines.append("| --- | ---: | ---: |")
    total = len(joined)
    for key, count in primary_failure_counts.most_common():
        lines.append(f"| `{key}` | {count} | {pct(count / total)} |")
    lines.append("")
    lines.append("## Component Mismatches Among Nonmatches")
    lines.append("")
    lines.append("| component | all nonmatches | executed nonmatches |")
    lines.append("| --- | ---: | ---: |")
    for key in ["gate_types_match", "num_clbits_match", "num_qubits_match", "gate_count_match"]:
        lines.append(
            f"| `{key}` failed | {component_mismatch_counts.get(key, 0)} | {component_mismatch_executed_counts.get(key, 0)} |"
        )
    lines.append("")
    lines.append("## Model Tiers")
    lines.extend(markdown_rate_table(by_tier))
    lines.append("")
    lines.append("## Model-Level Conditional Fidelity")
    lines.extend(markdown_rate_table(by_model_rows))
    lines.append("")
    lines.append("## Item Difficulty Buckets")
    lines.append("")
    lines.append("| bucket | prompts |")
    lines.append("| --- | ---: |")
    for key, value in result["item_bucket_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    lines.append("## Hardest Items")
    lines.append("")
    lines.append(f"| prompt | solved / {len(MODEL_ORDER)} | difficulty | q | c | gates | gate types | families | instruction excerpt |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in result["hardest_items"][:10]:
        excerpt = row["instruction"].replace("|", "/")[:120]
        lines.append(
            f"| `{row['prompt_id']}` | {row['solved_models']} | {row['difficulty']:.3f} | {row['num_qubits']} | {row['num_clbits']} | {row['gate_count']} | {row['gate_type_count']} | {', '.join(row['families'])} | {excerpt} |"
        )
    lines.append("")
    lines.append("## Easiest Items")
    lines.append("")
    lines.append(f"| prompt | solved / {len(MODEL_ORDER)} | difficulty | q | c | gates | gate types | families | instruction excerpt |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in result["easiest_items"][:10]:
        excerpt = row["instruction"].replace("|", "/")[:120]
        lines.append(
            f"| `{row['prompt_id']}` | {row['solved_models']} | {row['difficulty']:.3f} | {row['num_qubits']} | {row['num_clbits']} | {row['gate_count']} | {row['gate_type_count']} | {', '.join(row['families'])} | {excerpt} |"
        )
    lines.append("")
    lines.append("## Tier-Feature Interactions")
    lines.append("")
    lines.append("| feature | value | tier | n | structural | M given E | runnable wrong |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: |")
    for row in tier_feature_rows:
        lines.append(
            f"| `{row['feature']}` | `{row['value']}` | `{row['tier']}` | {row['n']} | {pct(row.get('structural_all_match'))} | {pct(row.get('structural_given_execution'))} | {pct(row.get('runnable_but_structurally_wrong'))} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The matrix confirms that PQID-Bench is not only separating executable from non-executable outputs. Among executable outputs, only about three fifths are structurally correct, so a large share of model behavior is runnable but scientifically wrong. The primary failure taxonomy shows that gate-type mismatch is the dominant structural failure after execution succeeds, followed by classical-bit, qubit, and gate-count mismatches. Item difficulty is highly concentrated: several prompts are solved by all models, while several protocol-like or heterogeneous prompts are solved by none."
    )
    lines.append("")
    args.md_out.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.csv_out}")


if __name__ == "__main__":
    main()
