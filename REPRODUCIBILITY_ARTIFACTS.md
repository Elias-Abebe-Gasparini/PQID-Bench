# PQID-Bench Reproducibility Artifacts

This is the exhaustive path-level inventory that accompanies the benchmark
study. It is intentionally detailed and is not the ecosystem front door.
Begin with the [local repository README](README.md) for the appropriate
ecosystem or package entry point. Use this file when a reviewer or maintainer
needs to locate the exact script, trace, report, table, or figure behind a
claim.

## Artifact Principles

Each experiment should be traceable through:

- a script or notebook entry point;
- the input population and split policy;
- excluded leakage features or target metadata;
- generated Markdown/JSON/CSV reports;
- raw model responses where an external provider is used;
- figure builders for manuscript panels.

## Core Scripts

| artifact | path |
| --- | --- |
| packaging and sanity report script | `PQID/scripts/05_benchmarking/build_pqid_bench_tables.py` |
| learned readiness baseline script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_readiness_baseline.py` |
| retrieval baseline script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_retrieval_baseline.py` |
| TF-IDF retrieval strengthening script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_tfidf_retrieval_baseline.py` |
| retrieval-copy generation script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_generation_copy_baseline.py` |
| retrieval-copy complementarity trace script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_retrieval_copy_complementarity.py` |
| external-model generation harness script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_external_model_generation_harness.py` |
| external-model traceability batch script | `PQID/submissions/acm_tqc_benchmark/scripts/export_pqid_bench_external_model_batches.py` |
| OpenAI Batch request export script | `PQID/submissions/acm_tqc_benchmark/scripts/export_pqid_bench_openai_batch_requests.py` |
| OpenAI Batch job script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_openai_batch_job.py` |
| OpenAI Batch materialization script | `PQID/submissions/acm_tqc_benchmark/scripts/materialize_pqid_bench_openai_batch_responses.py` |
| OpenAI-compatible chat runner | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_openai_compatible_chat.py` |
| Gemini API runner | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_gemini_generate_content.py` |
| Anthropic Messages API runner | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_anthropic_messages.py` |
| external-model results summary script | `PQID/submissions/acm_tqc_benchmark/scripts/summarize_pqid_bench_external_model_results.py` |
| complexity-difficulty analysis script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_complexity_difficulty.py` |
| statistical diminishing-returns analysis script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_statistical_diminishing_returns.py` |
| model regression and distribution analysis script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_model_regression.py` |
| hierarchical clustering and logistic-regression diagnostic script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_clustering_logistic.py` |
| cluster-aware inferential analysis script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_inferential.py` |
| replication, crossed-bootstrap, family-balance, and developer-sensitivity script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_robustness_suite.py` |
| operational assembly-layer and pointwise-nesting audit script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_operational_assembly_layer.py` |
| ordered and operand-aware signature-validation script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_ordered_operand_validation.py` |
| versioned safe-built-in evaluator correction audit script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_evaluator_builtin_correction.py` |
| stochastic-repeatability analyzer | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_stochastic_repeatability.py` |
| stochastic-repeatability invariant tests | `PQID/submissions/acm_tqc_benchmark/scripts/test_pqid_bench_stochastic_repeatability.py` |
| item difficulty and failure-matrix script | `PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_item_failure_matrix.py` |
| result-panel figure builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_pqid_bench_result_panels.py` |
| diagnostic-panel figure builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_pqid_bench_diagnostic_panels.py` |
| compatibility entry point for the cluster-aware task-feature panel | `PQID/submissions/acm_tqc_benchmark/scripts/build_pqid_bench_regression_panels.py` |
| main-text model-profile and inferential figure builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_pqid_bench_inferential_figures.py` |
| retrieval-copy complementarity circuit-panel builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_retrieval_copy_complementarity_circuit_panel.py` |
| mutation-stress detection script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_mutation_stress_baseline.py` |
| executable-validity check script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_executable_validity_check.py` |
| context-recovery ablation script | `PQID/submissions/acm_tqc_benchmark/scripts/run_pqid_bench_context_recovery_ablation.py` |
| clean vs mutation-stress schematic script | `PQID/submissions/acm_tqc_benchmark/scripts/build_clean_vs_mutation_stress_schematic.py` |
| execution-to-structure validation-ladder builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_execution_structure_validation_ladder.py` |
| public-release synchronizer, privacy scanner, manifest, and archive builder | `PQID/submissions/acm_tqc_benchmark/scripts/build_pqid_bench_public_release.py` |
| installable reproducibility and live-evaluation package | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/src/pqid_bench/` |
| governed OpenAI-compatible live-model collector | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/src/pqid_bench/live.py` |
| isolated replay and canonical-summary adapter | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/src/pqid_bench/replay.py` |
| package and command metadata | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/pyproject.toml` |
| versioned machine-readable schemas | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/src/pqid_bench/schemas/` |
| isolated executable-replay worker | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/docker/evaluator/` |
| unit, integration, and exhaustive release-parity tests | `PQID/submissions/acm_tqc_benchmark/PQID-Bench/tests/` |

## Runbooks And Plans

| artifact | path |
| --- | --- |
| external-model evaluation plan | `PQID/submissions/acm_tqc_benchmark/MODEL_EVAL_PLAN.md` |
| OpenAI Batch runbook | `PQID/submissions/acm_tqc_benchmark/OPENAI_BATCH_RUNBOOK.md` |
| Groq/open-model API runbook | `PQID/submissions/acm_tqc_benchmark/GROQ_AND_OPEN_MODEL_API_RUNBOOK.md` |
| Hugging Face hosted open-model runbook | `PQID/submissions/acm_tqc_benchmark/HF_HOSTED_OPEN_MODEL_RUNBOOK.md` |
| non-HF hosted open-model route memo | `PQID/submissions/acm_tqc_benchmark/OPEN_MODEL_ALTERNATIVE_ROUTES.md` |
| GitHub Models and DeepInfra access runbook | `PQID/submissions/acm_tqc_benchmark/GITHUB_AND_DEEPINFRA_ACCESS_RUNBOOK.md` |
| stochastic-repeatability protocol | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x36/PRESPECIFIED_PROTOCOL.md` |
| stochastic-repeatability protocol amendments | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x36/PROTOCOL_AMENDMENTS.md` |
| stochastic-repeatability runbook | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x36/RUN_STOCHASTIC_REPEATABILITY.md` |
| stochastic-repeatability augmentation protocol | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/PRESPECIFIED_AUGMENTATION_PROTOCOL.md` |
| stochastic-repeatability immutable pretransmission bundle | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/preregistration_bundle_20260716_pretransmission/` |
| stochastic-repeatability pooled consolidation manifest | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/pqid_bench_stochastic_repeatability_consolidation_manifest.json` |
| prospectively registered PQID-Bench 2 Stage 1 semantic-validity and family-contrast plan (not analyzed on current data; DOI `10.17605/OSF.IO/WDERQ`) | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_2_prereg.json` |
| PQID-Bench 2 public OSF Stage 1 registration receipt | `PQID/submissions/acm_tqc_benchmark/artifacts/PQID_BENCH_2_OSF_STAGE_1_RECEIPT.json` |

## Reports And Derived Tables

| artifact | path |
| --- | --- |
| packaging and sanity report | `PQID/data/processed/pqid_bench_tables/pqid_bench_readiness_and_packaging_report.md` |
| learned baseline report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_readiness_learned_baseline_report.md` |
| retrieval baseline report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_retrieval_baseline_report.md` |
| TF-IDF retrieval strengthening report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_tfidf_retrieval_baseline_report.md` |
| retrieval-copy generation report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_generation_copy_baseline_report.md` |
| retrieval-copy complementarity trace | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_retrieval_copy_complementarity_cases.md` |
| external-model generation harness report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_external_model_generation_harness_report.md` |
| external-model held-out prompts | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_external_generation_prompts.jsonl` |
| external-model response template | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_external_generation_response_template.jsonl` |
| external-model run matrix | `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/external_model_run_matrix.md` |
| external-model traceability manifest | `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/manifests/external_model_traceability_manifest.md` |
| OpenAI Batch request manifest | `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/openai_batch/openai_batch_request_manifest.md` |
| external-model results summary | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_external_model_results_summary.md` |
| complexity-difficulty analysis report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_complexity_difficulty_analysis.md` |
| statistical diminishing-returns report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_statistical_diminishing_returns.md` |
| model regression and distribution report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_model_regression_analysis.md` |
| hierarchical clustering and logistic-regression report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_clustering_logistic_analysis.md` |
| cluster-aware inferential report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_inferential_analysis.md` |
| cluster-aware model-term grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_inferential_model_terms.csv` |
| signature-grouped cross-validation grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_grouped_cross_validation.csv` |
| paired model-comparison grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_paired_model_comparisons.csv` |
| rank-stability grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_rank_stability.csv` |
| versioned evaluator built-in correction audit | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/evaluator_builtin_correction/evaluator_builtin_correction_report.md` |
| evaluator correction machine-readable report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/evaluator_builtin_correction/evaluator_builtin_correction_report.json` |
| evaluator correction cell-level transition audit | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/evaluator_builtin_correction/evaluator_builtin_correction_cell_audit.jsonl` |
| stochastic-repeatability report | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/PQID_BENCH_STOCHASTIC_REPEATABILITY_REPORT.md` |
| stochastic-repeatability machine-readable analysis | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_analysis.json` |
| stochastic-repeatability cell outcomes | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_cell_outcomes.csv` |
| stochastic-repeatability per-model summary | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_model_summary.csv` |
| stochastic-repeatability provenance manifest | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_file_manifest.json` |
| canonical manuscript-input SHA-256 manifest | `PQID/submissions/acm_tqc_benchmark/artifacts/stochastic_repeatability_21x72/consolidated/analysis/CANONICAL_MANUSCRIPT_INPUT_SHA256.json` |
| Qiskit-specialist evaluation report | `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches_154/qiskit_mistral/evaluations/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai/pqid_bench_external_model_generation_harness_report.md` |
| exact Mistral-parent evaluation report | `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches_154/mistral_parent_control/evaluations/openrouter_mistralai_mistral-small-3_2-24b-instruct/pqid_bench_external_model_generation_harness_report.md` |
| Qiskit specialist versus exact-parent paired analysis | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/qiskit_specialist_parent_comparison.md` |
| final 21-model model-by-prompt matrix | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv` |
| final 21-model item and failure report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_item_failure_matrix_analysis.md` |
| final 21-model complexity report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_complexity_difficulty_analysis.md` |
| final 21-model clustering report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_clustering_logistic_analysis.md` |
| final 21-model inferential report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_inferential_analysis.md` |
| pilot-extension, crossed, family, and developer robustness report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_replication_crossed_family_vendor_robustness.md` |
| pilot-extension per-model grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_pilot_extension_per_model.csv` |
| family and developer sensitivity grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_family_vendor_sensitivity.csv` |
| operational assembly-layer audit report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_operational_assembly_layer_audit.md` |
| operational assembly-layer machine-readable audit | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_operational_assembly_layer_audit.json` |
| ordered and operand-aware signature-validation report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_validation.md` |
| ordered/operand cell-level replay audit | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_cell_audit.jsonl` |
| ordered/operand per-model grid | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_by_model.csv` |
| final 21-model signature sensitivity report | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_signature_sensitivity_report.md` |
| final 21-model retrieval complementarity trace | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_retrieval_copy_complementarity_cases.md` |
| initial-19 roster sensitivity artifacts | `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/*_initial19.*` |
| mutation-stress detection report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_mutation_stress_baseline_report.md` |
| executable-validity report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_executable_validity_report.md` |
| context-recovery ablation report | `PQID/submissions/acm_tqc_benchmark/artifacts/pqid_bench_context_recovery_ablation_report.md` |

## External-Model Traceability

External-provider runs are organized under:

- `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/requests/`
- `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/responses/`
- `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/raw_outputs/`
- `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/evaluations/`
- `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches/manifests/`

Each completed response file records provider/model identifiers, request hashes,
prompt record hashes, generated code, raw response payloads where retained, and
per-run configuration fields.

For new replication runs, `pqid-bench run-model` writes the same scientific
chain as a portable run directory: `run-manifest.json`, credential-free
`requests.jsonl`, canonical `responses.jsonl`, `provider-attempts.jsonl`,
per-prompt state records, hashed raw provider payloads, and
`run-summary.json`. Credentials and evaluator-only target metadata are never
written to that directory. `pqid-bench replay` consumes the canonical response
file inside the network-disabled evaluator and additionally materializes
canonical evaluation cells plus JSON, text, Markdown, and CSV summaries for
`evaluate` and `compare`.

## Publication-Output Regeneration

The public release retains the numerical inputs and generation scripts needed
to recreate publication figures and copy tables, but intentionally excludes
the rendered outputs, captions, editable authoring sources, copy-ready tables,
and manuscript-specific walkthrough notebook. This keeps the scientific
evidence reproducible without distributing submission products.

The relevant builders remain under
`PQID/submissions/acm_tqc_benchmark/scripts/`, including
`build_clean_vs_mutation_stress_schematic.py`,
`build_pqid_bench_result_panels.py`,
`build_pqid_bench_inferential_figures.py`,
`build_pqid_bench_diagnostic_panels.py`,
`build_supplemental_method_expansion_figures.py`, and
`build_pqid_bench_stochastic_repeatability_panel.py`. They regenerate outputs
locally from the frozen artifacts. Generated `figures/` and
`tables_copy_ready/` directories are outside the public release allowlist.

## Frozen Public-Release Object

The standalone `PQID-Bench/` directory is the canonical upload source for the
benchmark's GitHub, Zenodo, and Hugging Face releases. It is distinct from the
immutable PQID v1.0.2 dataset object.

| public artifact | package-relative path |
| --- | --- |
| repository-cleared clean generation population | `data/pqid_bench_clean_generation_734.jsonl` |
| frozen split and model-facing prompts | `artifacts/test_split_154/` |
| canonical 21-model requests, responses, and evaluator reports | `artifacts/external_model_batches_154/` |
| final 154-prompt analyses | `artifacts/analysis_154/` |
| consolidated 72-prompt, three-run repeatability audit | `artifacts/stochastic_repeatability_21x72/consolidated/` |
| public-safe preregistration projection | `artifacts/stochastic_repeatability_21x72/preregistration_bundle_20260716_pretransmission/` |
| publication-output regeneration code | `scripts/` and `docs/REGENERATING_PUBLICATION_OUTPUTS.md` |
| Hugging Face dataset card | `HUGGINGFACE_DATASET_CARD.md` |
| Zenodo metadata | `.zenodo.json` and `ZENODO_METADATA.md` |
| complete byte/hash inventory | `ARTIFACT_MANIFEST.tsv` |

Unpublished manuscript source is intentionally excluded from this standalone
release object. The v1.0.0 release-scope correction and clean-history
verification are recorded in
`PQID/submissions/acm_tqc_benchmark/ecosystem/RELEASE_SCOPE_INCIDENT_2026-07-29.md`.

The public preregistration projection omits only copied launchers and transcript
lines that exposed machine-local paths. It retains the original bundle
manifest and checksums, all scientific contracts, panels, protocols, requests,
and the pretransmission empty-output assertion. The package-level
`PUBLIC_RELEASE_NOTE.md` records this privacy-only projection explicitly.
