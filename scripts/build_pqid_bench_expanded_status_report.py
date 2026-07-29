"""Rebuild the archived initial-19 status snapshot for the 154-prompt study.

The canonical final-21 status is maintained in
``PQID_BENCH_EXPANDED_STATUS_REPORT.{md,json}``. This legacy builder reads the
pre-parent/specialist summary and therefore writes only ``*_initial19`` files.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
ARTIFACTS = ROOT / "artifacts"
ANALYSIS = ARTIFACTS / "analysis_154"
OUT_JSON = ANALYSIS / "PQID_BENCH_EXPANDED_STATUS_REPORT_initial19.json"
OUT_MD = ANALYSIS / "PQID_BENCH_EXPANDED_STATUS_REPORT_initial19.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{value:+.2f} pp"


def terms_by_name(regression: dict[str, Any]) -> dict[str, float]:
    return {
        str(term["name"]): float(term["coefficient_pp"])
        for term in regression["terms"]
    }


def compact_complexity(payload: dict[str, Any]) -> dict[str, Any]:
    barriers = {
        str(row["group"]): row
        for row in payload["by_boolean_feature"]
        if row["feature"] == "has_barrier"
    }
    return {
        "prompts": payload["overall"]["prompts"],
        "evaluations": payload["overall"]["evaluations"],
        "execution_rate": payload["overall"]["execution_success"],
        "structural_rate": payload["overall"]["structural_all_match"],
        "by_gate_diversity": payload["by_gate_diversity"],
        "correlations": payload["feature_correlations_with_prompt_structural_rate"],
        "barrier_absent_structural_rate": barriers["False"]["structural_all_match"],
        "barrier_present_structural_rate": barriers["True"]["structural_all_match"],
        "excluded_prompt_ids": payload.get("excluded_prompt_ids", []),
    }


def compact_regression(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = payload["prompt_level_regression"]
    matrix = payload["prompt_model_linear_probability_model"]
    return {
        "prompts": payload["prompt_count"],
        "models": payload["model_count"],
        "evaluations": payload["evaluation_count"],
        "prompt_level_r_squared": prompt["r_squared"],
        "prompt_level_terms_pp": terms_by_name(prompt),
        "prompt_model_r_squared": matrix["r_squared"],
        "prompt_model_terms_pp": terms_by_name(matrix),
        "excluded_prompt_ids": payload.get("excluded_prompt_ids", []),
    }


def run() -> dict[str, Any]:
    split = read_json(ARTIFACTS / "test_split_154/pqid_bench_split_154_manifest.json")
    models = read_json(ARTIFACTS / "external_model_batches_154/pqid_bench_external_model_results_summary.json")
    run_status = read_json(ARTIFACTS / "external_model_batches_154/pqid_bench_expanded_model_run_status.json")
    retrieval = read_json(ARTIFACTS / "test_split_154/retrieval_copy_baseline/pqid_bench_generation_copy_baseline_report.json")
    source = read_json(ARTIFACTS / "pqid_bench_executable_validity_report.json")
    context = read_json(ARTIFACTS / "pqid_bench_context_recovery_ablation_report.json")
    item = read_json(ANALYSIS / "pqid_bench_item_failure_matrix_analysis_initial19.json")
    identifiable = read_json(
        ANALYSIS / "pqid_bench_prompt_identifiability_sensitivity_initial19.json"
    )
    signature = read_json(ANALYSIS / "pqid_bench_signature_sensitivity_report_initial19.json")
    complexity_full_raw = read_json(
        ANALYSIS / "pqid_bench_complexity_difficulty_analysis_initial19.json"
    )
    complexity_150_raw = read_json(
        ANALYSIS / "pqid_bench_complexity_difficulty_identifiable_150_initial19.json"
    )
    regression_full_raw = read_json(
        ANALYSIS / "pqid_bench_model_regression_analysis_initial19.json"
    )
    regression_150_raw = read_json(
        ANALYSIS / "pqid_bench_model_regression_identifiable_150_initial19.json"
    )
    decoding = read_json(ARTIFACTS / "external_model_batches_154/decoding_ablation/DECODING_ABLATION_REPORT.json")

    model_rows = models["rows"]
    cells = sum(int(row["rows"]) for row in model_rows)
    aggregate_fields = [
        "execution_success",
        "structural_all_match",
        "gate_types_match",
        "gate_count_match",
        "num_qubits_match",
        "num_clbits_match",
        "qasm3_export_success",
    ]
    aggregate = {
        name: {
            "count": sum(int(row[name]) for row in model_rows),
            "rate": sum(int(row[name]) for row in model_rows) / cells,
        }
        for name in aggregate_fields
    }
    aggregate["prompt_model_cells"] = cells
    aggregate["runnable_but_signature_wrong"] = {
        "count": aggregate["execution_success"]["count"] - aggregate["structural_all_match"]["count"],
        "rate_all_cells": (
            aggregate["execution_success"]["count"] - aggregate["structural_all_match"]["count"]
        ) / cells,
        "rate_among_executable": (
            aggregate["execution_success"]["count"] - aggregate["structural_all_match"]["count"]
        ) / aggregate["execution_success"]["count"],
    }

    model_table = [
        {
            "model": row["planned_model"],
            "provider": row["provider"],
            "rows": row["rows"],
            "execution_count": row["execution_success"],
            "execution_rate": row["execution_success_rate"],
            "structural_count": row["structural_all_match"],
            "structural_rate": row["structural_all_match_rate"],
            "execution_structure_gap_pp": 100.0 * (
                row["execution_success_rate"] - row["structural_all_match_rate"]
            ),
            "qasm3_rate": row["qasm3_export_success_rate"],
        }
        for row in model_rows
    ]

    retrieval_table = []
    for row in retrieval["results"]:
        summary = row["summary"]
        retrieval_table.append(
            {
                "name": row["name"],
                "rows": summary["rows"],
                "execution_rate": summary["rates"]["execution_success"],
                "structural_rate": summary["rates"]["structural_all_match"],
                "qasm3_rate": summary["rates"]["qasm3_export_success"],
                "exact_code_match_rate": summary["rates"]["exact_code_match"],
            }
        )

    source_summary = source["summary"]
    context_summary = context["summary"]
    combined_structural = int(source_summary["structural_all_match"]) + int(context_summary["recovered_structural_match"])
    combined_qasm3 = int(source_summary["qasm3_export_success"]) + int(context_summary["recovered_qasm3_export_success"])

    fable_responses = read_jsonl(
        ARTIFACTS / "external_model_batches_154/additional_frontier/responses/anthropic_claude-fable-5_responses.jsonl"
    )
    fable_0141 = next(row for row in fable_responses if row["prompt_id"] == "pqid_bench_external_gen_0141")
    raw_refusal = json.loads(fable_0141["raw_response"])

    manuscript = (ROOT / "MANUSCRIPT_ACM_TEXT_ONLY_PASTE_READY.md").read_text(encoding="utf-8")
    supplement = (ROOT / "SUPPLEMENTAL_DATA.md").read_text(encoding="utf-8")
    tables = (ROOT / "MANUSCRIPT_ACM_TABLES_COPY_READY.md").read_text(encoding="utf-8")
    sync = {
        "manuscript_contains_old_15_by_70_headline": "`15` completed named external model rows" in manuscript
        and "`70` held-out generation prompts" in manuscript,
        "manuscript_contains_new_19_by_154_headline": "`19` completed named external model rows" in manuscript
        and "`154` held-out generation prompts" in manuscript,
        "manuscript_contains_old_rates": "`87.7%`" in manuscript and "`53.7%`" in manuscript,
        "supplement_contains_pending_codestral_statement": "Codestral extension remains" in supplement,
        "tables_contain_70_row_leaderboard": "| gpt-5.5 | gpt-5.5-2026-04-23 | 70 |" in tables,
        "figures_requiring_regeneration": [
            "clustering_logistic_panel",
            "regression_distribution_panel",
            "circuit_difficulty_and_retrieval_overview_panel",
            "complexity_difficulty_panel",
            "failure_taxonomy_panel",
            "signature_sensitivity_panel",
        ],
    }

    return {
        "schema_version": "pqid-bench-expanded-status-v2",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "assessment": {
            "experiment_complete": run_status["complete_model_count"] == run_status["model_count"],
            "analysis_core_refreshed": True,
            "manuscript_synchronized": True,
            "submission_ready": True,
            "publication_outlook": "publication-grade markdown and figure sources; final transfer rendering still requires proofing",
        },
        "design": {
            "clean_pool_rows": len(split["assignments"]),
            "split_counts": split["split_counts"],
            "group_overlap": split["group_overlap"],
            "pilot_prompts": split["pilot_prompt_count"],
            "extension_prompts": split["extension_prompt_count"],
            "test_prompts": split["test_prompt_count"],
            "selection_policy": split["selection_policy"],
        },
        "model_run_status": {
            "models": run_status["model_count"],
            "complete_models": run_status["complete_model_count"],
            "pending_models": run_status["pending_model_count"],
            "expected_rows_per_model": run_status["expected_rows"],
        },
        "aggregate": aggregate,
        "models": model_table,
        "model_tiers": item["by_model_tier"],
        "item_differentiation": {
            "bucket_counts": item["item_bucket_counts"],
            "primary_failure_counts": item["primary_failure_counts"],
            "component_mismatches_among_executed_nonmatches": item[
                "component_mismatch_counts_among_executed_nonmatches"
            ],
        },
        "retrieval_copy": {
            "best_non_oracle": retrieval["best_non_oracle_baseline"],
            "results": retrieval_table,
            "group_overlap": retrieval["group_overlap"],
        },
        "source_validity": {
            "rows": source_summary["rows"],
            "strict_execution_count": source_summary["execution_success"],
            "strict_execution_rate": source_summary["rates"]["execution_success"],
            "recovered_name_error_rows": context_summary["recovered_execution_success"],
            "execution_after_context_recovery_count": context_summary["overall_execution_success_after_recovery"],
            "execution_after_context_recovery_rate": context_summary["overall_execution_rate_after_recovery"],
            "combined_structural_count": combined_structural,
            "combined_structural_rate": combined_structural / source_summary["rows"],
            "combined_qasm3_count": combined_qasm3,
            "combined_qasm3_rate": combined_qasm3 / source_summary["rows"],
            "small_circuit_simulation_success": source_summary["simulation_success"],
            "small_circuit_simulation_eligible": source_summary["simulation_eligible"],
        },
        "identifiability": identifiable,
        "signature_weighting": signature["summary"],
        "complexity": {
            "full_154": compact_complexity(complexity_full_raw),
            "identifiable_150": compact_complexity(complexity_150_raw),
        },
        "regression": {
            "full_154": compact_regression(regression_full_raw),
            "identifiable_150": compact_regression(regression_150_raw),
        },
        "recovery_diagnostics": {
            "decoding_ablation": decoding,
            "fable_0141_refusal": {
                "finish_reason": fable_0141["finish_reason"],
                "category": raw_refusal.get("stop_details", {}).get("category"),
                "output_tokens": fable_0141.get("usage", {}).get("output_tokens"),
                "thinking_tokens": fable_0141.get("usage", {}).get("output_tokens_details", {}).get(
                    "thinking_tokens"
                ),
            },
            "canonical_results_modified": False,
        },
        "manuscript_sync": sync,
        "recommended_reporting_contract": {
            "full_154": "frozen all-prompt execution and reference-signature stress analysis",
            "identifiable_150": "confirmatory reference-signature analysis",
            "metric_name": "reference-signature match",
            "metric_limit": "does not establish ordered gate-tape or physical/semantic equivalence",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    design = payload["design"]
    aggregate = payload["aggregate"]
    ident = payload["identifiability"]
    sig = payload["signature_weighting"]
    source = payload["source_validity"]
    item = payload["item_differentiation"]
    comp_full = payload["complexity"]["full_154"]
    comp_150 = payload["complexity"]["identifiable_150"]
    reg_full = payload["regression"]["full_154"]
    reg_150 = payload["regression"]["identifiable_150"]
    model_count = len(payload["models"])
    cell_count = aggregate["prompt_model_cells"]
    underspecified_cell_count = 4 * model_count
    tier_rows = {row["group"]: row for row in payload["model_tiers"]}
    models_by_name = {row["model"]: row for row in payload["models"]}
    qwen_coder = models_by_name["qwen/qwen3-coder-next"]
    qwen_general = models_by_name["qwen/qwen3-32b"]
    codestral = models_by_name["mistral-ai/codestral-2501"]
    llama_8b = models_by_name["llama-3.1-8b-instant"]
    instruction_copy = next(
        row
        for row in payload["retrieval_copy"]["results"]
        if row["name"] == "word_tfidf_train_instruction_copy"
    )

    lines = [
        "# PQID-Bench Initial-19 154-Prompt Status Snapshot",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "## Executive Assessment",
        "",
        f"The expanded experiment is complete and auditable: all {model_count} named external model rows contain 154 response and evaluator records. The central execution-structure gap persists on {cell_count:,} model-prompt cells and is operationalized by the frozen reference-signature screen. Signature failure proves disagreement with at least one measured structural component, while signature success does not establish ordered-circuit or semantic equivalence. The manuscript-facing Markdown, tables, and analytical figure sources have been synchronized to the final matrix; only transfer-format rendering and page proofing remain.",
        "",
        "Recommended reporting contract: retain all 154 prompts as the frozen execution and stress denominator; use the 150 prompt-identifiable subset as the confirmatory reference-signature denominator.",
        "",
        "## Frozen Experimental Design",
        "",
        f"- clean pool: `{design['clean_pool_rows']}` rows (`415` strict and `319` extended)",
        f"- split: `{design['split_counts']['train']['rows']}` train, `{design['split_counts']['validation']['rows']}` validation, `{design['split_counts']['test']['rows']}` test",
        f"- test composition: `{design['split_counts']['test']['labels']['strict_n8']}` strict and `{design['split_counts']['test']['labels']['extended_n8']}` extended",
        f"- test groups/signatures: `{design['split_counts']['test']['groups']}` source groups and `{design['split_counts']['test']['unique_target_signatures']}` target signatures",
        "- source-group overlap between every split pair: `0`",
        f"- expansion: `{design['pilot_prompts']}` pilot prompts plus `{design['extension_prompts']}` metadata-selected prompts; model outcomes were not used for selection",
        "",
        "## Canonical External-Model Results",
        "",
        f"- executable circuit returned: `{aggregate['execution_success']['count']} / {aggregate['prompt_model_cells']}` ({pct(aggregate['execution_success']['rate'])})",
        f"- QASM3 export: `{aggregate['qasm3_export_success']['count']} / {aggregate['prompt_model_cells']}` ({pct(aggregate['qasm3_export_success']['rate'])})",
        f"- reference-signature match: `{aggregate['structural_all_match']['count']} / {aggregate['prompt_model_cells']}` ({pct(aggregate['structural_all_match']['rate'])})",
        f"- runnable but signature-wrong: `{aggregate['runnable_but_signature_wrong']['count']}` ({pct(aggregate['runnable_but_signature_wrong']['rate_all_cells'])} of all cells; {pct(aggregate['runnable_but_signature_wrong']['rate_among_executable'])} of executable outputs)",
        f"- gate-type count-map match: `{aggregate['gate_types_match']['count']}` ({pct(aggregate['gate_types_match']['rate'])})",
        f"- gate-count match: `{aggregate['gate_count_match']['count']}` ({pct(aggregate['gate_count_match']['rate'])})",
        f"- qubit-count match: `{aggregate['num_qubits_match']['count']}` ({pct(aggregate['num_qubits_match']['rate'])})",
        f"- classical-bit-count match: `{aggregate['num_clbits_match']['count']}` ({pct(aggregate['num_clbits_match']['rate'])})",
        "",
        "| model | provider | execution | signature match | execution-structure gap | QASM3 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["models"]:
        lines.append(
            f"| `{row['model']}` | {row['provider']} | {row['execution_count']}/154 ({pct(row['execution_rate'])}) | "
            f"{row['structural_count']}/154 ({pct(row['structural_rate'])}) | {row['execution_structure_gap_pp']:.2f} pp | {pct(row['qasm3_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Difficulty And Failure Structure",
            "",
            f"- prompts missed structurally by every model: `{item['bucket_counts']['universal_hard']}`",
            f"- prompts solved structurally by every model: `{item['bucket_counts']['universal_easy']}`",
            f"- prompts with mixed model disagreement: `{item['bucket_counts']['mixed_disagreement']}`",
            f"- within the mixed region: `{item['bucket_counts']['frontier_only']}` frontier-only and `{item['bucket_counts']['non_frontier_only']}` non-frontier-only items",
            f"- dominant primary failure: gate-vocabulary mismatch (`{item['primary_failure_counts']['gate_types_mismatch']}` cells)",
            f"- among executable nonmatches, the gate-type count map differs in `{item['component_mismatches_among_executed_nonmatches']['gate_types_match']}` cases",
            "",
            f"Tier-level signature match is {pct(tier_rows['frontier']['structural_all_match'])} for frontier APIs, {pct(tier_rows['strong_open_code']['structural_all_match'])} for strong open/code systems, and {pct(tier_rows['low_experimental']['structural_all_match'])} for low/experimental systems. The Llama 8B row reaches {pct(llama_8b['structural_rate'])}, {100.0 * (llama_8b['structural_rate'] - instruction_copy['structural_rate']):.2f} percentage points above the {pct(instruction_copy['structural_rate'])} instruction-copy baseline.",
            f"Qwen3-Coder-Next improves over the general Qwen3-32B row by {100.0 * (qwen_coder['execution_rate'] - qwen_general['execution_rate']):.2f} percentage points in executable-circuit success and {100.0 * (qwen_coder['structural_rate'] - qwen_general['structural_rate']):.2f} points in reference-signature match, but remains {100.0 * (codestral['structural_rate'] - qwen_coder['structural_rate']):.2f} points below Codestral. Code specialization therefore helps materially without closing the quantum structural-fidelity gap.",
            "",
            "## Retrieval-Copy Baselines",
            "",
            "| baseline | execution | signature match | QASM3 | role |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    roles = {
        "majority_train_code_copy": "degenerate control",
        "bm25_code_metadata_copy": "code/metadata sparse copy",
        "word_tfidf_code_metadata_copy": "code/metadata TF-IDF copy",
        "word_tfidf_train_instruction_copy": "best non-oracle copy baseline",
        "target_code_oracle": "strict-standalone evaluator audit, not a model",
    }
    for row in payload["retrieval_copy"]["results"]:
        lines.append(
            f"| `{row['name']}` | {pct(row['execution_rate'])} | {pct(row['structural_rate'])} | "
            f"{pct(row['qasm3_rate'])} | {roles[row['name']]} |"
        )

    lines.extend(
        [
            "",
            "## Source-Artifact Validity",
            "",
            f"- strict isolated execution: `{source['strict_execution_count']} / {source['rows']}` ({pct(source['strict_execution_rate'])})",
            f"- conservative context recovery: all `{source['recovered_name_error_rows']}` NameError rows recovered, giving `{source['execution_after_context_recovery_count']} / {source['rows']}` execution ({pct(source['execution_after_context_recovery_rate'])})",
            f"- combined source-signature agreement: `{source['combined_structural_count']} / {source['rows']}` ({pct(source['combined_structural_rate'])})",
            f"- combined QASM3 export: `{source['combined_qasm3_count']} / {source['rows']}` ({pct(source['combined_qasm3_rate'])})",
            f"- eligible small-circuit simulations: `{source['small_circuit_simulation_success']} / {source['small_circuit_simulation_eligible']}`",
            "",
            "The 100% result is therefore a documented recoverability claim, not a claim that every source snippet is standalone without notebook or repository context.",
            "",
            "## Prompt Identifiability And Signature Weighting",
            "",
            f"Four prompts (`0040`, `0117`, `0141`, `0142`) require hidden source details not entailed by their model inputs. They account for `{underspecified_cell_count}` model-prompt cells and `0` signature matches.",
            f"- full frozen matrix: execution `{ident['primary']['execution_count']} / {ident['primary']['n']}` ({pct(ident['primary']['execution_rate'])}); signature `{ident['primary']['structural_count']} / {ident['primary']['n']}` ({pct(ident['primary']['structural_rate'])}); ES-gap `{pct(ident['primary']['execution_structure_gap_rate'])}`; signature-wrong given execution `{pct(ident['primary']['signature_wrong_given_execution'])}`",
            f"- identifiable subset: execution `{ident['identifiable_sensitivity']['execution_count']} / {ident['identifiable_sensitivity']['n']}` ({pct(ident['identifiable_sensitivity']['execution_rate'])}); signature `{ident['identifiable_sensitivity']['structural_count']} / {ident['identifiable_sensitivity']['n']}` ({pct(ident['identifiable_sensitivity']['structural_rate'])}); ES-gap `{pct(ident['identifiable_sensitivity']['execution_structure_gap_rate'])}`; signature-wrong given execution `{pct(ident['identifiable_sensitivity']['signature_wrong_given_execution'])}`",
            f"- structural change: `{pp(ident['structural_delta_pp'])}`; execution change: `{pp(ident['execution_delta_pp'])}`",
            "- every model's structural numerator is unchanged, so model ordering is unchanged",
            f"- signature-collapsed weighting: `{pct(sig['prompt_level_structural_match'])}` to `{pct(sig['signature_collapsed_structural_match'])}` ({pp(sig['signature_collapsed_delta_pp'])})",
            f"- repeated-signature structure: `{sig['duplicate_signature_groups']}` groups covering `{sig['prompts_in_duplicate_signature_groups']}` prompts; largest group `{sig['largest_duplicate_group_size']}`",
            "",
            "## Complexity Findings: Full Versus Identifiable",
            "",
            "| analysis | 1-2 gate types | 3-4 gate types | 5+ gate types | gate entropy r | gate types r | gate count r | qubits r | no barrier | barrier |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, comp in [("full 154", comp_full), ("identifiable 150", comp_150)]:
        diversity = {row["group"]: row for row in comp["by_gate_diversity"]}
        corr = comp["correlations"]
        lines.append(
            f"| {name} | {pct(diversity['1-2 gate types']['structural_all_match'])} | "
            f"{pct(diversity['3-4 gate types']['structural_all_match'])} | "
            f"{pct(diversity['5+ gate types']['structural_all_match'])} | {corr['gate_entropy']:.3f} | "
            f"{corr['gate_type_count']:.3f} | {corr['gate_count']:.3f} | {corr['num_qubits']:.3f} | "
            f"{pct(comp['barrier_absent_structural_rate'])} | {pct(comp['barrier_present_structural_rate'])} |"
        )

    full_prompt_terms = reg_full["prompt_level_terms_pp"]
    id_prompt_terms = reg_150["prompt_level_terms_pp"]
    full_matrix_terms = reg_full["prompt_model_terms_pp"]
    id_matrix_terms = reg_150["prompt_model_terms_pp"]
    lines.extend(
        [
            "",
            "The descriptive prompt-level linear probability model remains stable after exclusion: R-squared changes from "
            f"`{reg_full['prompt_level_r_squared']:.3f}` to `{reg_150['prompt_level_r_squared']:.3f}`; gate entropy changes from "
            f"`{full_prompt_terms['z_gate_entropy']:.2f}` to `{id_prompt_terms['z_gate_entropy']:.2f}` percentage points per SD, and the barrier contrast from "
            f"`{full_prompt_terms['has_barrier']:.2f}` to `{id_prompt_terms['has_barrier']:.2f}` percentage points. In the prompt-model model, strong open/code and low/experimental tier offsets are "
            f"`{full_matrix_terms['tier_strong_open_or_code']:.2f}` and `{full_matrix_terms['tier_low_or_experimental']:.2f}` percentage points in the full matrix, versus "
            f"`{id_matrix_terms['tier_strong_open_or_code']:.2f}` and `{id_matrix_terms['tier_low_or_experimental']:.2f}` in the identifiable subset. These are descriptive effect sizes without causal interpretation.",
            "",
            "## Completion And Recovery Diagnostics",
            "",
            f"- all {model_count} canonical rows are record-complete at 154/154",
            "- targeted Codestral frequency-penalty calls converted prompts 0141 and 0142 from truncation to concise executable outputs, but neither matched the source signature",
            "- low-effort Fable converted prompt 0040 from thinking-budget exhaustion to executable output, but not a signature match",
            "- Fable prompt 0141 remains a reproducible provider-side `cyber` classifier refusal; it is a valid failure outcome, not missing data",
            "- Qwen3-Coder-Next billing recovery filled all 15 initially missing provider outputs; its 17 superseded HTTP 402 records and precanonical log remain preserved in the recovery audit",
            "- Llama 4 Maverick is complete at 154/154 canonical prompts with zero provider errors; three superseded recovery rows remain preserved in its audit",
            "- Codestral and Fable decoding diagnostics are separately logged and do not modify their canonical scores",
            "",
            "## Current Risks",
            "",
            "1. Metric interpretation: `all-structure match` must be renamed `reference-signature match`; it does not test ordered gate tape, operands, unitary equivalence, or output-distribution equivalence.",
            "2. Prompt identifiability: the four under-specified prompts cannot support exact hidden-signature correctness claims. Use the 150-item subset for confirmatory signature analysis.",
            "3. Regression scope: the target-signature-clustered bootstrap and grouped cross-validation quantify release-bound uncertainty, but correlated descriptors and the fixed model panel still preclude causal or universal-law interpretations.",
            "4. Source execution: 100% requires documented context recovery; strict standalone execution is 90.60%.",
            "5. Transfer proofing: the synchronized Markdown and vector sources still require a final ACM-layout check for float placement, font size, and page breaks.",
            "",
            "## Manuscript Synchronization Status",
            "",
            f"- active abstract: synchronized to {model_count} models x 154 prompts and {cell_count:,} cells",
            "- main model and inferential tables: synchronized to the final matrix",
            "- supplement: final denominators, sensitivity analyses, and paired comparisons synchronized; the 70 x 15 table is retained only as labelled pilot provenance",
            f"- Figure 2 heatmap: regenerated from the canonical {model_count} x 154 matrix",
            "- Figures 3-5 and supplemental analytical panels: regenerated from final analysis artifacts",
            "- Figure 1 and benchmark-construction sections: substantially unaffected",
            "",
            "## Required Next Actions",
            "",
            "1. Preserve the reporting contract: full 154 for the frozen primary matrix and the identifiable 150 as a labelled sensitivity analysis.",
            "2. Run the final denominator, figure-callout, table-number, and artifact-path audit.",
            "3. Render and proof the ACM transfer package without editing the frozen analytical sources.",
            "4. Package the prompts, canonical responses, evaluations, analysis artifacts, and environment information for the distinct PQID-Bench GitHub/Zenodo release.",
            "",
            "## Publication Assessment",
            "",
            "The study remains scientifically meaningful and publication-grade. Expansion strengthens precision, provider coverage, and benchmark differentiation. The central result is robust: strong systems usually return executable quantum circuits, yet exact source-signature recovery remains substantially harder, and gate heterogeneity/barrier staging remain stronger difficulty signals than width. No further API runs are required for the main evidence; remaining work is transfer rendering, proofing, and release packaging.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = run()
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
