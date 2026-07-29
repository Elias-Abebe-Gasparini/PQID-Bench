"""Freeze the outcome-blind 36-prompt augmentation for the 72-prompt audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from build_pqid_bench_stochastic_repeatability_panel import (
    BIN_ORDER,
    COHORT_ORDER,
    DEFAULT_IDENTIFIABILITY_PATH,
    DEFAULT_PROMPT_PATH,
    cohort,
    display_path,
    gate_type_bin,
    has_barrier,
    iter_jsonl,
    prompt_number,
    reference_signature,
    sha256_file,
    sha256_text,
    stable_json,
    write_json,
    write_jsonl,
)


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE_PANEL_PATH = (
    SUBMISSION_DIR
    / "artifacts"
    / "stochastic_repeatability_21x36"
    / "panel"
    / "pqid_bench_stochastic_repeatability_prompts_36.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x72" / "panel"
)
EXPECTED_BASE_PANEL_SHA256 = (
    "a607d5cd17abb8728acfc857d7bcc6aa122f71945a4f4072808a4c52079dab61"
)
SELECTION_SEED_DERIVATION = (
    "sha256('pqid-bench-stochastic-repeatability-augmentation-v1' + NUL + "
    "base_panel_sha256)"
)
SELECTION_SEED = hashlib.sha256(
    (
        "pqid-bench-stochastic-repeatability-augmentation-v1"
        + "\x00"
        + EXPECTED_BASE_PANEL_SHA256
    ).encode("utf-8")
).hexdigest()
SCHEMA_VERSION = "pqid-bench-stochastic-repeatability-augmentation-v1"


def seeded_rank(*parts: str) -> str:
    value = SELECTION_SEED + "\x00" + "\x00".join(parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def representative_rows(
    prompts: list[dict[str, Any]],
    excluded_ids: set[str],
    excluded_signatures: set[str],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        if str(prompt["prompt_id"]) in excluded_ids:
            continue
        signature_key = stable_json(reference_signature(prompt))
        if signature_key in excluded_signatures:
            continue
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
        signature_members[signature_key] = sorted(
            str(row["prompt_id"]) for row in members
        )
    return representatives, signature_members


def choose_cross_stratum_quotas(
    candidates: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[tuple[str, str], int]:
    """Allocate 12 prompts per gate bin and 18 per cohort as evenly as possible."""

    bins = list(BIN_ORDER)
    feasible: list[tuple[tuple[Any, ...], dict[tuple[str, str], int]]] = []
    for first_pilot in range(13):
        for second_pilot in range(13):
            third_pilot = 18 - first_pilot - second_pilot
            pilot_counts = (first_pilot, second_pilot, third_pilot)
            if not 0 <= third_pilot <= 12:
                continue
            quotas: dict[tuple[str, str], int] = {}
            valid = True
            for gate_bin, pilot_count in zip(bins, pilot_counts, strict=True):
                extension_count = 12 - pilot_count
                quotas[(gate_bin, "pilot")] = pilot_count
                quotas[(gate_bin, "extension")] = extension_count
                if pilot_count > len(candidates[(gate_bin, "pilot")]):
                    valid = False
                if extension_count > len(candidates[(gate_bin, "extension")]):
                    valid = False
            if not valid:
                continue
            deviations = [abs(count - 6) for count in pilot_counts]
            allocation_key = ",".join(str(count) for count in pilot_counts)
            score = (
                max(deviations),
                sum(value * value for value in deviations),
                seeded_rank("allocation", allocation_key),
            )
            feasible.append((score, quotas))

    if not feasible:
        raise ValueError("No feasible augmentation allocation satisfies the frozen margins")
    return min(feasible, key=lambda item: item[0])[1]


def select_stratum(
    rows: list[dict[str, Any]],
    *,
    quota: int,
    base_barriers: int,
    base_total: int,
) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: seeded_rank("panel", str(row["prompt_id"])),
    )
    with_barrier = [row for row in ordered if has_barrier(row)]
    without_barrier = [row for row in ordered if not has_barrier(row)]

    final_total = base_total + quota
    desired_final_barriers = final_total // 2
    desired_new_barriers = min(
        quota,
        max(0, desired_final_barriers - base_barriers),
    )
    selected = (
        with_barrier[:desired_new_barriers]
        + without_barrier[: quota - desired_new_barriers]
    )
    selected_ids = {str(row["prompt_id"]) for row in selected}
    if len(selected) < quota:
        selected.extend(
            row for row in ordered if str(row["prompt_id"]) not in selected_ids
        )
    return selected[:quota]


def selected_record(
    row: dict[str, Any],
    signature_members: dict[str, list[str]],
) -> dict[str, Any]:
    signature = reference_signature(row)
    signature_key = stable_json(signature)
    return {
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


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench Stochastic Repeatability Augmentation",
        "",
        f"- schema: `{manifest['schema_version']}`",
        f"- selection seed: `{manifest['selection_seed']}`",
        f"- seed derivation: `{manifest['selection_seed_derivation']}`",
        f"- original panel prompts: `{manifest['base_prompt_count']}`",
        f"- augmentation prompts: `{manifest['augmentation_prompt_count']}`",
        f"- combined prompts: `{manifest['combined_prompt_count']}`",
        f"- combined unique reference signatures: `{manifest['combined_unique_signature_count']}`",
        f"- augmentation SHA-256: `{manifest['augmentation_panel_sha256']}`",
        f"- combined SHA-256: `{manifest['combined_panel_sha256']}`",
        "",
        "The augmentation was selected without consulting any model outcome. It excludes",
        "the original panel's reference signatures and the four prespecified",
        "prompt-identifiability exceptions. A deterministic seeded allocation adds 12",
        "prompts per gate-diversity band and 18 prompts per benchmark cohort. Cross-stratum",
        "counts are kept as close to six as the remaining unique-signature pool permits,",
        "and barrier representation is balanced against the original panel whenever the",
        "candidate pool permits.",
        "",
        "## Combined Margins",
        "",
        "| margin | count |",
        "| --- | ---: |",
    ]
    for name, count in manifest["combined_balance"]["gate_type_bins"].items():
        lines.append(f"| gate types `{name}` | {count} |")
    for name, count in manifest["combined_balance"]["cohorts"].items():
        lines.append(f"| cohort `{name}` | {count} |")
    lines.extend(
        [
            "",
            "## Augmentation Strata",
            "",
            "| gate-type bin | cohort | available | selected | barrier | no barrier |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in manifest["augmentation_strata"]:
        lines.append(
            f"| `{row['gate_type_bin']}` | `{row['cohort']}` | "
            f"{row['candidate_unique_signatures']} | {row['selected']} | "
            f"{row['barrier']} | {row['no_barrier']} |"
        )
    lines.extend(
        [
            "",
            "## Added Prompts",
            "",
            "| prompt | cohort | gate-type bin | barrier | signature SHA-256 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in manifest["selected_prompts"]:
        lines.append(
            f"| `{row['prompt_id']}` | `{row['cohort']}` | `{row['gate_type_bin']}` | "
            f"{'yes' if row['has_barrier'] else 'no'} | "
            f"`{row['reference_signature_sha256']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_extension(
    prompt_path: Path,
    identifiability_path: Path,
    base_panel_path: Path,
    output_dir: Path,
) -> None:
    observed_base_hash = sha256_file(base_panel_path)
    if observed_base_hash != EXPECTED_BASE_PANEL_SHA256:
        raise ValueError(
            "Original repeatability panel changed: "
            f"expected {EXPECTED_BASE_PANEL_SHA256}, found {observed_base_hash}"
        )

    prompts = iter_jsonl(prompt_path)
    base_rows = iter_jsonl(base_panel_path)
    identifiability = json.loads(identifiability_path.read_text(encoding="utf-8"))
    excluded_ids = {
        str(row["prompt_id"]) for row in identifiability.get("exceptions", [])
    }
    base_signatures = {
        stable_json(reference_signature(row)) for row in base_rows
    }
    if len(base_rows) != 36 or len(base_signatures) != 36:
        raise ValueError("The frozen base panel must contain 36 unique signatures")

    representatives, signature_members = representative_rows(
        prompts,
        excluded_ids,
        base_signatures,
    )
    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for prompt in representatives:
        strata[(gate_type_bin(prompt), cohort(prompt))].append(prompt)

    quotas = choose_cross_stratum_quotas(strata)
    selected: list[dict[str, Any]] = []
    augmentation_strata: list[dict[str, Any]] = []
    for gate_bin in BIN_ORDER:
        for cohort_name in COHORT_ORDER:
            base_subset = [
                row
                for row in base_rows
                if gate_type_bin(row) == gate_bin and cohort(row) == cohort_name
            ]
            quota = quotas[(gate_bin, cohort_name)]
            subset = select_stratum(
                strata[(gate_bin, cohort_name)],
                quota=quota,
                base_barriers=sum(has_barrier(row) for row in base_subset),
                base_total=len(base_subset),
            )
            if len(subset) != quota:
                raise ValueError(f"Could not fill augmentation stratum {(gate_bin, cohort_name)}")
            selected.extend(subset)
            augmentation_strata.append(
                {
                    "gate_type_bin": gate_bin,
                    "cohort": cohort_name,
                    "candidate_unique_signatures": len(strata[(gate_bin, cohort_name)]),
                    "selected": len(subset),
                    "barrier": sum(has_barrier(row) for row in subset),
                    "no_barrier": sum(not has_barrier(row) for row in subset),
                }
            )

    selected.sort(key=lambda row: prompt_number(str(row["prompt_id"])))
    combined = sorted(
        [*base_rows, *selected],
        key=lambda row: prompt_number(str(row["prompt_id"])),
    )
    selected_ids = [str(row["prompt_id"]) for row in selected]
    combined_ids = [str(row["prompt_id"]) for row in combined]
    selected_signatures = [stable_json(reference_signature(row)) for row in selected]
    combined_signatures = [stable_json(reference_signature(row)) for row in combined]

    if len(selected) != 36 or len(set(selected_ids)) != 36:
        raise AssertionError("The augmentation must contain 36 unique prompts")
    if len(set(selected_signatures)) != 36:
        raise AssertionError("The augmentation must contain 36 unique signatures")
    if base_signatures.intersection(selected_signatures):
        raise AssertionError("An original-panel signature entered the augmentation")
    if excluded_ids.intersection(selected_ids):
        raise AssertionError("An identifiability exception entered the augmentation")
    if len(combined) != 72 or len(set(combined_ids)) != 72:
        raise AssertionError("The combined panel must contain 72 unique prompts")
    if len(set(combined_signatures)) != 72:
        raise AssertionError("The combined panel must contain 72 unique signatures")

    selected_bin_counts = Counter(gate_type_bin(row) for row in selected)
    selected_cohort_counts = Counter(cohort(row) for row in selected)
    combined_bin_counts = Counter(gate_type_bin(row) for row in combined)
    combined_cohort_counts = Counter(cohort(row) for row in combined)
    if selected_bin_counts != Counter({"1-2": 12, "3-4": 12, "5+": 12}):
        raise AssertionError(f"Unexpected augmentation gate balance: {selected_bin_counts}")
    if selected_cohort_counts != Counter({"pilot": 18, "extension": 18}):
        raise AssertionError(f"Unexpected augmentation cohort balance: {selected_cohort_counts}")
    if combined_bin_counts != Counter({"1-2": 24, "3-4": 24, "5+": 24}):
        raise AssertionError(f"Unexpected combined gate balance: {combined_bin_counts}")
    if combined_cohort_counts != Counter({"pilot": 36, "extension": 36}):
        raise AssertionError(f"Unexpected combined cohort balance: {combined_cohort_counts}")

    output_dir.mkdir(parents=True, exist_ok=True)
    augmentation_path = output_dir / "pqid_bench_stochastic_repeatability_augmentation_prompts_36.jsonl"
    combined_path = output_dir / "pqid_bench_stochastic_repeatability_prompts_72.jsonl"
    write_jsonl(augmentation_path, selected)
    write_jsonl(combined_path, combined)

    selected_records = [
        selected_record(row, signature_members) for row in selected
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "selection_seed": SELECTION_SEED,
        "selection_seed_derivation": SELECTION_SEED_DERIVATION,
        "selection_is_outcome_blind": True,
        "selection_used_model_outcomes": False,
        "source_prompt_file": display_path(prompt_path),
        "source_prompt_sha256": sha256_file(prompt_path),
        "identifiability_audit_file": display_path(identifiability_path),
        "identifiability_audit_sha256": sha256_file(identifiability_path),
        "excluded_prompt_ids": sorted(excluded_ids),
        "base_panel_file": display_path(base_panel_path),
        "base_panel_sha256": observed_base_hash,
        "base_prompt_count": len(base_rows),
        "augmentation_panel_file": display_path(augmentation_path),
        "augmentation_panel_sha256": sha256_file(augmentation_path),
        "augmentation_prompt_count": len(selected),
        "combined_panel_file": display_path(combined_path),
        "combined_panel_sha256": sha256_file(combined_path),
        "combined_prompt_count": len(combined),
        "combined_unique_signature_count": len(set(combined_signatures)),
        "eligible_remaining_unique_signature_count": len(representatives),
        "augmentation_balance": {
            "gate_type_bins": dict(
                sorted(selected_bin_counts.items(), key=lambda item: BIN_ORDER[item[0]])
            ),
            "cohorts": dict(
                sorted(selected_cohort_counts.items(), key=lambda item: COHORT_ORDER[item[0]])
            ),
            "barrier": sum(has_barrier(row) for row in selected),
            "no_barrier": sum(not has_barrier(row) for row in selected),
        },
        "combined_balance": {
            "gate_type_bins": dict(
                sorted(combined_bin_counts.items(), key=lambda item: BIN_ORDER[item[0]])
            ),
            "cohorts": dict(
                sorted(combined_cohort_counts.items(), key=lambda item: COHORT_ORDER[item[0]])
            ),
            "barrier": sum(has_barrier(row) for row in combined),
            "no_barrier": sum(not has_barrier(row) for row in combined),
        },
        "augmentation_strata": augmentation_strata,
        "selected_prompts": selected_records,
    }
    manifest_path = output_dir / "pqid_bench_stochastic_repeatability_augmentation_manifest.json"
    report_path = output_dir / "pqid_bench_stochastic_repeatability_augmentation_manifest.md"
    write_json(manifest_path, manifest)
    write_markdown(report_path, manifest)

    print(f"Wrote {augmentation_path}")
    print(f"Wrote {combined_path}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-path", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument(
        "--identifiability-path", type=Path, default=DEFAULT_IDENTIFIABILITY_PATH
    )
    parser.add_argument("--base-panel-path", type=Path, default=DEFAULT_BASE_PANEL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    build_extension(
        args.prompt_path,
        args.identifiability_path,
        args.base_panel_path,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
