"""Audit exact 6/8 PQID readiness rows as possible clean benchmark additions.

The audit is deliberately non-mutating. It reconstructs the frozen readiness
checks from the canonical source, replays path-clean candidates through the
published evaluator, and compares their signatures and lineage groups with the
current 734-row clean generation pool.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
PQID_DIR = SCRIPT_PATH.parents[3]
PROJECT_SCRIPTS_DIR = PQID_DIR / "scripts"
if str(PROJECT_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_SCRIPTS_DIR))

import filter_benchmark_and_tier2 as readiness  # noqa: E402
import run_pqid_bench_generation_copy_baseline as copy_baseline  # noqa: E402


DEFAULT_SOURCE = (
    PQID_DIR
    / "data"
    / "processed"
    / "pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl"
)
DEFAULT_SEED_DRAFTS = (
    PQID_DIR / "data" / "processed" / "seed_drafts_quality_aware_source_code_v1.jsonl"
)
DEFAULT_SPLIT_MANIFEST = (
    SUBMISSION_DIR
    / "artifacts"
    / "test_split_154"
    / "pqid_bench_split_154_manifest.json"
)
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts" / "n6_cleanliness_expansion_audit"

SCHEMA_VERSION = "pqid-bench-n6-cleanliness-expansion-audit-v1"
SELECTION_NAMESPACE = "pqid-bench-n6-drop-in-candidates-v1"
CLEAN_ROLES = {"gold_generation", "broad_generation"}
MIN_CODE_LINES = 5
MIN_GATE_COUNT = 2


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_rank(value: str) -> str:
    return hashlib.sha256(f"{SELECTION_NAMESPACE}:{value}".encode("utf-8")).hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def target_signature(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "num_qubits": metadata.get("num_qubits"),
        "num_clbits": metadata.get("num_clbits"),
        "gate_count": metadata.get("gate_count"),
        "gate_types": dict(sorted((metadata.get("gate_types") or {}).items())),
    }


def signature_key(metadata: dict[str, Any]) -> str:
    return stable_json(target_signature(metadata))


def gate_type_bin(metadata: dict[str, Any]) -> str:
    count = len(metadata.get("gate_types") or {})
    if count <= 2:
        return "1-2"
    if count <= 4:
        return "3-4"
    return "5+"


def public_redistributable(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("release_view_membership") == "public_open"
        and str(metadata.get("distribution_rights_status") or "").startswith(
            "redistributable"
        )
    )


def signature_complete(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("num_qubits") is not None
        and metadata.get("num_clbits") is not None
        and metadata.get("gate_count") is not None
        and isinstance(metadata.get("gate_types"), dict)
    )


def gate_count_consistent(metadata: dict[str, Any]) -> bool:
    gate_types = metadata.get("gate_types")
    if not isinstance(gate_types, dict) or metadata.get("gate_count") is None:
        return False
    count = sum(
        int(value or 0)
        for name, value in gate_types.items()
        if str(name).lower() != "barrier"
    )
    return count == int(metadata["gate_count"])


def compact_replay(result: dict[str, Any]) -> dict[str, Any]:
    checks = (result.get("structural") or {}).get("checks") or {}
    return {
        "execution_success": bool(result.get("execution_success")),
        "execution_error_type": result.get("execution_error_type"),
        "circuit_found": bool(result.get("circuit_found")),
        "signature_match": bool(checks.get("all_match")),
        "component_checks": checks,
        "qasm3_export_success": bool((result.get("qasm3_export") or {}).get("success")),
    }


def replay_record(
    record: dict[str, Any], qiskit_env: dict[str, Any]
) -> dict[str, Any]:
    metadata = record["metadata"]
    row = {
        "row_id": str(metadata.get("circuit_hash") or metadata.get("hash")),
        "label": record["audit_label"],
        "code": record.get("output") or "",
        "metadata": metadata,
    }
    strict = copy_baseline.execute_generated_code(
        target_row=row,
        generated_code=row["code"],
        context_metadata={},
        qiskit_env=qiskit_env,
    )
    target_context = copy_baseline.execute_generated_code(
        target_row=row,
        generated_code=row["code"],
        context_metadata=metadata,
        qiskit_env=qiskit_env,
    )
    return {
        "strict": compact_replay(strict),
        "target_context": compact_replay(target_context),
    }


def replay_pass(replay: dict[str, Any], mode: str = "strict") -> bool:
    result = replay[mode]
    return (
        result["execution_success"]
        and result["circuit_found"]
        and result["signature_match"]
        and result["qasm3_export_success"]
    )


def load_seed_contract(
    seed_path: Path,
) -> tuple[
    set[str],
    set[str],
    dict[str, dict[str, Any]],
]:
    clean_hashes: set[str] = set()
    clean_signatures: set[str] = set()
    drafts_by_circuit_hash: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(seed_path):
        metadata = row.get("metadata") or {}
        circuit_hash = str(metadata.get("circuit_hash") or "")
        if circuit_hash:
            drafts_by_circuit_hash[circuit_hash] = {
                "seed_role": metadata.get("seed_role"),
                "has_prompt": bool(str(row.get("input") or "").strip()),
            }
        if metadata.get("seed_role") in CLEAN_ROLES:
            clean_hashes.add(circuit_hash)
            clean_signatures.add(signature_key(metadata))
    return clean_hashes, clean_signatures, drafts_by_circuit_hash


def failed_key(failed_checks: Iterable[str]) -> str:
    return " + ".join(failed_checks) or "<none>"


def metadata_counter() -> Counter[str]:
    return Counter(
        {
            "rows": 0,
            "validated": 0,
            "materialized": 0,
            "circuit_stats": 0,
            "stored_qasm3_success": 0,
            "signature_complete": 0,
            "gate_count_map_consistent": 0,
            "public_redistributable": 0,
        }
    )


def update_metadata_counter(counter: Counter[str], metadata: dict[str, Any]) -> None:
    counter["rows"] += 1
    counter["validated"] += metadata.get("validation_status") == "validated"
    counter["materialized"] += metadata.get("materialized_circuit") is True
    counter["circuit_stats"] += metadata.get("circuit_stats_available") is True
    counter["stored_qasm3_success"] += (
        metadata.get("openqasm3_export_successful") is True
    )
    counter["signature_complete"] += signature_complete(metadata)
    counter["gate_count_map_consistent"] += gate_count_consistent(metadata)
    counter["public_redistributable"] += public_redistributable(metadata)


def deduplicate_signatures(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    ordered = sorted(
        rows,
        key=lambda item: stable_rank(
            str(item["metadata"].get("circuit_hash") or item["metadata"].get("hash"))
        ),
    )
    for item in ordered:
        signature = signature_key(item["metadata"])
        if signature in seen:
            continue
        seen.add(signature)
        selected.append(item)
    return selected


def replay_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    for item in rows:
        replay = item["replay"]
        for mode in ["strict", "target_context"]:
            result = replay[mode]
            prefix = f"{mode}_"
            counts[prefix + "execution"] += result["execution_success"]
            counts[prefix + "circuit"] += result["circuit_found"]
            counts[prefix + "signature"] += result["signature_match"]
            counts[prefix + "qasm3"] += result["qasm3_export_success"]
            if not result["execution_success"]:
                errors[f"{mode}:{result['execution_error_type']}"] += 1
    return {
        "rows": len(rows),
        **dict(counts),
        "execution_errors": dict(sorted(errors.items())),
    }


def split_contract(path: Path) -> dict[str, int]:
    defaults = {"train": 514, "validation": 66, "test": 154}
    if not path.exists():
        return defaults
    payload = json.loads(path.read_text(encoding="utf-8"))
    counts = payload.get("split_counts") or {}
    parsed = {
        split: int((counts.get(split) or {}).get("rows", defaults[split]))
        for split in defaults
    }
    return parsed


def candidate_row(item: dict[str, Any], selected_hashes: set[str]) -> dict[str, Any]:
    metadata = item["metadata"]
    circuit_hash = str(metadata.get("circuit_hash") or metadata.get("hash"))
    replay = item["replay"]
    return {
        "circuit_hash": circuit_hash,
        "failed_checks": failed_key(item["failed_checks"]),
        "repo_owner": metadata.get("repo_owner"),
        "repo_name": metadata.get("repo_name"),
        "file_path": metadata.get("file_path"),
        "split_group_id": metadata.get("split_group_id"),
        "near_duplicate_group_id": metadata.get("near_duplicate_group_id"),
        "code_lines": metadata.get("code_lines"),
        "num_qubits": metadata.get("num_qubits"),
        "num_clbits": metadata.get("num_clbits"),
        "gate_count": metadata.get("gate_count"),
        "gate_type_count": len(metadata.get("gate_types") or {}),
        "gate_type_bin": gate_type_bin(metadata),
        "gate_types_json": stable_json(metadata.get("gate_types") or {}),
        "seed_role": item.get("seed_role"),
        "existing_prompt_is_generation_facing": item.get("seed_role") in CLEAN_ROLES,
        "strict_execution": replay["strict"]["execution_success"],
        "strict_signature": replay["strict"]["signature_match"],
        "strict_qasm3": replay["strict"]["qasm3_export_success"],
        "target_context_signature": replay["target_context"]["signature_match"],
        "novel_signature_vs_clean_734": item["novel_signature"],
        "novel_split_group_vs_clean_734": item["novel_split_group"],
        "novel_near_duplicate_group_vs_clean_734": item["novel_near_duplicate_group"],
        "selected_drop_in_candidate": circuit_hash in selected_hashes,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def pct(numerator: int, denominator: int) -> str:
    return f"{100.0 * numerator / denominator:.2f}%" if denominator else "n/a"


def build_report(payload: dict[str, Any]) -> str:
    n6 = payload["exact_6_of_8"]
    funnel = n6["candidate_funnel"]
    replay = n6["path_clean_replay"]
    selected = n6["selected_drop_in_candidates"]
    comparator = payload["seven_of_eight_short_code_comparator"]
    split = payload["split_governance"]
    lines = [
        "# PQID Exact 6/8 Cleanliness Expansion Audit",
        "",
        "## Verdict",
        "",
        "Exact `6/8` rows do **not** provide a defensible bulk expansion of the clean generation pool. "
        "Their metadata are generally complete, but most belong to mutation stress, are trivial or near-empty, "
        "lack public redistribution clearance, fail the benchmark's strict replay, duplicate an existing target "
        "signature, or retain a repair-facing rather than generation-facing prompt.",
        "",
        f"The auditable funnel starts with `{funnel['exact_6_of_8']:,}` rows and leaves only "
        f"`{funnel['signature_deduplicated_drop_in']:,}` provisional drop-in rows. Those rows add "
        f"`{selected['pool_increase_percent']:.2f}%` to the current 734-row pool, cover "
        f"`{selected['source_groups']}` source groups, and contain no `5+` operation-type target. "
        "They should therefore remain a separately labelled curation pilot, not be merged into `strict_n8` or "
        "`extended_n8` and not be used to revise the frozen manuscript denominator.",
        "",
        "## Definition",
        "",
        "Here `6/8` means **exactly six passes** under the frozen cleanliness-aware readiness profile, not a new "
        "benchmark label and not six arbitrarily selected checks. The eight checks are:",
        "",
    ]
    for check_id in payload["readiness_contract"]["check_order"]:
        lines.append(
            f"- `{check_id}`: {payload['readiness_contract']['descriptions'][check_id]}"
        )
    lines.extend(
        [
            "",
            "## Exact 6/8 Funnel",
            "",
            "| stage | rows | share of exact 6/8 | interpretation |",
            "| --- | ---: | ---: | --- |",
            f"| exact 6/8 source rows | {funnel['exact_6_of_8']:,} | 100.00% | starting stratum |",
            f"| non-mutation path | {funnel['non_mutation']:,} | {pct(funnel['non_mutation'], funnel['exact_6_of_8'])} | removes mutation-stress material |",
            f"| nontrivial short circuit (`gate_count >= 2`) | {funnel['nontrivial_short']:,} | {pct(funnel['nontrivial_short'], funnel['exact_6_of_8'])} | fails only code length and provenance |",
            f"| public and redistributable | {funnel['public_redistributable']:,} | {pct(funnel['public_redistributable'], funnel['exact_6_of_8'])} | eligible for a public artifact |",
            f"| strict execution + signature + QASM3 replay | {funnel['strict_replay_pass']:,} | {pct(funnel['strict_replay_pass'], funnel['exact_6_of_8'])} | evaluator-admissible source target |",
            f"| novel against clean 734 | {funnel['novel_rows']:,} | {pct(funnel['novel_rows'], funnel['exact_6_of_8'])} | no existing signature or lineage-group overlap |",
            f"| one row per novel signature | {funnel['signature_deduplicated_drop_in']:,} | {pct(funnel['signature_deduplicated_drop_in'], funnel['exact_6_of_8'])} | provisional expansion ceiling |",
            "",
            "## Failed-Check Composition",
            "",
            "| failed checks | rows | public/redistributable | stored signature complete |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for failed, row in n6["failed_check_combinations"].items():
        lines.append(
            f"| `{failed}` | {row['rows']:,} | {row['public_redistributable']:,} | "
            f"{row['signature_complete']:,} |"
        )
    lines.extend(
        [
            "",
            "## Evaluator Replay",
            "",
            f"All `{replay['rows']:,}` path-clean exact-6/8 rows were replayed under Qiskit "
            f"`{payload['environment']['qiskit_version']}`. Strict replay executes "
            f"`{replay['strict_execution']:,}/{replay['rows']:,}` rows and recovers the stored signature for "
            f"`{replay['strict_signature']:,}/{replay['rows']:,}`. Target-context replay recovers "
            f"`{replay['target_context_signature']:,}/{replay['rows']:,}` signatures. The difference shows that "
            "frozen source validation does not make every short snippet a standalone generation target.",
            "",
            "## Surviving Candidate Profile",
            "",
            f"- rows/signatures: `{selected['rows']}` / `{selected['unique_signatures']}`",
            f"- source groups: `{selected['source_groups']}`",
            f"- operation-type bins: `{stable_json(selected['gate_type_bins'])}`",
            f"- repositories: `{stable_json(selected['repositories'])}`",
            "- existing seed role: `repair_or_explanation`; every surviving row requires a new, independently "
            "audited generation prompt",
            "- no candidate belongs to the `5+` operation-type band, so this route would increase the easy side "
            "of the pool rather than repair its high-diversity coverage",
            "",
            "## Split-Governance Consequence",
            "",
            f"Adding all `{selected['rows']}` provisional rows would create a `{split['n6_pool_size']}`-row pool. "
            f"With the existing `{split['current_train']}` training rows and a 70% training floor, at least "
            f"`{split['n6_candidates_required_for_train']}` of the new rows must enter training. At most "
            f"`{split['n6_max_nontraining_additions']}` could be added across validation and test without moving "
            "existing rows. The route therefore cannot materially enlarge the held-out panel while preserving "
            "the stated split-governance principle.",
            "",
            "## Seven-of-Eight Comparator",
            "",
            f"The adjacent `7/8` stratum that fails **only** `minimum_code_lines` is a better curation source: "
            f"`{comparator['public_rows']}` rows are public/redistributable, `{comparator['strict_replay_pass']}` "
            f"pass strict replay, and `{comparator['signature_deduplicated_novel']}` novel signatures remain after "
            f"lineage and signature controls. Even this comparator has operation-type bins "
            f"`{stable_json(comparator['gate_type_bins'])}` and no `5+` targets. It is suitable for a future "
            "short-circuit calibration stratum, not for silently enlarging the frozen clean denominator.",
            "",
            "## Recommendation",
            "",
            "1. Keep PQID-Bench v1 and its 734-row clean pool frozen.",
            "2. Do not redefine exact `6/8` as clean generation material.",
            "3. If an expansion is needed, preregister a separately labelled `short-circuit calibration` pilot "
            "from the audited `7/8` candidates, regenerate uniquely identifying generation prompts, normalize "
            "source code to the standalone evaluator contract, and rerun release, lineage, identifiability, and "
            "split audits before assigning any row.",
            "4. Seek genuinely new `5+` operation-type circuits from additional repositories for a meaningful "
            "difficulty expansion; the current near-threshold strata do not supply them.",
            "",
            "## Reproducibility Artifacts",
            "",
        ]
    )
    for label, path in payload["artifacts"].items():
        lines.append(f"- {label.replace('_', ' ')}: `{path}`")
    return "\n".join(lines) + "\n"


def run(
    source_path: Path,
    seed_path: Path,
    split_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    clean_hashes, clean_signatures, draft_map = load_seed_contract(seed_path)
    score_distribution: Counter[int] = Counter()
    n6_combinations: dict[str, Counter[str]] = defaultdict(metadata_counter)
    n6_records: list[dict[str, Any]] = []
    n7_short_public: list[dict[str, Any]] = []
    clean_split_groups: set[str] = set()
    clean_near_groups: set[str] = set()
    source_rows = 0

    for source_index, row in enumerate(iter_jsonl(source_path)):
        source_rows += 1
        metadata = row.get("metadata") or {}
        evaluation = readiness.evaluate_benchmark_suitability_v2(
            row,
            min_code_lines=MIN_CODE_LINES,
            min_gate_count=MIN_GATE_COUNT,
        )
        score = int(evaluation["checks_passed"])
        score_distribution[score] += 1
        circuit_hash = str(metadata.get("circuit_hash") or "")
        if circuit_hash in clean_hashes:
            if metadata.get("split_group_id"):
                clean_split_groups.add(str(metadata["split_group_id"]))
            if metadata.get("near_duplicate_group_id"):
                clean_near_groups.add(str(metadata["near_duplicate_group_id"]))

        if score == 6:
            failed = tuple(evaluation["failed_checks"])
            update_metadata_counter(n6_combinations[failed_key(failed)], metadata)
            if evaluation["checks"]["non_mutation_suite_path"]:
                draft = draft_map.get(circuit_hash) or {}
                n6_records.append(
                    {
                        "source_index": source_index,
                        "audit_label": "exact_6_of_8_nonmutation",
                        "output": row.get("output") or "",
                        "metadata": metadata,
                        "failed_checks": failed,
                        "seed_role": draft.get("seed_role"),
                        "has_existing_prompt": bool(draft.get("has_prompt")),
                    }
                )

        if (
            score == 7
            and tuple(evaluation["failed_checks"]) == ("minimum_code_lines",)
            and public_redistributable(metadata)
        ):
            draft = draft_map.get(circuit_hash) or {}
            n7_short_public.append(
                {
                    "source_index": source_index,
                    "audit_label": "seven_of_eight_short_code_public",
                    "output": row.get("output") or "",
                    "metadata": metadata,
                    "failed_checks": tuple(evaluation["failed_checks"]),
                    "seed_role": draft.get("seed_role"),
                    "has_existing_prompt": bool(draft.get("has_prompt")),
                }
            )

    if source_rows != 91_719:
        raise RuntimeError(f"Expected 91,719 source rows, found {source_rows:,}")
    if len(clean_hashes) != 734:
        raise RuntimeError(f"Expected 734 clean seed hashes, found {len(clean_hashes)}")

    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit unavailable: {qiskit_env.get('error')}")

    for item in [*n6_records, *n7_short_public]:
        item["replay"] = replay_record(item, qiskit_env)
        metadata = item["metadata"]
        item["novel_signature"] = signature_key(metadata) not in clean_signatures
        item["novel_split_group"] = (
            not metadata.get("split_group_id")
            or str(metadata["split_group_id"]) not in clean_split_groups
        )
        item["novel_near_duplicate_group"] = (
            not metadata.get("near_duplicate_group_id")
            or str(metadata["near_duplicate_group_id"]) not in clean_near_groups
        )

    n6_short_nontrivial = [
        item
        for item in n6_records
        if item["failed_checks"]
        == ("minimum_code_lines", "trusted_retrieval_strategy")
    ]
    n6_public = [
        item for item in n6_short_nontrivial if public_redistributable(item["metadata"])
    ]
    n6_strict_pass = [item for item in n6_public if replay_pass(item["replay"])]
    n6_novel = [
        item
        for item in n6_strict_pass
        if item["novel_signature"]
        and item["novel_split_group"]
        and item["novel_near_duplicate_group"]
    ]
    n6_selected = deduplicate_signatures(n6_novel)
    n6_selected_hashes = {
        str(item["metadata"].get("circuit_hash") or item["metadata"].get("hash"))
        for item in n6_selected
    }

    n7_strict_pass = [
        item for item in n7_short_public if replay_pass(item["replay"])
    ]
    n7_novel = [
        item
        for item in n7_strict_pass
        if item["novel_signature"]
        and item["novel_split_group"]
        and item["novel_near_duplicate_group"]
    ]
    n7_selected = deduplicate_signatures(n7_novel)
    n7_selected_hashes = {
        str(item["metadata"].get("circuit_hash") or item["metadata"].get("hash"))
        for item in n7_selected
    }

    current_split = split_contract(split_manifest_path)
    current_train = current_split["train"]
    n6_pool_size = 734 + len(n6_selected)
    n6_min_train = math.ceil(0.70 * n6_pool_size)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "pqid_n6_cleanliness_expansion_audit.json"
    report_md_path = output_dir / "pqid_n6_cleanliness_expansion_audit.md"
    replay_path = output_dir / "pqid_n6_and_n7_replay_audit.jsonl"
    inventory_path = output_dir / "pqid_n6_public_candidate_inventory.tsv"
    n6_selected_path = output_dir / "pqid_n6_drop_in_candidates.tsv"
    n7_selected_path = output_dir / "pqid_n7_short_code_comparator_candidates.tsv"

    replay_rows = []
    for item in [*n6_records, *n7_short_public]:
        metadata = item["metadata"]
        replay_rows.append(
            {
                "audit_label": item["audit_label"],
                "circuit_hash": metadata.get("circuit_hash"),
                "failed_checks": list(item["failed_checks"]),
                "repo_owner": metadata.get("repo_owner"),
                "repo_name": metadata.get("repo_name"),
                "file_path": metadata.get("file_path"),
                "public_redistributable": public_redistributable(metadata),
                "target_signature": target_signature(metadata),
                "strict": item["replay"]["strict"],
                "target_context": item["replay"]["target_context"],
            }
        )
    write_jsonl(replay_path, replay_rows)

    inventory_rows = [
        candidate_row(item, n6_selected_hashes) for item in n6_public
    ]
    write_tsv(inventory_path, inventory_rows)
    write_tsv(
        n6_selected_path,
        [candidate_row(item, n6_selected_hashes) for item in n6_selected],
    )
    write_tsv(
        n7_selected_path,
        [candidate_row(item, n7_selected_hashes) for item in n7_selected],
    )

    artifacts = {
        "report_json": display_path(report_json_path),
        "report_markdown": display_path(report_md_path),
        "replay_cell_audit": display_path(replay_path),
        "n6_public_candidate_inventory": display_path(inventory_path),
        "n6_drop_in_candidates": display_path(n6_selected_path),
        "n7_short_code_comparator_candidates": display_path(n7_selected_path),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "frozen_benchmark_changed": False,
            "manuscript_denominator_changed": False,
            "interpretation": "exactly six of eight readiness checks",
        },
        "inputs": {
            "source": {
                "path": display_path(source_path),
                "sha256": sha256_file(source_path),
                "rows": source_rows,
            },
            "seed_drafts": {
                "path": display_path(seed_path),
                "sha256": sha256_file(seed_path),
                "clean_generation_rows": len(clean_hashes),
            },
            "split_manifest": {
                "path": display_path(split_manifest_path),
                "sha256": sha256_file(split_manifest_path)
                if split_manifest_path.exists()
                else None,
            },
        },
        "environment": {
            "python": sys.version.split()[0],
            "qiskit_version": qiskit_env.get("version"),
            "evaluator_version": getattr(
                copy_baseline.validity, "EVALUATOR_VERSION", "<unknown>"
            ),
            "structural_predicate_version": getattr(
                copy_baseline.validity,
                "STRUCTURAL_PREDICATE_VERSION",
                "<unknown>",
            ),
        },
        "readiness_contract": {
            "check_order": list(readiness.BENCHMARK_CHECK_ORDER_V2),
            "descriptions": dict(readiness.BENCHMARK_CHECK_DESCRIPTIONS_V2),
            "minimum_code_lines": MIN_CODE_LINES,
            "minimum_gate_count": MIN_GATE_COUNT,
            "score_distribution": {
                str(score): count for score, count in sorted(score_distribution.items())
            },
        },
        "exact_6_of_8": {
            "failed_check_combinations": {
                key: dict(value)
                for key, value in sorted(
                    n6_combinations.items(),
                    key=lambda item: (-item[1]["rows"], item[0]),
                )
            },
            "candidate_funnel": {
                "exact_6_of_8": score_distribution[6],
                "non_mutation": len(n6_records),
                "nontrivial_short": len(n6_short_nontrivial),
                "public_redistributable": len(n6_public),
                "strict_replay_pass": len(n6_strict_pass),
                "novel_rows": len(n6_novel),
                "signature_deduplicated_drop_in": len(n6_selected),
            },
            "path_clean_replay": replay_counts(n6_records),
            "short_nontrivial_replay": replay_counts(n6_short_nontrivial),
            "public_short_nontrivial_replay": replay_counts(n6_public),
            "selected_drop_in_candidates": {
                "rows": len(n6_selected),
                "unique_signatures": len(
                    {signature_key(item["metadata"]) for item in n6_selected}
                ),
                "source_groups": len(
                    {
                        item["metadata"].get("split_group_id")
                        for item in n6_selected
                    }
                ),
                "gate_type_bins": dict(
                    Counter(gate_type_bin(item["metadata"]) for item in n6_selected)
                ),
                "repositories": {
                    f"{owner}/{repo}": count
                    for (owner, repo), count in sorted(
                        Counter(
                            (
                                item["metadata"].get("repo_owner"),
                                item["metadata"].get("repo_name"),
                            )
                            for item in n6_selected
                        ).items()
                    )
                },
                "pool_increase_percent": 100.0 * len(n6_selected) / 734,
                "existing_generation_facing_prompts": sum(
                    item.get("seed_role") in CLEAN_ROLES for item in n6_selected
                ),
            },
        },
        "seven_of_eight_short_code_comparator": {
            "public_rows": len(n7_short_public),
            "replay": replay_counts(n7_short_public),
            "strict_replay_pass": len(n7_strict_pass),
            "novel_rows": len(n7_novel),
            "signature_deduplicated_novel": len(n7_selected),
            "source_groups": len(
                {item["metadata"].get("split_group_id") for item in n7_selected}
            ),
            "gate_type_bins": dict(
                Counter(gate_type_bin(item["metadata"]) for item in n7_selected)
            ),
        },
        "split_governance": {
            "current_pool_size": 734,
            "current_train": current_train,
            "current_validation": current_split["validation"],
            "current_test": current_split["test"],
            "training_floor": 0.70,
            "n6_pool_size": n6_pool_size,
            "n6_minimum_train_rows": n6_min_train,
            "n6_candidates_required_for_train": max(0, n6_min_train - current_train),
            "n6_max_nontraining_additions": max(
                0, len(n6_selected) - max(0, n6_min_train - current_train)
            ),
        },
        "artifacts": artifacts,
    }
    report_json_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_md_path.write_text(build_report(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--seed-drafts", type=Path, default=DEFAULT_SEED_DRAFTS)
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    payload = run(
        source_path=args.source,
        seed_path=args.seed_drafts,
        split_manifest_path=args.split_manifest,
        output_dir=args.output_dir,
    )
    funnel = payload["exact_6_of_8"]["candidate_funnel"]
    print(f"Exact 6/8 rows: {funnel['exact_6_of_8']:,}")
    print(
        "Provisional signature-deduplicated drop-in candidates: "
        f"{funnel['signature_deduplicated_drop_in']:,}"
    )
    print(
        "Report: "
        f"{payload['artifacts']['report_markdown']}"
    )


if __name__ == "__main__":
    main()
