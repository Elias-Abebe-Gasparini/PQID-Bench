"""Freeze the prospective 154-prompt PQID-Bench generation split.

The original 70 prompts remain the pilot cohort.  This script moves 84
singleton source-file groups from the original training partition into an
extension cohort using only source metadata.  Selection is deterministic,
stratified by clean view and gate-type diversity, and excludes evaluator-facing
target signatures already represented in the pilot or selected extension.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import run_pqid_bench_external_model_generation_harness as harness
import run_pqid_bench_generation_copy_baseline as copy_baseline
import run_pqid_bench_retrieval_baseline as retrieval


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
DEFAULT_INPUT = retrieval.DEFAULT_INPUT
DEFAULT_PILOT_PROMPTS = ARTIFACTS_DIR / "pqid_bench_external_generation_prompts.jsonl"
DEFAULT_OUTPUT_DIR = ARTIFACTS_DIR / "test_split_154"

SCHEMA_VERSION = "pqid-bench-expanded-split-v1"
SPLIT_ID = "pqid-bench-clean-generation-154-v1"
SELECTION_NAMESPACE = "pqid-bench-test-154-v1"
TARGET_TEST_SIZE = 154
TARGET_LABEL_COUNTS = {"strict_n8": 77, "extended_n8": 77}
TARGET_GATE_BIN_COUNTS = {"1-2": 42, "3-4": 85, "5+": 27}
LABEL_ORDER = ["strict_n8", "extended_n8"]
GATE_BIN_ORDER = ["1-2", "3-4", "5+"]


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


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def gate_type_bin(row: dict[str, Any]) -> str:
    count = len(row["metadata"].get("gate_types") or {})
    if count <= 2:
        return "1-2"
    if count <= 4:
        return "3-4"
    return "5+"


def target_signature(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row["metadata"]
    return {
        "num_qubits": metadata.get("num_qubits"),
        "num_clbits": metadata.get("num_clbits"),
        "gate_count": metadata.get("gate_count"),
        "gate_types": dict(sorted((metadata.get("gate_types") or {}).items())),
    }


def signature_key(row: dict[str, Any]) -> str:
    return stable_json(target_signature(row))


def joint_target_counts(rows: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Find the integer joint allocation closest to each view's pool profile."""

    source = Counter((row["label"], gate_type_bin(row)) for row in rows)
    expected: dict[tuple[str, str], float] = {}
    for label in LABEL_ORDER:
        denominator = sum(source[(label, gate_bin)] for gate_bin in GATE_BIN_ORDER)
        for gate_bin in GATE_BIN_ORDER:
            expected[(label, gate_bin)] = (
                TARGET_LABEL_COUNTS[label] * source[(label, gate_bin)] / denominator
            )

    best: tuple[float, tuple[int, int, int]] | None = None
    for strict_12 in range(TARGET_GATE_BIN_COUNTS["1-2"] + 1):
        for strict_34 in range(TARGET_GATE_BIN_COUNTS["3-4"] + 1):
            strict_5 = TARGET_LABEL_COUNTS["strict_n8"] - strict_12 - strict_34
            if strict_5 < 0 or strict_5 > TARGET_GATE_BIN_COUNTS["5+"]:
                continue
            strict_counts = (strict_12, strict_34, strict_5)
            extended_counts = tuple(
                TARGET_GATE_BIN_COUNTS[gate_bin] - value
                for gate_bin, value in zip(GATE_BIN_ORDER, strict_counts, strict=True)
            )
            if min(extended_counts) < 0 or sum(extended_counts) != TARGET_LABEL_COUNTS["extended_n8"]:
                continue
            objective = 0.0
            for gate_bin, value in zip(GATE_BIN_ORDER, strict_counts, strict=True):
                objective += (value - expected[("strict_n8", gate_bin)]) ** 2
            for gate_bin, value in zip(GATE_BIN_ORDER, extended_counts, strict=True):
                objective += (value - expected[("extended_n8", gate_bin)]) ** 2
            candidate = (objective, strict_counts)
            if best is None or candidate < best:
                best = candidate

    if best is None:
        raise RuntimeError("No feasible joint label/gate-bin allocation")

    strict_counts = best[1]
    extended_counts = tuple(
        TARGET_GATE_BIN_COUNTS[gate_bin] - value
        for gate_bin, value in zip(GATE_BIN_ORDER, strict_counts, strict=True)
    )
    return {
        **{("strict_n8", gate_bin): value for gate_bin, value in zip(GATE_BIN_ORDER, strict_counts, strict=True)},
        **{
            ("extended_n8", gate_bin): value
            for gate_bin, value in zip(GATE_BIN_ORDER, extended_counts, strict=True)
        },
    }


def select_extension(
    rows: list[dict[str, Any]],
    original_splits: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], int], dict[tuple[str, str], int]]:
    final_joint = joint_target_counts(rows)
    pilot_joint = Counter(
        (row["label"], gate_type_bin(row)) for row in original_splits["test"]
    )
    extension_quota = {
        key: final_joint[key] - pilot_joint[key]
        for key in final_joint
    }
    if any(value < 0 for value in extension_quota.values()):
        raise RuntimeError(f"Pilot exceeds a final stratum target: {extension_quota}")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in original_splits["train"]:
        groups[row["_group_id"]].append(row)

    pilot_signatures = {signature_key(row) for row in original_splits["test"]}
    candidates = [
        group_rows[0]
        for group_rows in groups.values()
        if len(group_rows) == 1 and signature_key(group_rows[0]) not in pilot_signatures
    ]

    selected: list[dict[str, Any]] = []
    used_signatures = set(pilot_signatures)
    for label in LABEL_ORDER:
        for gate_bin in GATE_BIN_ORDER:
            quota = extension_quota[(label, gate_bin)]
            stratum = [
                row
                for row in candidates
                if row["label"] == label and gate_type_bin(row) == gate_bin
            ]
            ordered = sorted(
                stratum,
                key=lambda row: copy_baseline.stable_int(
                    f"{SELECTION_NAMESPACE}:{row['_group_id']}:{row['row_id']}"
                ),
            )
            chosen = []
            for row in ordered:
                signature = signature_key(row)
                if signature in used_signatures:
                    continue
                chosen.append(row)
                used_signatures.add(signature)
                if len(chosen) == quota:
                    break
            if len(chosen) != quota:
                raise RuntimeError(
                    f"Insufficient unique candidates for {(label, gate_bin)}: "
                    f"needed {quota}, found {len(chosen)}"
                )
            selected.extend(chosen)

    if len(selected) != TARGET_TEST_SIZE - len(original_splits["test"]):
        raise RuntimeError(f"Expected 84 extension rows, selected {len(selected)}")
    selected.sort(
        key=lambda row: copy_baseline.stable_int(
            f"{SELECTION_NAMESPACE}:prompt-order:{row['row_id']}"
        )
    )
    return selected, final_joint, extension_quota


def expanded_splits(
    rows: list[dict[str, Any]],
    original_splits: dict[str, list[dict[str, Any]]],
    extension_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    extension_ids = {row["row_id"] for row in extension_rows}
    final = {
        "train": [row for row in original_splits["train"] if row["row_id"] not in extension_ids],
        "validation": list(original_splits["validation"]),
        "test": list(original_splits["test"]) + list(extension_rows),
    }
    assigned = [row["row_id"] for split_rows in final.values() for row in split_rows]
    if len(assigned) != len(rows) or len(set(assigned)) != len(rows):
        raise RuntimeError("Expanded split does not assign each clean row exactly once")
    return final


def split_counts(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    output = {}
    for split, split_rows in splits.items():
        output[split] = {
            "rows": len(split_rows),
            "groups": len({row["_group_id"] for row in split_rows}),
            "labels": dict(Counter(row["label"] for row in split_rows)),
            "gate_type_bins": dict(Counter(gate_type_bin(row) for row in split_rows)),
            "unique_target_signatures": len({signature_key(row) for row in split_rows}),
        }
    return output


def validate_group_separation(splits: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    groups = {name: {row["_group_id"] for row in values} for name, values in splits.items()}
    overlaps = {
        "train_validation": len(groups["train"] & groups["validation"]),
        "train_test": len(groups["train"] & groups["test"]),
        "validation_test": len(groups["validation"] & groups["test"]),
    }
    if any(overlaps.values()):
        raise RuntimeError(f"Source-group leakage detected: {overlaps}")
    return overlaps


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_selection_tsv(path: Path, extension_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "prompt_id",
                "row_id",
                "label",
                "gate_type_bin",
                "group_id",
                "signature_sha256",
                "instruction",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        for index, row in enumerate(extension_rows, start=71):
            writer.writerow(
                {
                    "prompt_id": f"pqid_bench_external_gen_{index:04d}",
                    "row_id": row["row_id"],
                    "label": row["label"],
                    "gate_type_bin": gate_type_bin(row),
                    "group_id": row["_group_id"],
                    "signature_sha256": sha256_text(signature_key(row)),
                    "instruction": row["query"].replace("\t", " ").replace("\n", " "),
                }
            )


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    counts = manifest["split_counts"]
    lines = [
        "# PQID-Bench Frozen 154-Prompt Split",
        "",
        f"- split ID: `{manifest['split_id']}`",
        f"- frozen at UTC: `{manifest['created_at_utc']}`",
        f"- pilot prompts retained unchanged: `{manifest['pilot_prompt_count']}`",
        f"- prospectively selected extension prompts: `{manifest['extension_prompt_count']}`",
        f"- final held-out prompts: `{manifest['test_prompt_count']}`",
        f"- unique final target signatures: `{counts['test']['unique_target_signatures']}`",
        "- model outcomes were not used to select extension rows",
        "",
        "## Allocation",
        "",
        "| split | rows | groups | strict clean | extended clean | 1-2 gate types | 3-4 gate types | 5+ gate types | unique signatures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in ["train", "validation", "test"]:
        row = counts[split]
        lines.append(
            f"| {split} | {row['rows']} | {row['groups']} | "
            f"{row['labels'].get('strict_n8', 0)} | {row['labels'].get('extended_n8', 0)} | "
            f"{row['gate_type_bins'].get('1-2', 0)} | {row['gate_type_bins'].get('3-4', 0)} | "
            f"{row['gate_type_bins'].get('5+', 0)} | {row['unique_target_signatures']} |"
        )
    lines.extend(
        [
            "",
            "## Selection Contract",
            "",
            "The original 70-prompt order and identifiers are preserved. The extension moves entire singleton source-file groups from the original training split, excludes target signatures already present in the pilot, and admits at most one row per evaluator-facing signature. The final test set is balanced 77/77 across strict and extended clean views. Its 42/85/27 gate-diversity allocation is the largest-remainder projection of the complete 734-row clean pool. The joint view-by-diversity allocation is the integer solution with the smallest squared deviation from each clean view's source-pool composition under those fixed margins.",
            "",
            "The split leaves 514 training rows (70.03% of the clean pool), keeps the existing 66-row validation partition unchanged, and contains no source-file group overlap between train, validation, and test.",
            "",
            "## Frozen Artifacts",
            "",
            f"- split manifest: `{manifest['artifacts']['split_manifest']}`",
            f"- complete prompt manifest: `{manifest['artifacts']['prompts_154']}`",
            f"- extension-only prompt manifest: `{manifest['artifacts']['prompts_extension_84']}`",
            f"- extension selection audit: `{manifest['artifacts']['selection_tsv']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(input_path: Path, pilot_prompt_path: Path, output_dir: Path) -> None:
    rows = copy_baseline.clean_rows(input_path)
    if len(rows) != 734:
        raise RuntimeError(f"Expected 734 clean rows, found {len(rows)}")
    original_splits = copy_baseline.split_rows(rows)
    pilot_prompts = harness.iter_jsonl(pilot_prompt_path)
    pilot_ids = [row["row_id"] for row in pilot_prompts]
    original_test_ids = [row["row_id"] for row in original_splits["test"]]
    if pilot_ids != original_test_ids:
        raise RuntimeError("The frozen pilot prompt order differs from the deterministic 70-row split")

    extension_rows, final_joint, extension_quota = select_extension(rows, original_splits)
    final_splits = expanded_splits(rows, original_splits, extension_rows)
    overlaps = validate_group_separation(final_splits)

    prompt_rows = [
        harness.prompt_record(row, index)
        for index, row in enumerate(final_splits["test"], start=1)
    ]
    if [stable_json(row) for row in prompt_rows[:70]] != [stable_json(row) for row in pilot_prompts]:
        raise RuntimeError("Regenerated pilot prompt records are not byte-content equivalent")
    extension_prompts = prompt_rows[70:]
    templates = [harness.response_template(prompt) for prompt in prompt_rows]
    extension_templates = templates[70:]

    manifest_path = output_dir / "pqid_bench_split_154_manifest.json"
    report_path = output_dir / "pqid_bench_split_154_manifest.md"
    prompts_path = output_dir / "pqid_bench_external_generation_prompts_154.jsonl"
    extension_path = output_dir / "pqid_bench_external_generation_prompts_extension_84.jsonl"
    templates_path = output_dir / "pqid_bench_external_generation_response_template_154.jsonl"
    extension_templates_path = output_dir / "pqid_bench_external_generation_response_template_extension_84.jsonl"
    selection_path = output_dir / "pqid_bench_extension_84_selection.tsv"

    assignments = []
    pilot_id_set = set(pilot_ids)
    extension_id_set = {row["row_id"] for row in extension_rows}
    split_by_id = {
        row["row_id"]: split
        for split, split_rows in final_splits.items()
        for row in split_rows
    }
    for row in rows:
        cohort = "pilot" if row["row_id"] in pilot_id_set else "extension" if row["row_id"] in extension_id_set else "development"
        assignments.append(
            {
                "row_id": row["row_id"],
                "group_id": row["_group_id"],
                "label": row["label"],
                "gate_type_bin": gate_type_bin(row),
                "target_signature": target_signature(row),
                "target_signature_sha256": sha256_text(signature_key(row)),
                "split": split_by_id[row["row_id"]],
                "cohort": cohort,
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "split_id": SPLIT_ID,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "selection_namespace": SELECTION_NAMESPACE,
        "input": {"path": display_path(input_path), "sha256": sha256_file(input_path), "rows": len(rows)},
        "pilot_prompt_manifest": {
            "path": display_path(pilot_prompt_path),
            "sha256": sha256_file(pilot_prompt_path),
        },
        "selection_policy": {
            "pilot_retained": True,
            "extension_source_split": "original training partition",
            "extension_group_size": 1,
            "selection_uses_model_outcomes": False,
            "exclude_pilot_target_signatures": True,
            "unique_extension_target_signatures": True,
            "target_label_counts": TARGET_LABEL_COUNTS,
            "target_gate_type_bin_counts": TARGET_GATE_BIN_COUNTS,
            "target_joint_counts": {f"{label}|{gate_bin}": count for (label, gate_bin), count in final_joint.items()},
            "extension_joint_quotas": {f"{label}|{gate_bin}": count for (label, gate_bin), count in extension_quota.items()},
        },
        "pilot_prompt_count": 70,
        "extension_prompt_count": len(extension_prompts),
        "test_prompt_count": len(prompt_rows),
        "split_counts": split_counts(final_splits),
        "group_overlap": overlaps,
        "test_prompt_order": [
            {
                "prompt_id": prompt["prompt_id"],
                "row_id": prompt["row_id"],
                "cohort": "pilot" if index <= 70 else "extension",
            }
            for index, prompt in enumerate(prompt_rows, start=1)
        ],
        "assignments": assignments,
        "artifacts": {
            "split_manifest": display_path(manifest_path),
            "split_report": display_path(report_path),
            "prompts_154": display_path(prompts_path),
            "prompts_extension_84": display_path(extension_path),
            "response_template_154": display_path(templates_path),
            "response_template_extension_84": display_path(extension_templates_path),
            "selection_tsv": display_path(selection_path),
        },
    }

    write_jsonl(prompts_path, prompt_rows)
    write_jsonl(extension_path, extension_prompts)
    write_jsonl(templates_path, templates)
    write_jsonl(extension_templates_path, extension_templates)
    write_selection_tsv(selection_path, extension_rows)
    write_json(manifest_path, manifest)
    write_report(report_path, manifest)

    print(f"Wrote {display_path(manifest_path)}")
    print(f"Wrote {display_path(prompts_path)} ({len(prompt_rows)} prompts)")
    print(f"Wrote {display_path(extension_path)} ({len(extension_prompts)} prompts)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--pilot-prompts", type=Path, default=DEFAULT_PILOT_PROMPTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    build(args.input, args.pilot_prompts, args.output_dir)


if __name__ == "__main__":
    main()
