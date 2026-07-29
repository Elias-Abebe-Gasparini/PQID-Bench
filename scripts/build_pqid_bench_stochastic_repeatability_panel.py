"""Freeze the deterministic prompt panel for the PQID-Bench repeatability audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_PATH = (
    SUBMISSION_DIR
    / "artifacts"
    / "test_split_154"
    / "pqid_bench_external_generation_prompts_154.jsonl"
)
DEFAULT_IDENTIFIABILITY_PATH = (
    SUBMISSION_DIR
    / "artifacts"
    / "analysis_154"
    / "pqid_bench_prompt_identifiability_sensitivity.json"
)
DEFAULT_OUTPUT_DIR = (
    SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x36" / "panel"
)
SCHEMA_VERSION = "pqid-bench-stochastic-repeatability-panel-v1"
SELECTION_SEED = "pqid-bench-stochastic-repeatability-v1-20260715"
BIN_ORDER = {"1-2": 0, "3-4": 1, "5+": 2}
COHORT_ORDER = {"pilot": 0, "extension": 1}


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prompt_number(prompt_id: str) -> int:
    return int(prompt_id.rsplit("_", 1)[-1])


def reference_signature(prompt: dict[str, Any]) -> dict[str, Any]:
    target = prompt["target_metadata"]
    return {
        "num_qubits": int(target["num_qubits"]),
        "num_clbits": int(target["num_clbits"]),
        "gate_count": int(target["gate_count"]),
        "gate_types": {
            str(name): int(count)
            for name, count in sorted((target.get("gate_types") or {}).items())
        },
    }


def gate_type_bin(prompt: dict[str, Any]) -> str:
    count = len((prompt["target_metadata"].get("gate_types") or {}))
    if count <= 2:
        return "1-2"
    if count <= 4:
        return "3-4"
    return "5+"


def cohort(prompt: dict[str, Any]) -> str:
    return "pilot" if prompt_number(str(prompt["prompt_id"])) <= 70 else "extension"


def has_barrier(prompt: dict[str, Any]) -> bool:
    gates = prompt["target_metadata"].get("gate_types") or {}
    return int(gates.get("barrier", 0)) > 0


def seeded_rank(*parts: str) -> str:
    return sha256_text(SELECTION_SEED + "\x00" + "\x00".join(parts))


def representative_rows(
    prompts: list[dict[str, Any]], excluded_ids: set[str]
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        if str(prompt["prompt_id"]) in excluded_ids:
            continue
        signature_key = stable_json(reference_signature(prompt))
        grouped[signature_key].append(prompt)

    representatives: list[dict[str, Any]] = []
    signature_members: dict[str, list[str]] = {}
    for signature_key, members in grouped.items():
        ranked = sorted(
            members,
            key=lambda row: seeded_rank(
                "representative", signature_key, str(row["prompt_id"])
            ),
        )
        representatives.append(ranked[0])
        signature_members[signature_key] = sorted(str(row["prompt_id"]) for row in members)
    return representatives, signature_members


def select_stratum(rows: list[dict[str, Any]], *, quota: int = 6) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: seeded_rank("panel", str(row["prompt_id"])),
    )
    with_barrier = [row for row in ordered if has_barrier(row)]
    without_barrier = [row for row in ordered if not has_barrier(row)]
    selected = with_barrier[: quota // 2] + without_barrier[: quota // 2]
    selected_ids = {str(row["prompt_id"]) for row in selected}
    if len(selected) < quota:
        selected.extend(
            row for row in ordered if str(row["prompt_id"]) not in selected_ids
        )
    return selected[:quota]


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench Stochastic Repeatability Panel",
        "",
        f"- schema: `{manifest['schema_version']}`",
        f"- selection seed: `{manifest['selection_seed']}`",
        f"- prompts: `{manifest['prompt_count']}`",
        f"- unique reference signatures: `{manifest['unique_signature_count']}`",
        f"- excluded prompt-identifiability exceptions: `{len(manifest['excluded_prompt_ids'])}`",
        f"- panel SHA-256: `{manifest['panel_sha256']}`",
        "",
        "The panel was selected without consulting any model outcome. Four prespecified",
        "prompt-identifiability exceptions were removed, duplicate evaluator-facing",
        "reference signatures were collapsed by seeded rank, and six prompts were",
        "selected from each gate-diversity-by-cohort stratum. Within each stratum the",
        "selection targets three barrier/staged and three non-barrier prompts whenever",
        "the candidate pool permits that split.",
        "",
        "## Strata",
        "",
        "| gate-type bin | cohort | barrier | no barrier | total |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in manifest["strata"]:
        lines.append(
            f"| `{row['gate_type_bin']}` | `{row['cohort']}` | "
            f"{row['barrier']} | {row['no_barrier']} | {row['total']} |"
        )
    lines.extend(
        [
            "",
            "## Selected Prompts",
            "",
            "| prompt | cohort | gate-type bin | barrier | signature SHA-256 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in manifest["selected_prompts"]:
        lines.append(
            f"| `{row['prompt_id']}` | `{row['cohort']}` | `{row['gate_type_bin']}` | "
            f"{'yes' if row['has_barrier'] else 'no'} | `{row['reference_signature_sha256']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_panel(prompt_path: Path, identifiability_path: Path, output_dir: Path) -> None:
    prompts = iter_jsonl(prompt_path)
    identifiability = json.loads(identifiability_path.read_text(encoding="utf-8"))
    excluded_ids = {
        str(row["prompt_id"]) for row in identifiability.get("exceptions", [])
    }
    representatives, signature_members = representative_rows(prompts, excluded_ids)

    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for prompt in representatives:
        strata[(gate_type_bin(prompt), cohort(prompt))].append(prompt)

    selected: list[dict[str, Any]] = []
    for gate_bin in BIN_ORDER:
        for cohort_name in COHORT_ORDER:
            candidates = strata[(gate_bin, cohort_name)]
            if len(candidates) < 6:
                raise ValueError(
                    f"Stratum {(gate_bin, cohort_name)} has only {len(candidates)} unique signatures"
                )
            selected.extend(select_stratum(candidates, quota=6))
    selected.sort(key=lambda row: prompt_number(str(row["prompt_id"])))

    selected_ids = [str(row["prompt_id"]) for row in selected]
    signatures = [stable_json(reference_signature(row)) for row in selected]
    if len(selected) != 36 or len(set(selected_ids)) != 36 or len(set(signatures)) != 36:
        raise AssertionError("The repeatability panel must contain 36 unique prompts and signatures")
    if excluded_ids.intersection(selected_ids):
        raise AssertionError("An identifiability exception entered the repeatability panel")

    bin_counts = Counter(gate_type_bin(row) for row in selected)
    cohort_counts = Counter(cohort(row) for row in selected)
    if bin_counts != Counter({"1-2": 12, "3-4": 12, "5+": 12}):
        raise AssertionError(f"Unexpected gate-diversity balance: {bin_counts}")
    if cohort_counts != Counter({"pilot": 18, "extension": 18}):
        raise AssertionError(f"Unexpected cohort balance: {cohort_counts}")

    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = output_dir / "pqid_bench_stochastic_repeatability_prompts_36.jsonl"
    write_jsonl(panel_path, selected)

    strata_rows: list[dict[str, Any]] = []
    for gate_bin in BIN_ORDER:
        for cohort_name in COHORT_ORDER:
            subset = [
                row
                for row in selected
                if gate_type_bin(row) == gate_bin and cohort(row) == cohort_name
            ]
            barrier_count = sum(has_barrier(row) for row in subset)
            strata_rows.append(
                {
                    "gate_type_bin": gate_bin,
                    "cohort": cohort_name,
                    "barrier": barrier_count,
                    "no_barrier": len(subset) - barrier_count,
                    "total": len(subset),
                    "candidate_unique_signatures": len(strata[(gate_bin, cohort_name)]),
                }
            )

    selected_records: list[dict[str, Any]] = []
    for row in selected:
        signature = reference_signature(row)
        signature_key = stable_json(signature)
        selected_records.append(
            {
                "prompt_id": row["prompt_id"],
                "row_id": row["row_id"],
                "label": row.get("label"),
                "cohort": cohort(row),
                "gate_type_bin": gate_type_bin(row),
                "gate_type_count": len(signature["gate_types"]),
                "has_barrier": has_barrier(row),
                "reference_signature": signature,
                "reference_signature_sha256": sha256_text(signature_key),
                "collapsed_signature_members": signature_members[signature_key],
                "selection_rank_sha256": seeded_rank("panel", str(row["prompt_id"])),
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "selection_seed": SELECTION_SEED,
        "selection_is_outcome_blind": True,
        "source_prompt_file": display_path(prompt_path),
        "source_prompt_sha256": sha256_file(prompt_path),
        "identifiability_audit_file": display_path(identifiability_path),
        "identifiability_audit_sha256": sha256_file(identifiability_path),
        "excluded_prompt_ids": sorted(excluded_ids),
        "eligible_prompt_count": len(prompts) - len(excluded_ids),
        "eligible_unique_signature_count": len(representatives),
        "prompt_count": len(selected),
        "unique_signature_count": len(set(signatures)),
        "panel_file": display_path(panel_path),
        "panel_sha256": sha256_file(panel_path),
        "balance": {
            "gate_type_bins": dict(sorted(bin_counts.items(), key=lambda item: BIN_ORDER[item[0]])),
            "cohorts": dict(sorted(cohort_counts.items(), key=lambda item: COHORT_ORDER[item[0]])),
            "barrier": sum(has_barrier(row) for row in selected),
            "no_barrier": sum(not has_barrier(row) for row in selected),
        },
        "strata": strata_rows,
        "selected_prompts": selected_records,
    }
    manifest_path = output_dir / "pqid_bench_stochastic_repeatability_panel.json"
    report_path = output_dir / "pqid_bench_stochastic_repeatability_panel.md"
    write_json(manifest_path, manifest)
    write_markdown(report_path, manifest)
    print(f"Wrote {display_path(panel_path)}")
    print(f"Wrote {display_path(manifest_path)}")
    print(f"Wrote {display_path(report_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-path", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument(
        "--identifiability-path", type=Path, default=DEFAULT_IDENTIFIABILITY_PATH
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    build_panel(args.prompt_path, args.identifiability_path, args.output_dir)


if __name__ == "__main__":
    main()
