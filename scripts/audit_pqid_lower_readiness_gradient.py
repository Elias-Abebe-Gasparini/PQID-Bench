"""Audit exact 1/8--4/8 PQID readiness strata and their scientific uses.

The audit is deliberately non-mutating. It distinguishes records that retain
an identifiable validated circuit from parseable runtime failures and
syntax-level repair material. Public validated records are presentation-
normalized and replayed under the published evaluator. A separate sensitivity
tests whether the five-line threshold, rather than circuit integrity, is the
only remaining obstacle for any exact-4/8 records.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import sys
import warnings
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
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import audit_pqid_n5_cleanliness_expansion as n5  # noqa: E402
import audit_pqid_n6_cleanliness_expansion as common  # noqa: E402


DEFAULT_SOURCE = common.DEFAULT_SOURCE
DEFAULT_SEED_DRAFTS = common.DEFAULT_SEED_DRAFTS
DEFAULT_SPLIT_MANIFEST = common.DEFAULT_SPLIT_MANIFEST
DEFAULT_OUTPUT_DIR = (
    SUBMISSION_DIR / "artifacts" / "lower_readiness_gradient_audit"
)

SCHEMA_VERSION = "pqid-lower-readiness-gradient-audit-v1"
SELECTION_NAMESPACE = "pqid-lower-readiness-short-code-candidates-v1"
LOWER_SCORES = {1, 2, 3, 4}
PRESENTATION_RULES = {"draw_call", "print_call"}


def failed_key(failed_checks: list[str] | tuple[str, ...]) -> str:
    return " + ".join(failed_checks)


def ast_parseable(code: str) -> tuple[bool, str | None]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            ast.parse(code)
    except (SyntaxError, TypeError, ValueError) as exc:
        return False, type(exc).__name__
    return True, None


def initialized_counter() -> Counter[str]:
    return Counter(
        {
            "rows": 0,
            "public_redistributable": 0,
            "ast_parseable": 0,
            "ast_unparseable": 0,
            "public_ast_parseable": 0,
            "public_ast_unparseable": 0,
            "validated": 0,
            "validated_signature_complete": 0,
            "public_validated_signature_complete": 0,
            "materialized_circuit": 0,
            "circuit_stats_available": 0,
            "stored_qasm3_success": 0,
            "non_mutation_path": 0,
        }
    )


def update_counter(
    counter: Counter[str],
    row: dict[str, Any],
    parseable: bool,
) -> None:
    metadata = row.get("metadata") or {}
    public = common.public_redistributable(metadata)
    validated = metadata.get("validation_status") == "validated"
    signature = common.signature_complete(metadata)
    counter["rows"] += 1
    counter["public_redistributable"] += public
    counter["ast_parseable"] += parseable
    counter["ast_unparseable"] += not parseable
    counter["public_ast_parseable"] += public and parseable
    counter["public_ast_unparseable"] += public and not parseable
    counter["validated"] += validated
    counter["validated_signature_complete"] += validated and signature
    counter["public_validated_signature_complete"] += (
        public and validated and signature
    )
    counter["materialized_circuit"] += (
        metadata.get("materialized_circuit") is True
    )
    counter["circuit_stats_available"] += (
        metadata.get("circuit_stats_available") is True
    )
    counter["stored_qasm3_success"] += (
        metadata.get("openqasm3_export_successful") is True
    )
    counter["non_mutation_path"] += (
        metadata.get("mutation_suite_candidate") is not True
    )


def post_normalization(
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


def replay_summary(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    return {
        "rows": len(items),
        "strict_execution": sum(
            bool((item.get(field) or {}).get("strict", {}).get("execution_success"))
            for item in items
        ),
        "strict_signature": sum(
            bool((item.get(field) or {}).get("strict", {}).get("signature_match"))
            for item in items
        ),
        "strict_qasm3": sum(
            bool((item.get(field) or {}).get("strict", {}).get("qasm3_export_success"))
            for item in items
        ),
        "strict_full_pass": sum(
            bool(item.get(field)) and common.replay_pass(item[field])
            for item in items
        ),
        "target_context_full_pass": sum(
            bool(item.get(field))
            and common.replay_pass(item[field], mode="target_context")
            for item in items
        ),
    }


def novelty_flags(
    item: dict[str, Any],
    clean_signatures: set[str],
    clean_split_groups: set[str],
    clean_near_groups: set[str],
) -> dict[str, bool]:
    metadata = item["metadata"]
    split_group = str(metadata.get("split_group_id") or "")
    near_group = str(metadata.get("near_duplicate_group_id") or "")
    return {
        "novel_signature": common.signature_key(metadata) not in clean_signatures,
        "novel_split_group": not split_group or split_group not in clean_split_groups,
        "novel_near_duplicate_group": (
            not near_group or near_group not in clean_near_groups
        ),
    }


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(
        rows,
        key=lambda row: n5.stable_rank(
            f"{SELECTION_NAMESPACE}:{row['metadata'].get('circuit_hash')}"
        ),
    ):
        signature = common.signature_key(item["metadata"])
        if signature in seen:
            continue
        seen.add(signature)
        selected.append(item)
    return selected


def pct(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def inventory_row(item: dict[str, Any], selected_hashes: set[str]) -> dict[str, Any]:
    metadata = item["metadata"]
    replay = item.get("normalized_replay") or {}
    strict = replay.get("strict") or {}
    target_context = replay.get("target_context") or {}
    return {
        "readiness_score_before": item["score"],
        "failed_checks_before": failed_key(item["failed_checks"]),
        "circuit_hash": metadata.get("circuit_hash"),
        "repo_owner": metadata.get("repo_owner"),
        "repo_name": metadata.get("repo_name"),
        "file_path": metadata.get("file_path"),
        "retrieval_strategy": metadata.get("retrieval_strategy"),
        "original_code_lines": metadata.get("code_lines"),
        "normalized_code_lines": (
            item.get("normalization") or {}
        ).get("code_lines"),
        "gate_count": metadata.get("gate_count"),
        "gate_type_count": len(metadata.get("gate_types") or {}),
        "num_qubits": metadata.get("num_qubits"),
        "num_clbits": metadata.get("num_clbits"),
        "cleanup_rules": ",".join(
            sorted(metadata.get("cleanup_rules_triggered") or [])
        ),
        "normalization_success": bool(
            (item.get("normalization") or {}).get("success")
        ),
        "post_readiness_score": item.get("post_score"),
        "post_failed_checks": failed_key(
            (item.get("post_readiness") or {}).get("failed_checks") or []
        ),
        "strict_execution": strict.get("execution_success"),
        "strict_signature": strict.get("signature_match"),
        "strict_qasm3": strict.get("qasm3_export_success"),
        "strict_full_pass": bool(replay) and common.replay_pass(replay),
        "target_context_full_pass": bool(replay)
        and common.replay_pass(replay, mode="target_context"),
        "novel_signature": item.get("novel_signature"),
        "novel_split_group": item.get("novel_split_group"),
        "novel_near_duplicate_group": item.get(
            "novel_near_duplicate_group"
        ),
        "short_code_sensitivity_candidate": item.get(
            "short_code_sensitivity_candidate", False
        ),
        "selected": str(metadata.get("circuit_hash")) in selected_hashes,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_report(payload: dict[str, Any]) -> str:
    lower = payload["lower_readiness"]
    aggregate = lower["aggregate"]
    funnel = lower["validated_public_replay"]
    short = lower["short_code_sensitivity"]
    validation = payload["validation"]
    lines = [
        "# PQID Lower-Readiness Gradient Audit",
        "",
        "## Scope",
        "",
        "This non-mutating audit profiles every exact `1/8`--`4/8` row under "
        "the frozen eight-check readiness definition. It does not alter the "
        "PQID-Bench v1 split, model outputs, evaluator, manuscript denominator, "
        "or release artifacts. The purpose is to distinguish clean-generation "
        "expansion potential from repair, diagnosis, and non-identifiable code "
        "material.",
        "",
        "## Readiness Gradient",
        "",
        "| Score | Rows | Public | AST parseable | AST unparseable | "
        "Validated signatures | Public validated signatures |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for score in ("4", "3", "2", "1"):
        row = lower["by_score"][score]
        lines.append(
            f"| {score}/8 | {row['rows']:,} | "
            f"{row['public_redistributable']:,} | "
            f"{row['ast_parseable']:,} | {row['ast_unparseable']:,} | "
            f"{row['validated_signature_complete']:,} | "
            f"{row['public_validated_signature_complete']:,} |"
        )
    lines.extend(
        [
            "",
            f"Across the four strata, `{aggregate['rows']:,}` records are "
            f"present. Only `{aggregate['validated_signature_complete']:,}` "
            f"({aggregate['validated_signature_percent']:.2f}%) retain a "
            "validated, evaluator-facing target signature. The remaining "
            f"`{aggregate['non_identifiable_for_generation']:,}` records cannot "
            "be scored as clean generation targets without first reconstructing "
            "and validating a circuit.",
            "",
            "## Public Scientific Uses",
            "",
            f"Among `{aggregate['public_redistributable']:,}` public rows, "
            f"`{aggregate['public_validated_signature_complete']:,}` are "
            "validated circuit records, "
            f"`{aggregate['public_parseable_unvalidated']:,}` are syntactically "
            "parseable but unvalidated repair or diagnosis cases, and "
            f"`{aggregate['public_ast_unparseable']:,}` are syntax-level repair "
            "cases. The latter two classes are useful as repair-candidate "
            "curation and failure-taxonomy material, but they are not validated "
            "repair pairs or clean-generation targets.",
            "",
            "## Replay Of Identifiable Public Circuits",
            "",
            f"`{funnel['input_rows']:,}` public rows have validated complete "
            "signatures. Presentation-only normalization succeeds for "
            f"`{funnel['normalization_success']:,}` and the normalized evaluator "
            f"replay passes execution, signature, and OpenQASM 3 jointly for "
            f"`{funnel['strict_full_pass']:,}` rows. None reaches `8/8` under the "
            "unchanged readiness contract because each retains at least one "
            "independent size or provenance failure.",
            "",
            "## Five-Line Threshold Sensitivity",
            "",
            f"The exact-`4/8` short-code subgroup yields "
            f"`{short['integrity_pass_rows']:,}` public records whose only "
            "post-normalization readiness failure is `minimum_code_lines` and "
            "which pass strict execution, signature recovery, and OpenQASM 3 "
            "export. After excluding current clean-pool signatures and lineage "
            f"groups, `{short['novel_rows']:,}` rows remain and "
            f"`{short['signature_deduplicated_candidates']:,}` unique signatures "
            "are selected.",
            "",
        ]
    )
    if short["signature_deduplicated_candidates"]:
        lines.extend(
            [
                f"These candidates span gate-type bins "
                f"`{short['gate_type_bins']}` and would increase the 734-row "
                f"clean pool by {short['pool_increase_percent']:.2f}%. They are "
                "a threshold-sensitivity curation queue, not drop-in v1 rows: "
                "admission would require an explicit, versioned change to the "
                "five-line benchmark-readiness rule.",
                "",
            ]
        )
    lines.extend(
        [
            "## Scientific Data Interpretation",
            "",
            "The scalar readiness score should be published together with its "
            "eight-dimensional check vector. Equal scores conceal qualitatively "
            "different records: a validated short circuit, a provenance-limited "
            "circuit, a parseable runtime failure, and a syntax failure can occupy "
            "the same numerical stratum. The lower-readiness corpus is therefore "
            "scientifically useful, but mainly as a structured failure and repair "
            "resource rather than as an undifferentiated source of clean benchmark "
            "targets.",
            "",
            "The audit supports three release views: (1) validated identifiable "
            "circuits for diagnostic sensitivity analyses; (2) parseable "
            "unvalidated programs for runtime repair and diagnosis; and (3) "
            "unparseable programs for syntax repair. Generation benchmarks should "
            "continue to require a validated, materialized target and complete "
            "signature.",
            "",
            "## Cross-Stratum Curation Context",
            "",
            "| Starting stratum | Selected signatures | Audited route | "
            "`5+` operation types |",
            "|---:|---:|---|---:|",
            "| 7/8 | 28 | short-code comparator | 0 |",
            "| 6/8 | 6 | public, path-clean replay funnel | 0 |",
            "| 5/8 | 35 | presentation-only normalization | 14 |",
            f"| 4/8 | {short['signature_deduplicated_candidates']} | "
            "five-line-threshold sensitivity | 0 |",
            "| 3/8--1/8 | 0 | no single deterministic remediation reaches "
            "clean eligibility | 0 |",
            "",
            "These row-disjoint audits are curation ceilings, not an additive "
            "release count: a future combined queue still requires cross-queue "
            "signature and lineage deduplication, prompt authoring, "
            "identifiability review, and grouped split assignment. Exact `5/8` "
            "remains the only audited near-threshold route that materially adds "
            "high-diversity (`5+`) targets.",
            "",
            "## Validation",
            "",
            f"All `{validation['checks_total']}` audit invariants pass. They "
            "cover source cardinality, exact score totals, public-class "
            "partitioning, normalized-code compilation and hashing, strict "
            "replay, uniqueness, and exclusion of current clean signatures and "
            "lineage groups.",
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
    score_distribution: Counter[int] = Counter()
    by_score: dict[int, Counter[str]] = defaultdict(initialized_counter)
    by_combination: dict[tuple[int, str], Counter[str]] = defaultdict(
        initialized_counter
    )
    validation_statuses: dict[int, Counter[str]] = defaultdict(Counter)
    validation_errors: dict[int, Counter[str]] = defaultdict(Counter)
    clean_split_groups: set[str] = set()
    clean_near_groups: set[str] = set()
    public_validated: list[dict[str, Any]] = []
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

        if score not in LOWER_SCORES:
            continue
        code = str(row.get("output") or "")
        parseable, parse_error = ast_parseable(code)
        update_counter(by_score[score], row, parseable)
        combination = failed_key(evaluation["failed_checks"])
        update_counter(by_combination[(score, combination)], row, parseable)
        validation_statuses[score][
            str(metadata.get("validation_status") or "<none>")
        ] += 1
        validation_errors[score][
            str(
                metadata.get("validation_error_type")
                or metadata.get("execution_error_type")
                or parse_error
                or "<none>"
            )
        ] += 1

        if (
            common.public_redistributable(metadata)
            and metadata.get("validation_status") == "validated"
            and common.signature_complete(metadata)
        ):
            draft = draft_map.get(circuit_hash) or {}
            public_validated.append(
                {
                    "source_index": source_index,
                    "score": score,
                    "failed_checks": tuple(evaluation["failed_checks"]),
                    "input": row.get("input") or "",
                    "output": code,
                    "metadata": metadata,
                    "seed_role": draft.get("seed_role"),
                    "has_existing_prompt": bool(draft.get("has_prompt")),
                }
            )

    if source_rows != 91_719:
        raise RuntimeError(f"Expected 91,719 source rows, found {source_rows}")
    expected = {1: 73, 2: 2_980, 3: 9_153, 4: 39_219}
    observed = {score: score_distribution[score] for score in expected}
    if observed != expected:
        raise RuntimeError(
            f"Unexpected lower-readiness distribution: {observed}; expected {expected}"
        )

    qiskit_env = common.copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit unavailable: {qiskit_env.get('error')}")

    for item in public_validated:
        item["raw_replay"] = common.replay_record(
            {
                "audit_label": f"exact_{item['score']}_of_8_raw",
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
        item["normalization"] = n5.normalize_presentation_code(item["output"])
        if not item["normalization"].get("success"):
            continue
        normalized_metadata, post_readiness = post_normalization(item)
        item["normalized_metadata"] = normalized_metadata
        item["post_readiness"] = post_readiness
        item["post_score"] = int(post_readiness["checks_passed"])
        item["normalized_replay"] = common.replay_record(
            {
                "audit_label": f"exact_{item['score']}_of_8_normalized",
                "output": item["normalization"]["code"],
                "metadata": normalized_metadata,
            },
            qiskit_env,
        )
        item.update(
            novelty_flags(
                item,
                clean_signatures,
                clean_split_groups,
                clean_near_groups,
            )
        )
        item["short_code_sensitivity_candidate"] = (
            item["score"] == 4
            and post_readiness["failed_checks"] == ["minimum_code_lines"]
            and common.replay_pass(item["normalized_replay"])
        )

    normalized = [
        item
        for item in public_validated
        if (item.get("normalization") or {}).get("success")
    ]
    post_8 = [item for item in normalized if item.get("post_score") == 8]
    short_integrity = [
        item
        for item in normalized
        if item.get("short_code_sensitivity_candidate")
    ]
    short_novel = [
        item
        for item in short_integrity
        if item.get("novel_signature")
        and item.get("novel_split_group")
        and item.get("novel_near_duplicate_group")
    ]
    short_selected = deduplicate(short_novel)
    selected_hashes = {
        str(item["metadata"].get("circuit_hash")) for item in short_selected
    }

    aggregate = initialized_counter()
    for score in sorted(LOWER_SCORES):
        aggregate.update(by_score[score])
    aggregate_rows = int(aggregate["rows"])
    validated_signatures = int(aggregate["validated_signature_complete"])
    public_validated_signatures = int(
        aggregate["public_validated_signature_complete"]
    )
    public_parseable_unvalidated = (
        int(aggregate["public_ast_parseable"]) - public_validated_signatures
    )
    selected_signatures = {
        common.signature_key(item["metadata"]) for item in short_selected
    }
    selected_split_groups = {
        str(item["metadata"].get("split_group_id") or "")
        for item in short_selected
    }
    selected_near_groups = {
        str(item["metadata"].get("near_duplicate_group_id") or "")
        for item in short_selected
    }
    validation_checks = {
        "source_rows_91719": source_rows == 91_719,
        "exact_lower_score_distribution": observed == expected,
        "lower_rows_sum_51425": aggregate_rows == 51_425,
        "validated_rows_have_complete_signatures": (
            int(aggregate["validated"]) == validated_signatures == 405
        ),
        "all_lower_rows_are_nonmutation_path": (
            int(aggregate["non_mutation_path"]) == aggregate_rows
        ),
        "public_partition_is_exhaustive": (
            public_validated_signatures
            + public_parseable_unvalidated
            + int(aggregate["public_ast_unparseable"])
            == int(aggregate["public_redistributable"])
        ),
        "no_normalized_row_reaches_frozen_8_of_8": not post_8,
        "selected_candidates_are_public": all(
            common.public_redistributable(item["metadata"])
            for item in short_selected
        ),
        "selected_candidates_compile": all(
            ast_parseable(item["normalization"]["code"])[0]
            for item in short_selected
        ),
        "selected_candidate_hashes_match": all(
            n5.code_sha256(item["normalization"]["code"])
            == item["normalization"]["normalized_code_sha256"]
            for item in short_selected
        ),
        "selected_candidates_fail_only_line_threshold": all(
            item["post_readiness"]["failed_checks"] == ["minimum_code_lines"]
            for item in short_selected
        ),
        "selected_candidates_below_five_lines": all(
            int(item["normalization"]["code_lines"]) < common.MIN_CODE_LINES
            for item in short_selected
        ),
        "selected_candidates_pass_strict_replay": all(
            common.replay_pass(item["normalized_replay"])
            for item in short_selected
        ),
        "selected_signatures_unique": (
            len(selected_signatures) == len(short_selected)
        ),
        "selected_signatures_exclude_clean_pool": all(
            signature not in clean_signatures
            for signature in selected_signatures
        ),
        "selected_split_groups_exclude_clean_pool": all(
            not group or group not in clean_split_groups
            for group in selected_split_groups
        ),
        "selected_near_groups_exclude_clean_pool": all(
            not group or group not in clean_near_groups
            for group in selected_near_groups
        ),
    }
    failed_validation = [
        name for name, passed in validation_checks.items() if not passed
    ]
    if failed_validation:
        raise RuntimeError(
            "Lower-readiness audit validation failed: "
            + ", ".join(failed_validation)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "pqid_lower_readiness_gradient_audit.json"
    report_md_path = output_dir / "pqid_lower_readiness_gradient_audit.md"
    combinations_path = (
        output_dir / "pqid_lower_readiness_failed_check_combinations.tsv"
    )
    gradient_path = output_dir / "pqid_lower_readiness_scientific_data_table.tsv"
    replay_path = output_dir / "pqid_lower_readiness_public_validated_replay.jsonl"
    inventory_path = (
        output_dir / "pqid_lower_readiness_public_validated_inventory.tsv"
    )
    selected_path = (
        output_dir / "pqid_lower_readiness_short_code_candidates.tsv"
    )
    selected_source_path = (
        output_dir / "pqid_lower_readiness_short_code_candidate_source.jsonl"
    )

    combination_rows: list[dict[str, Any]] = []
    for (score, combination), counter in sorted(
        by_combination.items(), key=lambda item: (item[0][0], -item[1]["rows"], item[0][1])
    ):
        combination_rows.append(
            {
                "readiness_score": score,
                "failed_checks": combination,
                **dict(counter),
            }
        )
    write_tsv(combinations_path, combination_rows)

    gradient_rows: list[dict[str, Any]] = []
    for score in sorted(LOWER_SCORES, reverse=True):
        counter = by_score[score]
        gradient_rows.append(
            {
                "readiness_score": score,
                **dict(counter),
                "validation_status_distribution": json.dumps(
                    dict(validation_statuses[score]), sort_keys=True
                ),
                "validation_error_distribution": json.dumps(
                    dict(validation_errors[score]), sort_keys=True
                ),
            }
        )
    write_tsv(gradient_path, gradient_rows)

    replay_rows = []
    for item in public_validated:
        metadata = item["metadata"]
        replay_rows.append(
            {
                "readiness_score": item["score"],
                "circuit_hash": metadata.get("circuit_hash"),
                "failed_checks": list(item["failed_checks"]),
                "cleanup_rules_triggered": metadata.get(
                    "cleanup_rules_triggered"
                ),
                "normalization": {
                    key: value
                    for key, value in (item.get("normalization") or {}).items()
                    if key != "code"
                },
                "post_readiness": item.get("post_readiness"),
                "raw_replay": item.get("raw_replay"),
                "normalized_replay": item.get("normalized_replay"),
                "short_code_sensitivity_candidate": item.get(
                    "short_code_sensitivity_candidate", False
                ),
                "selected": str(metadata.get("circuit_hash")) in selected_hashes,
            }
        )
    common.write_jsonl(replay_path, replay_rows)
    write_tsv(
        inventory_path,
        [inventory_row(item, selected_hashes) for item in public_validated],
    )
    write_tsv(
        selected_path,
        [inventory_row(item, selected_hashes) for item in short_selected],
    )
    common.write_jsonl(
        selected_source_path,
        [
            {
                "candidate_schema_version": SCHEMA_VERSION,
                "status": (
                    "short-code-threshold-sensitivity-candidate-not-part-of-"
                    "frozen-benchmark"
                ),
                "circuit_hash": item["metadata"].get("circuit_hash"),
                "normalized_code": item["normalization"]["code"],
                "normalized_code_sha256": item["normalization"][
                    "normalized_code_sha256"
                ],
                "original_code_sha256": item["normalization"][
                    "original_code_sha256"
                ],
                "normalization_removed": item["normalization"]["removed"],
                "target_signature": common.target_signature(item["metadata"]),
                "source": {
                    "repo_owner": item["metadata"].get("repo_owner"),
                    "repo_name": item["metadata"].get("repo_name"),
                    "file_path": item["metadata"].get("file_path"),
                    "original_url": item["metadata"].get("original_url"),
                    "retrieval_strategy": item["metadata"].get(
                        "retrieval_strategy"
                    ),
                    "split_group_id": item["metadata"].get("split_group_id"),
                    "near_duplicate_group_id": item["metadata"].get(
                        "near_duplicate_group_id"
                    ),
                },
                "release": {
                    "release_view_membership": item["metadata"].get(
                        "release_view_membership"
                    ),
                    "distribution_rights_status": item["metadata"].get(
                        "distribution_rights_status"
                    ),
                    "repo_license": item["metadata"].get("repo_license"),
                },
            }
            for item in short_selected
        ],
    )

    current_split = common.split_contract(split_manifest_path)
    expanded_pool = 734 + len(short_selected)
    minimum_train = math.ceil(0.70 * expanded_pool)
    artifacts = {
        "report_json": common.display_path(report_json_path),
        "report_markdown": common.display_path(report_md_path),
        "failed_check_combinations": common.display_path(combinations_path),
        "scientific_data_table": common.display_path(gradient_path),
        "public_validated_replay": common.display_path(replay_path),
        "public_validated_inventory": common.display_path(inventory_path),
        "short_code_candidates": common.display_path(selected_path),
        "short_code_candidate_source": common.display_path(
            selected_source_path
        ),
    }
    short_gate_counts = [
        int(item["metadata"]["gate_count"]) for item in short_selected
    ]
    short_qubits = [
        int(item["metadata"]["num_qubits"]) for item in short_selected
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "frozen_benchmark_changed": False,
            "manuscript_denominator_changed": False,
            "readiness_scores": [1, 2, 3, 4],
            "normalization": "presentation-only AST transformation",
            "interpretation": "readiness-gradient and release-view audit",
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
                "sha256": common.sha256_file(split_manifest_path),
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
        "readiness_contract": {
            "check_order": list(common.readiness.BENCHMARK_CHECK_ORDER_V2),
            "check_descriptions": dict(
                common.readiness.BENCHMARK_CHECK_DESCRIPTIONS_V2
            ),
            "minimum_code_lines": common.MIN_CODE_LINES,
            "minimum_gate_count": common.MIN_GATE_COUNT,
        },
        "lower_readiness": {
            "score_distribution_full_source": {
                str(score): count
                for score, count in sorted(score_distribution.items())
            },
            "by_score": {
                str(score): dict(by_score[score])
                for score in sorted(LOWER_SCORES)
            },
            "failed_check_combinations": {
                f"{score}/8 | {combination}": dict(counter)
                for (score, combination), counter in sorted(
                    by_combination.items(),
                    key=lambda item: (
                        item[0][0],
                        -item[1]["rows"],
                        item[0][1],
                    ),
                )
            },
            "validation_statuses": {
                str(score): dict(validation_statuses[score])
                for score in sorted(LOWER_SCORES)
            },
            "validation_errors": {
                str(score): dict(validation_errors[score])
                for score in sorted(LOWER_SCORES)
            },
            "aggregate": {
                **dict(aggregate),
                "validated_signature_percent": pct(
                    validated_signatures, aggregate_rows
                ),
                "non_identifiable_for_generation": (
                    aggregate_rows - validated_signatures
                ),
                "public_parseable_unvalidated": public_parseable_unvalidated,
            },
            "validated_public_replay": {
                "input_rows": len(public_validated),
                "normalization_success": len(normalized),
                "post_normalization_8_of_8": len(post_8),
                **replay_summary(normalized, "normalized_replay"),
            },
            "short_code_sensitivity": {
                "integrity_pass_rows": len(short_integrity),
                "novel_rows": len(short_novel),
                "signature_deduplicated_candidates": len(short_selected),
                "gate_type_bins": dict(
                    sorted(
                        Counter(
                            common.gate_type_bin(item["metadata"])
                            for item in short_selected
                        ).items()
                    )
                ),
                "gate_count_range": (
                    [min(short_gate_counts), max(short_gate_counts)]
                    if short_gate_counts
                    else None
                ),
                "qubit_range": (
                    [min(short_qubits), max(short_qubits)]
                    if short_qubits
                    else None
                ),
                "pool_increase_percent": pct(len(short_selected), 734),
                "existing_generation_facing_prompts": sum(
                    item.get("seed_role") in common.CLEAN_ROLES
                    for item in short_selected
                ),
                "source_groups": len(selected_split_groups),
                "near_duplicate_groups": len(selected_near_groups),
                "repositories": {
                    f"{owner}/{repo}": count
                    for (owner, repo), count in sorted(
                        Counter(
                            (
                                item["metadata"].get("repo_owner"),
                                item["metadata"].get("repo_name"),
                            )
                            for item in short_selected
                        ).items()
                    )
                },
            },
        },
        "cross_stratum_curation_context": {
            "7_of_8_short_code_comparator": {
                "selected_signatures": 28,
                "gate_type_bins": {"1-2": 19, "3-4": 9, "5+": 0},
                "source_report": common.display_path(
                    SUBMISSION_DIR
                    / "artifacts"
                    / "n6_cleanliness_expansion_audit"
                    / "pqid_n6_cleanliness_expansion_audit.json"
                ),
            },
            "6_of_8_public_path_clean_funnel": {
                "selected_signatures": 6,
                "gate_type_bins": {"1-2": 4, "3-4": 2, "5+": 0},
                "source_report": common.display_path(
                    SUBMISSION_DIR
                    / "artifacts"
                    / "n6_cleanliness_expansion_audit"
                    / "pqid_n6_cleanliness_expansion_audit.json"
                ),
            },
            "5_of_8_presentation_normalization": {
                "selected_signatures": 35,
                "gate_type_bins": {"1-2": 10, "3-4": 11, "5+": 14},
                "source_report": common.display_path(
                    SUBMISSION_DIR
                    / "artifacts"
                    / "n5_cleanliness_expansion_audit"
                    / "pqid_n5_cleanliness_expansion_audit.json"
                ),
            },
            "4_of_8_line_threshold_sensitivity": {
                "selected_signatures": len(short_selected),
                "gate_type_bins": dict(
                    sorted(
                        Counter(
                            common.gate_type_bin(item["metadata"])
                            for item in short_selected
                        ).items()
                    )
                ),
            },
            "3_of_8_to_1_of_8": {
                "selected_signatures_under_tested_deterministic_route": 0,
            },
            "additivity_warning": (
                "Candidate counts are not additive until cross-queue signature "
                "and lineage deduplication is performed."
            ),
        },
        "split_governance_if_short_code_rule_changed": {
            "current_pool_size": 734,
            "current_train": current_split["train"],
            "current_validation": current_split["validation"],
            "current_test": current_split["test"],
            "expanded_pool_size": expanded_pool,
            "training_floor": 0.70,
            "minimum_train_rows": minimum_train,
            "candidates_required_for_train": max(
                0, minimum_train - current_split["train"]
            ),
            "maximum_nontraining_additions": max(
                0,
                len(short_selected)
                - max(0, minimum_train - current_split["train"]),
            ),
        },
        "validation": {
            "all_passed": True,
            "checks_total": len(validation_checks),
            "checks": validation_checks,
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
    parser.add_argument(
        "--split-manifest", type=Path, default=DEFAULT_SPLIT_MANIFEST
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    payload = run(
        source_path=args.source,
        seed_path=args.seed_drafts,
        split_manifest_path=args.split_manifest,
        output_dir=args.output_dir,
    )
    aggregate = payload["lower_readiness"]["aggregate"]
    short = payload["lower_readiness"]["short_code_sensitivity"]
    print(f"Exact 1/8--4/8 rows: {aggregate['rows']:,}")
    print(
        "Validated complete signatures: "
        f"{aggregate['validated_signature_complete']:,}"
    )
    print(
        "Selected short-code sensitivity candidates: "
        f"{short['signature_deduplicated_candidates']:,}"
    )
    print(f"Report: {payload['artifacts']['report_markdown']}")


if __name__ == "__main__":
    main()
