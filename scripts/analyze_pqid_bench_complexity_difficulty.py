"""Analyze PQID-Bench external results by circuit complexity descriptors.

This script joins the held-out external-generation prompts with all completed
external-model evaluation reports and asks whether structural success decreases
as target circuits become wider, longer, or more gate-diverse.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from pqid_bench_model_registry import EXPANDED_MODEL_ORDER, MODEL_ORDER, model_from_report_dir


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
JSON_OUT = ROOT / "artifacts/analysis_154/pqid_bench_complexity_difficulty_analysis.json"
MD_OUT = ROOT / "artifacts/analysis_154/pqid_bench_complexity_difficulty_analysis.md"


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


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def width_bin(q: int) -> str:
    if q <= 2:
        return "1-2 qubits"
    if q == 3:
        return "3 qubits"
    if q == 4:
        return "4 qubits"
    if q <= 8:
        return "5-8 qubits"
    return "9+ qubits"


def gate_count_bin(g: int) -> str:
    if g <= 4:
        return "2-4 gates"
    if g <= 8:
        return "5-8 gates"
    if g <= 12:
        return "9-12 gates"
    if g <= 20:
        return "13-20 gates"
    return "21+ gates"


def diversity_bin(d: int) -> str:
    if d <= 2:
        return "1-2 gate types"
    if d <= 4:
        return "3-4 gate types"
    return "5+ gate types"


def clbit_bin(c: int) -> str:
    if c == 0:
        return "0 clbits"
    if c <= 2:
        return "1-2 clbits"
    if c == 3:
        return "3 clbits"
    return "4+ clbits"


def family_labels(instruction: str) -> list[str]:
    labels = [
        label
        for label, pattern in FAMILY_PATTERNS
        if re.search(pattern, instruction, flags=re.IGNORECASE)
    ]
    return labels or ["generic_or_low_level"]


def prompt_features(prompt: dict[str, Any]) -> dict[str, Any]:
    metadata = prompt["target_metadata"]
    gate_types = {str(k): int(v) for k, v in metadata["gate_types"].items()}
    q = int(metadata["num_qubits"])
    c = int(metadata["num_clbits"])
    g = int(metadata["gate_count"])
    d = len(gate_types)
    total_ops = sum(gate_types.values())
    entropy = 0.0
    if total_ops:
        for count in gate_types.values():
            p = count / total_ops
            entropy -= p * math.log(p)
    gate_names = set(gate_types)
    return {
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "label": prompt["label"],
        "instruction": prompt["instruction"],
        "num_qubits": q,
        "num_clbits": c,
        "gate_count": g,
        "gate_type_count": d,
        "gate_entropy": entropy,
        "gate_types": gate_types,
        "width_bin": width_bin(q),
        "clbit_bin": clbit_bin(c),
        "gate_count_bin": gate_count_bin(g),
        "diversity_bin": diversity_bin(d),
        "has_measure": "measure" in gate_names,
        "has_barrier": "barrier" in gate_names,
        "has_controlled_or_entangling": bool(gate_names & CONTROLLED_OR_ENTANGLING_GATES),
        "has_rotation": bool(gate_names & ROTATION_GATES),
        "families": family_labels(prompt["instruction"]),
    }


def load_evaluations(eval_dirs: Path | list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            report = json.loads(report_path.read_text(encoding="utf-8"))
            records = report.get("records", [])
            if not records:
                continue
            provider = records[0].get("provider", report_path.parent.name)
            model = model_from_report_dir(report_path.parent.name)
            if model not in MODEL_ORDER:
                continue
            for record in records:
                execution = record.get("execution", {})
                checks = record.get("structural_checks") or {}
                qasm = execution.get("qasm3_export") or {}
                circuit_found = bool(execution.get("circuit_found"))
                rows.append(
                    {
                        "report_dir": report_path.parent.name,
                        "provider": provider,
                        "model": model,
                        "model_key": model,
                        "prompt_id": record["prompt_id"],
                        "label": record.get("label"),
                        "execution_success": bool(execution.get("execution_success")) and circuit_found,
                        "circuit_found": circuit_found,
                        "qasm3_success": bool(qasm.get("success")),
                        "structural_all_match": bool(checks.get("all_match")),
                        "gate_types_match": bool(checks.get("gate_types_match")),
                        "gate_count_match": bool(checks.get("gate_count_match")),
                        "num_qubits_match": bool(checks.get("num_qubits_match")),
                        "num_clbits_match": bool(checks.get("num_clbits_match")),
                        "execution_error_type": execution.get("execution_error_type"),
                    }
                )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "evaluations": 0,
            "prompts": 0,
            "models": 0,
            "execution_success": 0.0,
            "structural_all_match": 0.0,
            "qasm3_success": 0.0,
            "gate_types_match": 0.0,
            "gate_count_match": 0.0,
            "num_qubits_match": 0.0,
            "num_clbits_match": 0.0,
        }
    total = len(rows)
    return {
        "evaluations": total,
        "prompts": len({row["prompt_id"] for row in rows}),
        "models": len({row["model_key"] for row in rows}),
        "execution_success": sum(row["execution_success"] for row in rows) / total,
        "structural_all_match": sum(row["structural_all_match"] for row in rows) / total,
        "qasm3_success": sum(row["qasm3_success"] for row in rows) / total,
        "gate_types_match": sum(row["gate_types_match"] for row in rows) / total,
        "gate_count_match": sum(row["gate_count_match"] for row in rows) / total,
        "num_qubits_match": sum(row["num_qubits_match"] for row in rows) / total,
        "num_clbits_match": sum(row["num_clbits_match"] for row in rows) / total,
    }


def group_summary(rows: list[dict[str, Any]], key: str, order: list[str] | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    keys = order or sorted(grouped)
    output = []
    for value in keys:
        if value in grouped:
            item = summarize(grouped[value])
            item["group"] = value
            output.append(item)
    return output


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar = mean(xs)
    ybar = mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xden = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    yden = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    if xden == 0 or yden == 0:
        return None
    return numerator / (xden * yden)


def markdown_table(rows: list[dict[str, Any]], title_col: str = "group") -> list[str]:
    header = title_col.replace("_", " ")
    lines = [
        f"| {header} | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {group} | {prompts} | {evaluations} | {execution} | {structural} | {gate_types} | {gate_count} | {qubits} | {clbits} | {qasm3} |".format(
                group=row[title_col],
                prompts=row["prompts"],
                evaluations=row["evaluations"],
                execution=pct(row["execution_success"]),
                structural=pct(row["structural_all_match"]),
                gate_types=pct(row["gate_types_match"]),
                gate_count=pct(row["gate_count_match"]),
                qubits=pct(row["num_qubits_match"]),
                clbits=pct(row["num_clbits_match"]),
                qasm3=pct(row["qasm3_success"]),
            )
        )
    return lines


def main() -> None:
    global MODEL_ORDER

    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument("--eval-dir", type=Path, action="append", default=None)
    parser.add_argument("--expanded-roster", action="store_true")
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument(
        "--exclude-prompt-id",
        action="append",
        default=[],
        help="Exclude a prompt ID from the descriptive sensitivity analysis; may be repeated.",
    )
    args = parser.parse_args()

    if args.expanded_roster:
        MODEL_ORDER = list(EXPANDED_MODEL_ORDER)
    eval_dirs = args.eval_dir or DEFAULT_EVAL_DIRS

    prompts = read_jsonl(args.prompt_path)
    excluded_prompt_ids = set(args.exclude_prompt_id)
    if excluded_prompt_ids:
        prompts = [prompt for prompt in prompts if prompt["prompt_id"] not in excluded_prompt_ids]
    feature_by_prompt = {prompt["prompt_id"]: prompt_features(prompt) for prompt in prompts}
    eval_rows = load_evaluations(eval_dirs)

    joined: list[dict[str, Any]] = []
    for row in eval_rows:
        features = feature_by_prompt.get(row["prompt_id"])
        if not features:
            continue
        joined.append({**row, **features})
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

    prompt_rows: list[dict[str, Any]] = []
    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        by_prompt[row["prompt_id"]].append(row)
    for prompt_id, rows in sorted(by_prompt.items()):
        features = feature_by_prompt[prompt_id]
        prompt_rows.append(
            {
                **features,
                "models": len({row["model_key"] for row in rows}),
                "execution_rate": sum(row["execution_success"] for row in rows) / len(rows),
                "structural_rate": sum(row["structural_all_match"] for row in rows) / len(rows),
                "qasm3_rate": sum(row["qasm3_success"] for row in rows) / len(rows),
            }
        )

    feature_correlations = {
        name: pearson([float(row[name]) for row in prompt_rows], [float(row["structural_rate"]) for row in prompt_rows])
        for name in ["num_qubits", "num_clbits", "gate_count", "gate_type_count", "gate_entropy"]
    }

    gate_totals: Counter[str] = Counter()
    for prompt in prompts:
        gate_totals.update({str(k): int(v) for k, v in prompt["target_metadata"]["gate_types"].items()})

    width_rows = group_summary(
        joined,
        "width_bin",
        ["1-2 qubits", "3 qubits", "4 qubits", "5-8 qubits", "9+ qubits"],
    )
    gate_count_rows = group_summary(
        joined,
        "gate_count_bin",
        ["2-4 gates", "5-8 gates", "9-12 gates", "13-20 gates", "21+ gates"],
    )
    diversity_rows = group_summary(
        joined,
        "diversity_bin",
        ["1-2 gate types", "3-4 gate types", "5+ gate types"],
    )
    clbit_rows = group_summary(joined, "clbit_bin", ["0 clbits", "1-2 clbits", "3 clbits", "4+ clbits"])

    bool_rows = []
    for key in ["has_measure", "has_barrier", "has_controlled_or_entangling", "has_rotation"]:
        rows = group_summary(joined, key, ["False", "True"])
        for item in rows:
            item["feature"] = key
        bool_rows.extend(rows)

    family_joined = []
    for row in joined:
        for family in row["families"]:
            family_joined.append({**row, "family": family})
    family_rows = group_summary(family_joined, "family")
    family_rows = sorted(family_rows, key=lambda item: (-item["prompts"], item["group"]))

    hardest_prompts = sorted(prompt_rows, key=lambda row: (row["structural_rate"], -row["gate_count"], -row["num_qubits"]))[:10]
    easiest_prompts = sorted(prompt_rows, key=lambda row: (-row["structural_rate"], row["gate_count"], row["num_qubits"]))[:10]

    result = {
        "roster": "final_21_primary",
        "prompt_path": str(args.prompt_path),
        "eval_dirs": [str(path) for path in eval_dirs],
        "excluded_prompt_ids": sorted(excluded_prompt_ids),
        "completed_models": sorted({row["model_key"] for row in joined}),
        "overall": summarize(joined),
        "prompt_profile": {
            "rows": len(prompts),
            "labels": dict(Counter(prompt["label"] for prompt in prompts)),
            "gate_totals": dict(gate_totals.most_common()),
        },
        "by_width": width_rows,
        "by_gate_count": gate_count_rows,
        "by_gate_diversity": diversity_rows,
        "by_clbits": clbit_rows,
        "by_boolean_feature": bool_rows,
        "by_family": family_rows,
        "feature_correlations_with_prompt_structural_rate": feature_correlations,
        "hardest_prompts": hardest_prompts,
        "easiest_prompts": easiest_prompts,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    lines: list[str] = []
    lines.append("# PQID-Bench Complexity-Difficulty Analysis")
    lines.append("")
    overall = result["overall"]
    lines.append(f"- prompts: `{overall['prompts']}`")
    lines.append(f"- completed models: `{overall['models']}`")
    lines.append(f"- prompt-model evaluations: `{overall['evaluations']}`")
    lines.append(f"- pooled execution success: `{pct(overall['execution_success'])}`")
    lines.append(f"- pooled structural match: `{pct(overall['structural_all_match'])}`")
    lines.append("")
    lines.append("## Width")
    lines.extend(markdown_table(width_rows))
    lines.append("")
    lines.append("## Gate Count")
    lines.extend(markdown_table(gate_count_rows))
    lines.append("")
    lines.append("## Gate-Type Diversity")
    lines.extend(markdown_table(diversity_rows))
    lines.append("")
    lines.append("## Classical Bits")
    lines.extend(markdown_table(clbit_rows))
    lines.append("")
    lines.append("## Feature Presence")
    for item in bool_rows:
        item["feature_group"] = f"{item['feature']}={item['group']}"
    lines.extend(markdown_table(bool_rows, title_col="feature_group"))
    lines.append("")
    lines.append("## Prompt-Derived Circuit Families")
    family_public = [row for row in family_rows if row["prompts"] >= 2]
    lines.extend(markdown_table(family_public))
    lines.append("")
    lines.append("Singleton family labels are retained in the JSON artifact but omitted from this table.")
    lines.append("")
    lines.append("## Correlation With Per-Prompt Structural Rate")
    lines.append("")
    lines.append("| descriptor | Pearson r |")
    lines.append("| --- | ---: |")
    for key, value in feature_correlations.items():
        shown = "n/a" if value is None else f"{value:.3f}"
        lines.append(f"| `{key}` | {shown} |")
    lines.append("")
    lines.append("## Hardest Prompts By Mean Structural Match")
    lines.append("")
    lines.append("| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in hardest_prompts:
        excerpt = row["instruction"].replace("|", "/")[:110]
        lines.append(
            f"| `{row['prompt_id']}` | `{row['label']}` | {row['num_qubits']} | {row['num_clbits']} | {row['gate_count']} | {row['gate_type_count']} | {pct(row['structural_rate'])} | {', '.join(row['families'])} | {excerpt} |"
        )
    lines.append("")
    lines.append("## Easiest Prompts By Mean Structural Match")
    lines.append("")
    lines.append("| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in easiest_prompts:
        excerpt = row["instruction"].replace("|", "/")[:110]
        lines.append(
            f"| `{row['prompt_id']}` | `{row['label']}` | {row['num_qubits']} | {row['num_clbits']} | {row['gate_count']} | {row['gate_type_count']} | {pct(row['structural_rate'])} | {', '.join(row['families'])} | {excerpt} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The clearest complexity signal is gate-type diversity: targets with five or more gate types have substantially lower structural-match rates than targets with one or two gate types. Width and gate count are not monotone in this split because many wider circuits are regular Hadamard/CX templates, while some short circuits contain classical-control or gate-order traps. The benchmark therefore supports a refined version of the complexity hypothesis: structural difficulty increases most clearly with heterogeneity and semantic specificity, not with raw qubit count alone."
    )
    lines.append("")

    args.md_out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
