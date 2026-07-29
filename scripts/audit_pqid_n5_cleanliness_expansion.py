"""Audit exact 5/8 PQID readiness rows after presentation-only normalization.

The only plausible exact-5/8 subgroup consists of validated, path-clean,
nontrivial rows whose medium confidence and cleanup flags are jointly caused
by display-only ``draw`` or ``print`` calls. This script removes only those
presentation statements, recomputes the frozen readiness profile, and replays
the normalized circuit under the published evaluator.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
PQID_DIR = SCRIPT_PATH.parents[3]
PROJECT_SCRIPTS_DIR = PQID_DIR / "scripts"
if str(PROJECT_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_SCRIPTS_DIR))

import audit_pqid_n6_cleanliness_expansion as common  # noqa: E402
import enrich_metadata as enrichment  # noqa: E402


DEFAULT_SOURCE = common.DEFAULT_SOURCE
DEFAULT_SEED_DRAFTS = common.DEFAULT_SEED_DRAFTS
DEFAULT_SPLIT_MANIFEST = common.DEFAULT_SPLIT_MANIFEST
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts" / "n5_cleanliness_expansion_audit"

SCHEMA_VERSION = "pqid-bench-n5-cleanliness-expansion-audit-v1"
SELECTION_NAMESPACE = "pqid-bench-n5-normalized-candidates-v1"
PLAUSIBLE_FAILED_CHECKS = (
    "high_extraction_confidence",
    "no_demo_scaffolding",
    "no_cleanup_candidate",
)
PRESENTATION_RULES = {"draw_call", "print_call"}


def stable_rank(value: str) -> str:
    return hashlib.sha256(f"{SELECTION_NAMESPACE}:{value}".encode("utf-8")).hexdigest()


def code_sha256(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def call_is_draw(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Attribute) and call.func.attr == "draw"


def assignment_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    names: set[str] = set()
    for target in targets:
        for child in ast.walk(target):
            if isinstance(child, ast.Name):
                names.add(child.id)
    return names


class PresentationStripper(ast.NodeTransformer):
    """Remove presentation statements while retaining circuit mutations."""

    def __init__(self, loaded_names: set[str]) -> None:
        self.loaded_names = loaded_names
        self.removed: Counter[str] = Counter()

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        value = node.value
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name) and value.func.id == "print":
                self.removed["print_call"] += 1
                return None
            if call_is_draw(value):
                self.removed["draw_call"] += 1
                return None
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        if isinstance(node.value, ast.Call) and call_is_draw(node.value):
            names = assignment_names(node)
            if not names & self.loaded_names:
                self.removed["draw_assignment"] += 1
                return None
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if isinstance(node.value, ast.Call) and call_is_draw(node.value):
            names = assignment_names(node)
            if not names & self.loaded_names:
                self.removed["draw_assignment"] += 1
                return None
        return self.generic_visit(node)


def normalize_presentation_code(code: str) -> dict[str, Any]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"success": False, "error": f"SyntaxError:{exc.msg}"}

    loaded_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    stripper = PresentationStripper(loaded_names)
    normalized_tree = stripper.visit(tree)
    ast.fix_missing_locations(normalized_tree)
    try:
        normalized = ast.unparse(normalized_tree).strip() + "\n"
        compile(normalized, "<pqid-n5-normalized>", "exec")
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}:{exc}"}

    quality = enrichment.assess_extraction_quality(
        normalized, validation_status="validated"
    )
    if quality["contains_demo_scaffolding"]:
        return {
            "success": False,
            "error": "residual_demo_scaffolding",
            "quality": quality,
            "removed": dict(stripper.removed),
        }
    return {
        "success": True,
        "error": None,
        "code": normalized,
        "code_lines": len([line for line in normalized.splitlines() if line.strip()]),
        "quality": quality,
        "removed": dict(stripper.removed),
        "original_code_sha256": code_sha256(code),
        "normalized_code_sha256": code_sha256(normalized),
    }


def failed_key(failed_checks: tuple[str, ...]) -> str:
    return " + ".join(failed_checks)


def metadata_counter() -> Counter[str]:
    return Counter(
        {
            "rows": 0,
            "validated": 0,
            "path_clean": 0,
            "nontrivial": 0,
            "materialized": 0,
            "signature_complete": 0,
            "public_redistributable": 0,
        }
    )


def update_counter(
    counter: Counter[str], metadata: dict[str, Any], checks: dict[str, bool]
) -> None:
    counter["rows"] += 1
    counter["validated"] += checks["validated_execution"]
    counter["path_clean"] += checks["non_mutation_suite_path"]
    counter["nontrivial"] += int(metadata.get("gate_count") or 0) >= 2
    counter["materialized"] += metadata.get("materialized_circuit") is True
    counter["signature_complete"] += common.signature_complete(metadata)
    counter["public_redistributable"] += common.public_redistributable(metadata)


def post_normalization_readiness(
    item: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = dict(item["metadata"])
    normalization = item["normalization"]
    metadata["code_lines"] = normalization["code_lines"]
    metadata.update(normalization["quality"])
    normalized_row = {
        "input": item.get("input") or "",
        "output": normalization["code"],
        "metadata": metadata,
    }
    evaluation = common.readiness.evaluate_benchmark_suitability_v2(
        normalized_row,
        min_code_lines=common.MIN_CODE_LINES,
        min_gate_count=common.MIN_GATE_COUNT,
    )
    return metadata, evaluation


def normalized_replay(
    item: dict[str, Any], qiskit_env: dict[str, Any]
) -> dict[str, Any]:
    normalized_record = {
        "audit_label": "exact_5_of_8_presentation_normalized",
        "output": item["normalization"]["code"],
        "metadata": item["normalized_metadata"],
    }
    return common.replay_record(normalized_record, qiskit_env)


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(
        rows,
        key=lambda row: stable_rank(str(row["metadata"].get("circuit_hash"))),
    ):
        signature = common.signature_key(item["metadata"])
        if signature in seen:
            continue
        seen.add(signature)
        selected.append(item)
    return selected


def inventory_row(
    item: dict[str, Any], selected_hashes: set[str]
) -> dict[str, Any]:
    metadata = item["metadata"]
    normalized = item["normalization"]
    circuit_hash = str(metadata.get("circuit_hash"))
    return {
        "circuit_hash": circuit_hash,
        "repo_owner": metadata.get("repo_owner"),
        "repo_name": metadata.get("repo_name"),
        "file_path": metadata.get("file_path"),
        "split_group_id": metadata.get("split_group_id"),
        "near_duplicate_group_id": metadata.get("near_duplicate_group_id"),
        "original_code_lines": metadata.get("code_lines"),
        "normalized_code_lines": normalized.get("code_lines"),
        "removed_calls_json": common.stable_json(normalized.get("removed") or {}),
        "original_code_sha256": normalized.get("original_code_sha256"),
        "normalized_code_sha256": normalized.get("normalized_code_sha256"),
        "num_qubits": metadata.get("num_qubits"),
        "num_clbits": metadata.get("num_clbits"),
        "gate_count": metadata.get("gate_count"),
        "gate_type_count": len(metadata.get("gate_types") or {}),
        "gate_type_bin": common.gate_type_bin(metadata),
        "gate_types_json": common.stable_json(metadata.get("gate_types") or {}),
        "post_cleanup_readiness_score": item.get("post_score"),
        "normalized_execution": item.get("replay", {})
        .get("strict", {})
        .get("execution_success"),
        "normalized_signature": item.get("replay", {})
        .get("strict", {})
        .get("signature_match"),
        "normalized_qasm3": item.get("replay", {})
        .get("strict", {})
        .get("qasm3_export_success"),
        "novel_signature_vs_clean_734": item.get("novel_signature"),
        "novel_split_group_vs_clean_734": item.get("novel_split_group"),
        "novel_near_duplicate_group_vs_clean_734": item.get(
            "novel_near_duplicate_group"
        ),
        "seed_role": item.get("seed_role"),
        "selected_normalized_candidate": circuit_hash in selected_hashes,
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


def replay_counts(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    for item in rows:
        replay = item.get(field)
        if not replay:
            continue
        for mode in ["strict", "target_context"]:
            result = replay[mode]
            for metric in [
                "execution_success",
                "circuit_found",
                "signature_match",
                "qasm3_export_success",
            ]:
                counts[f"{mode}_{metric}"] += bool(result.get(metric))
            if not result.get("execution_success"):
                errors[f"{mode}:{result.get('execution_error_type')}"] += 1
    return {
        "rows": len(rows),
        **dict(counts),
        "execution_errors": dict(sorted(errors.items())),
    }


def pct(value: int, total: int) -> str:
    return f"{100.0 * value / total:.2f}%" if total else "n/a"


def build_report(payload: dict[str, Any]) -> str:
    n5 = payload["exact_5_of_8"]
    funnel = n5["candidate_funnel"]
    selected = n5["selected_normalized_candidates"]
    split = payload["split_governance"]
    lines = [
        "# PQID Exact 5/8 Cleanliness Expansion Audit",
        "",
        "## Verdict",
        "",
        "Exact `5/8` is not usable as a class, but it contains one defensible remediation subgroup. "
        "Most rows are unvalidated and structurally empty. In contrast, 238 validated, path-clean, "
        "nontrivial rows fail three correlated extraction checks because they include presentation-only "
        "`draw()` or `print()` calls. A conservative AST normalization can remove those calls without "
        "changing the circuit operations.",
        "",
        f"After public-release filtering, normalization, readiness recomputation, strict evaluator replay, "
        f"lineage exclusion, and signature deduplication, `{funnel['signature_deduplicated_candidates']}` "
        f"provisional candidates remain. They include `{selected['gate_type_bins'].get('5+', 0)}` targets "
        "in the `5+` operation-type band, so this route is materially more useful than exact `6/8`. "
        "It is still a curated future-release route, not permission to relabel raw `5/8` rows or revise "
        "the frozen PQID-Bench v1 denominator.",
        "",
        "## Exact 5/8 Composition",
        "",
        "| failed checks | rows | validated | path-clean | nontrivial | public/redistributable |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for failed, row in n5["failed_check_combinations"].items():
        lines.append(
            f"| `{failed}` | {row['rows']:,} | {row['validated']:,} | "
            f"{row['path_clean']:,} | {row['nontrivial']:,} | "
            f"{row['public_redistributable']:,} |"
        )
    lines.extend(
        [
            "",
            "## Normalization Funnel",
            "",
            "| stage | rows | share of exact 5/8 |",
            "| --- | ---: | ---: |",
            f"| exact 5/8 source rows | {funnel['exact_5_of_8']:,} | 100.00% |",
            f"| correlated presentation-scaffolding subgroup | {funnel['presentation_subgroup']:,} | {pct(funnel['presentation_subgroup'], funnel['exact_5_of_8'])} |",
            f"| public and redistributable | {funnel['public_redistributable']:,} | {pct(funnel['public_redistributable'], funnel['exact_5_of_8'])} |",
            f"| presentation-only normalization succeeds | {funnel['normalization_success']:,} | {pct(funnel['normalization_success'], funnel['exact_5_of_8'])} |",
            f"| normalized score becomes 8/8 | {funnel['post_cleanup_8_of_8']:,} | {pct(funnel['post_cleanup_8_of_8'], funnel['exact_5_of_8'])} |",
            f"| normalized strict execution + signature + QASM3 | {funnel['normalized_replay_pass']:,} | {pct(funnel['normalized_replay_pass'], funnel['exact_5_of_8'])} |",
            f"| both 8/8 and replay-valid | {funnel['readiness_and_replay_pass']:,} | {pct(funnel['readiness_and_replay_pass'], funnel['exact_5_of_8'])} |",
            f"| novel against clean 734 | {funnel['novel_rows']:,} | {pct(funnel['novel_rows'], funnel['exact_5_of_8'])} |",
            f"| one row per novel signature | {funnel['signature_deduplicated_candidates']:,} | {pct(funnel['signature_deduplicated_candidates'], funnel['exact_5_of_8'])} |",
            "",
            "## Why The Three Failed Checks Can Be Repaired Together",
            "",
            "The frozen extraction rule assigns `medium` confidence to an otherwise validated row whenever "
            "demo scaffolding is detected; the same signal also sets `cleanup_candidate=True`. Thus the "
            "three deficits in this subgroup arise from one observed cause. The normalizer removes only "
            "standalone `print` calls and unused `draw` calls or assignments. It does not remove gates, "
            "measurements, backend execution, result inspection, or arbitrary statements. The retained rows "
            "are then rescored from their normalized code and must independently reproduce the frozen target "
            "signature under strict replay.",
            "",
            "## Candidate Profile",
            "",
            f"- rows and unique signatures: `{selected['rows']}`",
            f"- source groups: `{selected['source_groups']}`",
            f"- operation-type bins: `{common.stable_json(selected['gate_type_bins'])}`",
            f"- gate-count range: `{selected['gate_count_range'][0]}--{selected['gate_count_range'][1]}`",
            f"- qubit range: `{selected['qubit_range'][0]}--{selected['qubit_range'][1]}`",
            f"- pool increase if all were admitted: `{selected['pool_increase_percent']:.2f}%`",
            f"- existing generation-facing prompts: `{selected['existing_generation_facing_prompts']}`",
            "",
            "The current prompts are repair/explanation prompts and cannot be reused. Each candidate still "
            "needs a new uniquely identifying generation prompt, an identifiability audit, and grouped split "
            "assignment before release.",
            "",
            "## Split-Governance Consequence",
            "",
            f"Adding all `{selected['rows']}` candidates would create a `{split['expanded_pool_size']}`-row "
            f"pool. Preserving the 70% training floor requires at least `{split['minimum_train_rows']}` "
            f"training rows, so at least `{split['candidates_required_for_train']}` candidates must enter "
            f"training and no more than `{split['maximum_nontraining_additions']}` can be added across "
            "validation and test without moving existing rows.",
            "",
            "## Recommendation",
            "",
            "1. Keep raw exact-5/8 rows outside the clean generation pool.",
            "2. Preserve PQID-Bench v1 and its 734-row population unchanged.",
            "3. Treat the selected normalized rows as a preregistered PQID-Bench v1.1/v2 curation queue.",
            "4. Generate fresh model-facing prompts, audit identifiability and parameters, and assign complete "
            "source groups under the existing leakage and 70% training-floor rules.",
            "5. Report the normalization provenance and both original and normalized code hashes in any future "
            "release.",
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
    clean_hashes, clean_signatures, draft_map = common.load_seed_contract(seed_path)
    failed_combinations: dict[str, Counter[str]] = defaultdict(metadata_counter)
    score_distribution: Counter[int] = Counter()
    clean_split_groups: set[str] = set()
    clean_near_groups: set[str] = set()
    presentation_subgroup: list[dict[str, Any]] = []
    source_rows = 0

    for source_index, row in enumerate(common.iter_jsonl(source_path)):
        source_rows += 1
        metadata = row.get("metadata") or {}
        evaluation = common.readiness.evaluate_benchmark_suitability_v2(
            row,
            min_code_lines=common.MIN_CODE_LINES,
            min_gate_count=common.MIN_GATE_COUNT,
        )
        score = int(evaluation["checks_passed"])
        score_distribution[score] += 1
        circuit_hash = str(metadata.get("circuit_hash") or "")
        if circuit_hash in clean_hashes:
            if metadata.get("split_group_id"):
                clean_split_groups.add(str(metadata["split_group_id"]))
            if metadata.get("near_duplicate_group_id"):
                clean_near_groups.add(str(metadata["near_duplicate_group_id"]))

        if score != 5:
            continue
        failed = tuple(evaluation["failed_checks"])
        update_counter(
            failed_combinations[failed_key(failed)],
            metadata,
            evaluation["checks"],
        )
        if failed == PLAUSIBLE_FAILED_CHECKS:
            draft = draft_map.get(circuit_hash) or {}
            presentation_subgroup.append(
                {
                    "source_index": source_index,
                    "input": row.get("input") or "",
                    "output": row.get("output") or "",
                    "metadata": metadata,
                    "failed_checks": failed,
                    "seed_role": draft.get("seed_role"),
                    "has_existing_prompt": bool(draft.get("has_prompt")),
                }
            )

    if source_rows != 91_719:
        raise RuntimeError(f"Expected 91,719 source rows, found {source_rows}")
    if score_distribution[5] != 27_116:
        raise RuntimeError(f"Expected 27,116 exact-5/8 rows, found {score_distribution[5]}")

    public_rows = [
        item
        for item in presentation_subgroup
        if common.public_redistributable(item["metadata"])
    ]
    qiskit_env = common.copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit unavailable: {qiskit_env.get('error')}")

    for item in public_rows:
        item["raw_replay"] = common.replay_record(
            {
                "audit_label": "exact_5_of_8_raw",
                "output": item["output"],
                "metadata": item["metadata"],
            },
            qiskit_env,
        )
        rules = set(item["metadata"].get("cleanup_rules_triggered") or [])
        if not rules <= PRESENTATION_RULES:
            item["normalization"] = {
                "success": False,
                "error": f"non_presentation_rules:{sorted(rules - PRESENTATION_RULES)}",
            }
            continue
        item["normalization"] = normalize_presentation_code(item["output"])
        if not item["normalization"]["success"]:
            continue
        normalized_metadata, post_evaluation = post_normalization_readiness(item)
        item["normalized_metadata"] = normalized_metadata
        item["post_readiness"] = post_evaluation
        item["post_score"] = int(post_evaluation["checks_passed"])
        item["replay"] = normalized_replay(item, qiskit_env)
        metadata = item["metadata"]
        item["novel_signature"] = (
            common.signature_key(metadata) not in clean_signatures
        )
        item["novel_split_group"] = (
            not metadata.get("split_group_id")
            or str(metadata["split_group_id"]) not in clean_split_groups
        )
        item["novel_near_duplicate_group"] = (
            not metadata.get("near_duplicate_group_id")
            or str(metadata["near_duplicate_group_id"]) not in clean_near_groups
        )

    normalized_rows = [
        item for item in public_rows if item["normalization"].get("success")
    ]
    post_8 = [item for item in normalized_rows if item.get("post_score") == 8]
    normalized_replay_pass = [
        item
        for item in normalized_rows
        if item.get("replay") and common.replay_pass(item["replay"])
    ]
    readiness_and_replay = [
        item
        for item in post_8
        if item.get("replay") and common.replay_pass(item["replay"])
    ]
    novel_rows = [
        item
        for item in readiness_and_replay
        if item["novel_signature"]
        and item["novel_split_group"]
        and item["novel_near_duplicate_group"]
    ]
    selected = deduplicate(novel_rows)
    selected_hashes = {
        str(item["metadata"].get("circuit_hash")) for item in selected
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "pqid_n5_cleanliness_expansion_audit.json"
    report_md_path = output_dir / "pqid_n5_cleanliness_expansion_audit.md"
    replay_path = output_dir / "pqid_n5_public_normalization_replay_audit.jsonl"
    inventory_path = output_dir / "pqid_n5_public_candidate_inventory.tsv"
    selected_path = output_dir / "pqid_n5_normalized_candidates.tsv"
    normalized_source_path = output_dir / "pqid_n5_normalized_candidate_source.jsonl"

    replay_rows = []
    for item in public_rows:
        metadata = item["metadata"]
        replay_rows.append(
            {
                "circuit_hash": metadata.get("circuit_hash"),
                "repo_owner": metadata.get("repo_owner"),
                "repo_name": metadata.get("repo_name"),
                "file_path": metadata.get("file_path"),
                "cleanup_rules_triggered": metadata.get("cleanup_rules_triggered"),
                "normalization": {
                    key: value
                    for key, value in item["normalization"].items()
                    if key != "code"
                },
                "post_cleanup_readiness_score": item.get("post_score"),
                "raw_replay": item.get("raw_replay"),
                "normalized_replay": item.get("replay"),
                "selected": str(metadata.get("circuit_hash")) in selected_hashes,
            }
        )
    common.write_jsonl(replay_path, replay_rows)
    write_tsv(
        inventory_path,
        [inventory_row(item, selected_hashes) for item in normalized_rows],
    )
    write_tsv(
        selected_path,
        [inventory_row(item, selected_hashes) for item in selected],
    )
    common.write_jsonl(
        normalized_source_path,
        [
            {
                "candidate_schema_version": SCHEMA_VERSION,
                "circuit_hash": item["metadata"].get("circuit_hash"),
                "normalized_code": item["normalization"]["code"],
                "normalized_code_sha256": item["normalization"][
                    "normalized_code_sha256"
                ],
                "original_code_sha256": item["normalization"]["original_code_sha256"],
                "normalization_removed": item["normalization"]["removed"],
                "source": {
                    "repo_owner": item["metadata"].get("repo_owner"),
                    "repo_name": item["metadata"].get("repo_name"),
                    "file_path": item["metadata"].get("file_path"),
                    "original_url": item["metadata"].get("original_url"),
                    "split_group_id": item["metadata"].get("split_group_id"),
                    "near_duplicate_group_id": item["metadata"].get(
                        "near_duplicate_group_id"
                    ),
                },
                "target_signature": common.target_signature(item["metadata"]),
                "release": {
                    "release_view_membership": item["metadata"].get(
                        "release_view_membership"
                    ),
                    "distribution_rights_status": item["metadata"].get(
                        "distribution_rights_status"
                    ),
                    "repo_license": item["metadata"].get("repo_license"),
                },
                "status": "curation_candidate_not_part_of_frozen_benchmark",
            }
            for item in selected
        ],
    )

    current_split = common.split_contract(split_manifest_path)
    expanded_pool = 734 + len(selected)
    minimum_train = math.ceil(0.70 * expanded_pool)
    gate_counts = [int(item["metadata"]["gate_count"]) for item in selected]
    qubits = [int(item["metadata"]["num_qubits"]) for item in selected]
    artifacts = {
        "report_json": common.display_path(report_json_path),
        "report_markdown": common.display_path(report_md_path),
        "normalization_replay_audit": common.display_path(replay_path),
        "public_candidate_inventory": common.display_path(inventory_path),
        "selected_normalized_candidates": common.display_path(selected_path),
        "normalized_candidate_source": common.display_path(normalized_source_path),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "frozen_benchmark_changed": False,
            "manuscript_denominator_changed": False,
            "interpretation": "exactly five of eight readiness checks",
            "normalization": "presentation-only AST transformation",
        },
        "inputs": {
            "source": {
                "path": common.display_path(source_path),
                "sha256": common.sha256_file(source_path),
                "rows": source_rows,
            },
            "seed_drafts": {
                "path": common.display_path(seed_path),
                "sha256": common.sha256_file(seed_path),
                "clean_generation_rows": len(clean_hashes),
            },
            "split_manifest": {
                "path": common.display_path(split_manifest_path),
                "sha256": common.sha256_file(split_manifest_path)
                if split_manifest_path.exists()
                else None,
            },
        },
        "environment": {
            "python": sys.version.split()[0],
            "qiskit_version": qiskit_env.get("version"),
            "evaluator_version": getattr(
                common.copy_baseline.validity, "EVALUATOR_VERSION", "<unknown>"
            ),
            "structural_predicate_version": getattr(
                common.copy_baseline.validity,
                "STRUCTURAL_PREDICATE_VERSION",
                "<unknown>",
            ),
        },
        "exact_5_of_8": {
            "score_distribution": {
                str(score): count for score, count in sorted(score_distribution.items())
            },
            "failed_check_combinations": {
                key: dict(value)
                for key, value in sorted(
                    failed_combinations.items(),
                    key=lambda item: (-item[1]["rows"], item[0]),
                )
            },
            "candidate_funnel": {
                "exact_5_of_8": score_distribution[5],
                "presentation_subgroup": len(presentation_subgroup),
                "public_redistributable": len(public_rows),
                "normalization_success": len(normalized_rows),
                "post_cleanup_8_of_8": len(post_8),
                "normalized_replay_pass": len(normalized_replay_pass),
                "readiness_and_replay_pass": len(readiness_and_replay),
                "novel_rows": len(novel_rows),
                "signature_deduplicated_candidates": len(selected),
            },
            "raw_replay": replay_counts(public_rows, "raw_replay"),
            "normalized_replay": replay_counts(normalized_rows, "replay"),
            "selected_normalized_candidates": {
                "rows": len(selected),
                "unique_signatures": len(
                    {common.signature_key(item["metadata"]) for item in selected}
                ),
                "source_groups": len(
                    {item["metadata"].get("split_group_id") for item in selected}
                ),
                "gate_type_bins": dict(
                    Counter(common.gate_type_bin(item["metadata"]) for item in selected)
                ),
                "repositories": {
                    f"{owner}/{repo}": count
                    for (owner, repo), count in sorted(
                        Counter(
                            (
                                item["metadata"].get("repo_owner"),
                                item["metadata"].get("repo_name"),
                            )
                            for item in selected
                        ).items()
                    )
                },
                "gate_count_range": [min(gate_counts), max(gate_counts)],
                "qubit_range": [min(qubits), max(qubits)],
                "pool_increase_percent": 100.0 * len(selected) / 734,
                "existing_generation_facing_prompts": sum(
                    item.get("seed_role") in common.CLEAN_ROLES for item in selected
                ),
            },
        },
        "comparison": {
            "exact_6_of_8_selected_candidates": 6,
            "exact_6_of_8_gate_type_bins": {"1-2": 4, "3-4": 2, "5+": 0},
            "seven_of_eight_short_code_selected_candidates": 28,
            "seven_of_eight_short_code_gate_type_bins": {
                "1-2": 19,
                "3-4": 9,
                "5+": 0,
            },
        },
        "split_governance": {
            "current_pool_size": 734,
            "current_train": current_split["train"],
            "current_validation": current_split["validation"],
            "current_test": current_split["test"],
            "training_floor": 0.70,
            "expanded_pool_size": expanded_pool,
            "minimum_train_rows": minimum_train,
            "candidates_required_for_train": max(
                0, minimum_train - current_split["train"]
            ),
            "maximum_nontraining_additions": max(
                0,
                len(selected)
                - max(0, minimum_train - current_split["train"]),
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
    funnel = payload["exact_5_of_8"]["candidate_funnel"]
    print(f"Exact 5/8 rows: {funnel['exact_5_of_8']:,}")
    print(
        "Selected presentation-normalized candidates: "
        f"{funnel['signature_deduplicated_candidates']:,}"
    )
    print(f"Report: {payload['artifacts']['report_markdown']}")


if __name__ == "__main__":
    main()
