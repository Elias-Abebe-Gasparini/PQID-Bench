"""Check whether repeated target-metadata signatures drive headline scores."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROMPT_JSONL = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
MATRIX_CSV = ROOT / "artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
JSON_OUT = ROOT / "artifacts/analysis_154/pqid_bench_signature_sensitivity_report.json"
MD_OUT = ROOT / "artifacts/analysis_154/pqid_bench_signature_sensitivity_report.md"

NON_MODEL_COLUMNS = {
    "prompt_id",
    "label",
    "solved_models",
    "difficulty",
    "num_qubits",
    "num_clbits",
    "gate_count",
    "gate_type_count",
    "families",
    "instruction",
}


def read_prompts(path: Path = PROMPT_JSONL) -> dict[str, dict[str, Any]]:
    prompts: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            prompts[str(record["prompt_id"])] = record
    return prompts


def read_matrix(path: Path = MATRIX_CSV) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def metadata_signature(prompt: dict[str, Any]) -> tuple[Any, ...]:
    metadata = prompt["target_metadata"]
    return (
        int(metadata["num_qubits"]),
        int(metadata["num_clbits"]),
        int(metadata["gate_count"]),
        tuple(sorted((str(k), int(v)) for k, v in metadata["gate_types"].items())),
    )


def compact_signature(signature: tuple[Any, ...]) -> dict[str, Any]:
    q, c, gates, gate_types = signature
    return {
        "num_qubits": q,
        "num_clbits": c,
        "gate_count": gates,
        "gate_types": dict(gate_types),
    }


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def run(
    prompt_jsonl: Path = PROMPT_JSONL,
    matrix_csv: Path = MATRIX_CSV,
) -> dict[str, Any]:
    prompts = read_prompts(prompt_jsonl)
    matrix_rows = read_matrix(matrix_csv)
    if not matrix_rows:
        raise RuntimeError("No model-by-prompt matrix rows found.")

    model_columns = [c for c in matrix_rows[0] if c not in NON_MODEL_COLUMNS]
    rows_by_prompt = {row["prompt_id"]: row for row in matrix_rows}

    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for prompt_id, prompt in prompts.items():
        if prompt_id in rows_by_prompt:
            groups[metadata_signature(prompt)].append(prompt_id)

    duplicate_groups = {
        signature: sorted(prompt_ids)
        for signature, prompt_ids in groups.items()
        if len(prompt_ids) > 1
    }

    original_values = [
        int(row[model])
        for row in matrix_rows
        for model in model_columns
    ]
    original_overall = sum(original_values) / len(original_values)

    collapsed_values = []
    for prompt_ids in groups.values():
        for model in model_columns:
            collapsed_values.append(
                sum(int(rows_by_prompt[prompt_id][model]) for prompt_id in prompt_ids)
                / len(prompt_ids)
            )
    collapsed_overall = sum(collapsed_values) / len(collapsed_values)

    per_model = []
    for model in model_columns:
        original = sum(int(row[model]) for row in matrix_rows) / len(matrix_rows)
        collapsed_model_values = []
        for prompt_ids in groups.values():
            collapsed_model_values.append(
                sum(int(rows_by_prompt[prompt_id][model]) for prompt_id in prompt_ids)
                / len(prompt_ids)
            )
        collapsed = sum(collapsed_model_values) / len(collapsed_model_values)
        per_model.append(
            {
                "model": model,
                "prompt_level": original,
                "signature_collapsed": collapsed,
                "delta_pp": 100 * (collapsed - original),
            }
        )

    duplicate_rows = []
    for signature, prompt_ids in sorted(
        duplicate_groups.items(),
        key=lambda item: (-len(item[1]), compact_signature(item[0])["num_qubits"], item[1]),
    ):
        prompt_success = []
        for prompt_id in prompt_ids:
            row = rows_by_prompt[prompt_id]
            prompt_success.append(
                {
                    "prompt_id": prompt_id,
                    "label": prompts[prompt_id]["label"],
                    "row_id": prompts[prompt_id]["row_id"],
                    "mean_structural_success": sum(int(row[model]) for model in model_columns)
                    / len(model_columns),
                    "instruction": prompts[prompt_id]["instruction"],
                }
            )
        duplicate_rows.append(
            {
                "group_size": len(prompt_ids),
                "signature": compact_signature(signature),
                "prompts": prompt_success,
            }
        )

    return {
        "summary": {
            "prompt_count": len(matrix_rows),
            "model_count": len(model_columns),
            "prompt_model_cells": len(original_values),
            "unique_metadata_signatures": len(groups),
            "duplicate_signature_groups": len(duplicate_groups),
            "prompts_in_duplicate_signature_groups": sum(
                len(prompt_ids) for prompt_ids in duplicate_groups.values()
            ),
            "largest_duplicate_group_size": max(
                (len(prompt_ids) for prompt_ids in duplicate_groups.values()),
                default=1,
            ),
            "prompt_level_structural_match": original_overall,
            "signature_collapsed_structural_match": collapsed_overall,
            "signature_collapsed_delta_pp": 100 * (collapsed_overall - original_overall),
        },
        "per_model": per_model,
        "duplicate_signature_groups": duplicate_rows,
    }


def write_markdown(payload: dict[str, Any], path: Path = MD_OUT) -> None:
    summary = payload["summary"]
    lines = [
        "# PQID-Bench Structural-Signature Sensitivity Report",
        "",
        "This report checks whether repeated target-metadata signatures drive the headline external-generation result. The signature used here is conservative and evaluator-facing: `(num_qubits, num_clbits, gate_count, gate-type multiset)`. It does not claim full quantum semantic equivalence, but it identifies prompt variants that share the same frozen structural metadata used by the all-structure scorer.",
        "",
        "## Summary",
        "",
        f"- held-out prompt instances: `{summary['prompt_count']}`",
        f"- completed named external model rows: `{summary['model_count']}`",
        f"- prompt-model cells: `{summary['prompt_model_cells']}`",
        f"- unique target-metadata signatures: `{summary['unique_metadata_signatures']}`",
        f"- duplicate-signature groups: `{summary['duplicate_signature_groups']}`",
        f"- prompt instances in duplicate-signature groups: `{summary['prompts_in_duplicate_signature_groups']}`",
        f"- largest duplicate-signature group: `{summary['largest_duplicate_group_size']}`",
        f"- prompt-level structural match: `{pct(summary['prompt_level_structural_match'])}`",
        f"- signature-collapsed structural match: `{pct(summary['signature_collapsed_structural_match'])}`",
        f"- collapsed-minus-prompt delta: `{summary['signature_collapsed_delta_pp']:.2f} pp`",
        "",
        "## Per-Model Sensitivity",
        "",
        "| model | prompt-level structural | signature-collapsed structural | delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in payload["per_model"]:
        lines.append(
            f"| `{row['model']}` | {pct(row['prompt_level'])} | "
            f"{pct(row['signature_collapsed'])} | {row['delta_pp']:+.2f} pp |"
        )

    lines.extend(
        [
            "",
            "## Duplicate Metadata-Signature Groups",
            "",
            "| group | target-metadata signature | prompt ids | prompt-level structural means |",
            "| ---: | --- | --- | --- |",
        ]
    )
    for index, group in enumerate(payload["duplicate_signature_groups"], start=1):
        signature = group["signature"]
        gate_text = ", ".join(
            f"{gate}:{count}" for gate, count in sorted(signature["gate_types"].items())
        )
        signature_text = (
            f"{signature['num_qubits']}q/{signature['num_clbits']}c; "
            f"{signature['gate_count']} gates; {gate_text}"
        )
        prompt_ids = ", ".join(f"`{row['prompt_id']}`" for row in group["prompts"])
        means = ", ".join(
            f"{row['prompt_id'].rsplit('_', 1)[-1]}={pct(row['mean_structural_success'])}"
            for row in group["prompts"]
        )
        lines.append(f"| {index} | {signature_text} | {prompt_ids} | {means} |")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-jsonl", type=Path, default=PROMPT_JSONL)
    parser.add_argument("--matrix-csv", type=Path, default=MATRIX_CSV)
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    args = parser.parse_args()

    payload = run(args.prompt_jsonl, args.matrix_csv)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, args.md_out)
    summary = payload["summary"]
    print(
        "Structural-signature sensitivity: "
        f"{summary['prompt_count']} prompts, "
        f"{summary['unique_metadata_signatures']} signatures, "
        f"{pct(summary['prompt_level_structural_match'])} -> "
        f"{pct(summary['signature_collapsed_structural_match'])} "
        f"({summary['signature_collapsed_delta_pp']:+.2f} pp)."
    )


if __name__ == "__main__":
    main()
