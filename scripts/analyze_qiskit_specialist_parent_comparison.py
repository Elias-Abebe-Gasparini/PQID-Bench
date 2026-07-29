from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECIALIST = (
    ROOT
    / "artifacts/external_model_batches_154/qiskit_mistral/evaluations/"
    "huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai/"
    "pqid_bench_external_model_generation_harness_report.json"
)
DEFAULT_PARENT = (
    ROOT
    / "artifacts/external_model_batches_154/mistral_parent_control/evaluations/"
    "openrouter_mistralai_mistral-small-3_2-24b-instruct/"
    "pqid_bench_external_model_generation_harness_report.json"
)
DEFAULT_SPECIALIST_REQUESTS = (
    ROOT
    / "artifacts/external_model_batches_154/qiskit_mistral/requests/"
    "huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_requests.jsonl"
)
DEFAULT_PARENT_REQUESTS = (
    ROOT
    / "artifacts/external_model_batches_154/mistral_parent_control/requests/"
    "openrouter_mistralai_mistral-small-3_2-24b-instruct_requests.jsonl"
)
DEFAULT_OUTPUT = ROOT / "artifacts/analysis_154/qiskit_specialist_parent_comparison"


def execution_check(row: dict, key: str) -> bool:
    execution = row.get("execution") or {}
    if key == "circuit_found":
        return bool(execution.get(key, False))
    qasm = execution.get("qasm3_export") or {}
    return bool(qasm.get("success", False))


def structural_check(row: dict, key: str) -> bool:
    return bool((row.get("structural_checks") or {}).get(key, False))


METRICS = {
    "execution": lambda row: execution_check(row, "circuit_found"),
    "reference_signature": lambda row: structural_check(row, "all_match"),
    "gate_types": lambda row: structural_check(row, "gate_types_match"),
    "gate_count": lambda row: structural_check(row, "gate_count_match"),
    "qubits": lambda row: structural_check(row, "num_qubits_match"),
    "classical_bits": lambda row: structural_check(row, "num_clbits_match"),
    "qasm3": lambda row: execution_check(row, "qasm3_export"),
}


def read_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def canonical_signature(row: dict) -> str:
    return json.dumps(row["target_metadata"], sort_keys=True, separators=(",", ":"))


def exact_mcnemar_p(specialist_wins: int, parent_wins: int) -> float:
    discordant = specialist_wins + parent_wins
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(specialist_wins, parent_wins) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(np.asarray(p_values))
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        value = min(1.0, (count - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted.tolist()


def compare_metric(
    specialist: np.ndarray,
    parent: np.ndarray,
    cluster_ids: np.ndarray,
    *,
    rng: np.random.Generator,
    bootstrap_samples: int,
    permutation_samples: int,
) -> dict:
    difference = specialist.astype(float) - parent.astype(float)
    unique_clusters = np.unique(cluster_ids)
    cluster_sums = np.asarray(
        [difference[cluster_ids == cluster].sum() for cluster in unique_clusters], dtype=float
    )
    cluster_sizes = np.asarray(
        [(cluster_ids == cluster).sum() for cluster in unique_clusters], dtype=float
    )

    bootstrap_index = rng.integers(
        0, len(unique_clusters), size=(bootstrap_samples, len(unique_clusters))
    )
    bootstrap_difference = (
        cluster_sums[bootstrap_index].sum(axis=1)
        / cluster_sizes[bootstrap_index].sum(axis=1)
    )
    ci_low, ci_high = np.quantile(bootstrap_difference, [0.025, 0.975])

    signs = rng.choice(
        np.asarray([-1.0, 1.0]),
        size=(permutation_samples, len(unique_clusters)),
    )
    permuted = (signs @ cluster_sums) / len(difference)
    observed = float(difference.mean())
    permutation_p = float(
        (1 + np.count_nonzero(np.abs(permuted) >= abs(observed) - 1e-15))
        / (permutation_samples + 1)
    )

    specialist_wins = int(np.count_nonzero((specialist == 1) & (parent == 0)))
    parent_wins = int(np.count_nonzero((specialist == 0) & (parent == 1)))
    ties = int(len(difference) - specialist_wins - parent_wins)
    return {
        "specialist_count": int(specialist.sum()),
        "specialist_rate": float(specialist.mean()),
        "parent_count": int(parent.sum()),
        "parent_rate": float(parent.mean()),
        "difference": observed,
        "cluster_bootstrap_95_ci": [float(ci_low), float(ci_high)],
        "specialist_wins": specialist_wins,
        "parent_wins": parent_wins,
        "ties": ties,
        "cluster_sign_flip_p": permutation_p,
        "exact_mcnemar_p_diagnostic": exact_mcnemar_p(specialist_wins, parent_wins),
    }


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100 * value:+.2f} pp"


def run(args: argparse.Namespace) -> dict:
    specialist_report = read_report(args.specialist_report)
    parent_report = read_report(args.parent_report)
    specialist_rows = {row["prompt_id"]: row for row in specialist_report["records"]}
    parent_rows = {row["prompt_id"]: row for row in parent_report["records"]}
    if set(specialist_rows) != set(parent_rows):
        raise ValueError("Specialist and parent prompt identifiers do not match.")

    prompt_ids = sorted(specialist_rows)
    if len(prompt_ids) != 154:
        raise ValueError(f"Expected 154 paired prompts, found {len(prompt_ids)}.")
    cluster_ids = np.asarray(
        [canonical_signature(parent_rows[prompt_id]) for prompt_id in prompt_ids]
    )
    specialist_requests = {
        row["prompt_id"]: row for row in read_jsonl(args.specialist_requests)
    }
    parent_requests = {row["prompt_id"]: row for row in read_jsonl(args.parent_requests)}
    if set(specialist_requests) != set(prompt_ids) or set(parent_requests) != set(prompt_ids):
        raise ValueError("Request manifests do not cover the same 154 prompt identifiers.")
    input_hash_mismatches = sum(
        specialist_requests[prompt_id]["model_input_sha256"]
        != parent_requests[prompt_id]["model_input_sha256"]
        for prompt_id in prompt_ids
    )
    prompt_hash_mismatches = sum(
        specialist_requests[prompt_id]["prompt_record_sha256"]
        != parent_requests[prompt_id]["prompt_record_sha256"]
        for prompt_id in prompt_ids
    )
    generation_config_match = all(
        specialist_requests[prompt_id]["generation_config"]
        == parent_requests[prompt_id]["generation_config"]
        for prompt_id in prompt_ids
    )
    if input_hash_mismatches or prompt_hash_mismatches or not generation_config_match:
        raise ValueError("Specialist and parent request inputs are not fully matched.")
    rng = np.random.default_rng(args.seed)

    comparisons: dict[str, dict] = {}
    for metric, extractor in METRICS.items():
        specialist = np.asarray(
            [extractor(specialist_rows[prompt_id]) for prompt_id in prompt_ids], dtype=int
        )
        parent = np.asarray(
            [extractor(parent_rows[prompt_id]) for prompt_id in prompt_ids], dtype=int
        )
        comparisons[metric] = compare_metric(
            specialist,
            parent,
            cluster_ids,
            rng=rng,
            bootstrap_samples=args.bootstrap_samples,
            permutation_samples=args.permutation_samples,
        )

    adjusted = holm_adjust(
        [comparisons[metric]["cluster_sign_flip_p"] for metric in METRICS]
    )
    for metric, value in zip(METRICS, adjusted, strict=True):
        comparisons[metric]["holm_p_across_seven_endpoints"] = value

    return {
        "comparison": "Qiskit specialist minus exact Mistral parent",
        "specialist_model": "Qiskit/mistral-small-3.2-24b-qiskit",
        "specialist_route": "Hugging Face Inference Providers / Featherless AI",
        "parent_model": "mistralai/mistral-small-3.2-24b-instruct",
        "parent_route": "OpenRouter pinned to Mistral; fallback disabled",
        "paired_prompts": len(prompt_ids),
        "target_signature_clusters": int(len(np.unique(cluster_ids))),
        "seed": args.seed,
        "cluster_bootstrap_samples": args.bootstrap_samples,
        "cluster_sign_flip_samples": args.permutation_samples,
        "request_input_audit": {
            "paired_request_rows": len(prompt_ids),
            "model_input_sha256_mismatches": input_hash_mismatches,
            "prompt_record_sha256_mismatches": prompt_hash_mismatches,
            "generation_config_match": generation_config_match,
            "generation_config": specialist_requests[prompt_ids[0]]["generation_config"],
        },
        "comparisons": comparisons,
        "interpretation": (
            "The specialist does not outperform its exact parent on the frozen "
            "reference-signature endpoint. Provider route differs, so the comparison "
            "is matched by checkpoint family and evaluation design but not by serving stack."
        ),
    }


def write_outputs(payload: dict, output_prefix: Path) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for metric, result in payload["comparisons"].items():
        rows.append(
            {
                "metric": metric,
                "specialist_count": result["specialist_count"],
                "specialist_rate": result["specialist_rate"],
                "parent_count": result["parent_count"],
                "parent_rate": result["parent_rate"],
                "specialist_minus_parent": result["difference"],
                "cluster_ci_low": result["cluster_bootstrap_95_ci"][0],
                "cluster_ci_high": result["cluster_bootstrap_95_ci"][1],
                "specialist_wins": result["specialist_wins"],
                "parent_wins": result["parent_wins"],
                "ties": result["ties"],
                "cluster_sign_flip_p": result["cluster_sign_flip_p"],
                "holm_p": result["holm_p_across_seven_endpoints"],
                "exact_mcnemar_p_diagnostic": result["exact_mcnemar_p_diagnostic"],
            }
        )
    csv_path = output_prefix.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Qiskit Specialist Versus Exact Mistral Parent",
        "",
        f"- paired prompts: `{payload['paired_prompts']}`",
        f"- target-signature clusters: `{payload['target_signature_clusters']}`",
        f"- cluster bootstrap samples: `{payload['cluster_bootstrap_samples']}`",
        f"- cluster sign-flip samples: `{payload['cluster_sign_flip_samples']}`",
        f"- paired request rows with identical model-input hashes: `{payload['request_input_audit']['paired_request_rows']}`",
        f"- model-input hash mismatches: `{payload['request_input_audit']['model_input_sha256_mismatches']}`",
        f"- prompt-record hash mismatches: `{payload['request_input_audit']['prompt_record_sha256_mismatches']}`",
        f"- generation configuration identical: `{payload['request_input_audit']['generation_config_match']}`",
        "- reported differences are specialist minus parent",
        "",
        "| metric | specialist | parent | difference (95% cluster interval) | specialist wins / parent wins / ties | cluster p | Holm p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for metric, result in payload["comparisons"].items():
        low, high = result["cluster_bootstrap_95_ci"]
        lines.append(
            "| {} | {}/{} ({}) | {}/{} ({}) | {} [{}, {}] | {} / {} / {} | {:.4f} | {:.4f} |".format(
                metric.replace("_", " "),
                result["specialist_count"],
                payload["paired_prompts"],
                pct(result["specialist_rate"]),
                result["parent_count"],
                payload["paired_prompts"],
                pct(result["parent_rate"]),
                pp(result["difference"]),
                pp(low),
                pp(high),
                result["specialist_wins"],
                result["parent_wins"],
                result["ties"],
                result["cluster_sign_flip_p"],
                result["holm_p_across_seven_endpoints"],
            )
        )
    lines.extend(
        [
            "",
            "The exact parent has the higher reference-signature point estimate. The paired cluster interval and sign-flip test determine whether that release-bound difference is distinguishable from zero. Because the specialist and parent were served through different provider routes, the result does not isolate the fine-tuning intervention from every serving-stack difference.",
            "",
        ]
    )
    output_prefix.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the Qiskit-specialized checkpoint with its exact Mistral parent."
    )
    parser.add_argument("--specialist-report", type=Path, default=DEFAULT_SPECIALIST)
    parser.add_argument("--parent-report", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--specialist-requests", type=Path, default=DEFAULT_SPECIALIST_REQUESTS)
    parser.add_argument("--parent-requests", type=Path, default=DEFAULT_PARENT_REQUESTS)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-samples", type=int, default=20_000)
    parser.add_argument("--permutation-samples", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260714)
    args = parser.parse_args()
    payload = run(args)
    write_outputs(payload, args.output_prefix)
    print(f"Wrote {args.output_prefix.with_suffix('.md')}")
    print(f"Wrote {args.output_prefix.with_suffix('.json')}")
    print(f"Wrote {args.output_prefix.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
