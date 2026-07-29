# PQID-Bench Initial-19 154-Prompt Status Snapshot

Generated: `2026-07-14T17:16:22+00:00`

## Executive Assessment

The expanded experiment is complete and auditable: all 19 named external model rows contain 154 response and evaluator records. The central execution-structure gap persists on 2,926 model-prompt cells and is operationalized by the frozen reference-signature screen. Signature failure proves disagreement with at least one measured structural component, while signature success does not establish ordered-circuit or semantic equivalence. The manuscript-facing Markdown, tables, and analytical figure sources have been synchronized to the final matrix; only transfer-format rendering and page proofing remain.

Recommended reporting contract: retain all 154 prompts as the frozen execution and stress denominator; use the 150 prompt-identifiable subset as the confirmatory reference-signature denominator.

## Frozen Experimental Design

- clean pool: `734` rows (`415` strict and `319` extended)
- split: `514` train, `66` validation, `154` test
- test composition: `77` strict and `77` extended
- test groups/signatures: `143` source groups and `144` target signatures
- source-group overlap between every split pair: `0`
- expansion: `70` pilot prompts plus `84` metadata-selected prompts; model outcomes were not used for selection

## Canonical External-Model Results

- executable circuit returned: `2673 / 2926` (91.35%)
- QASM3 export: `2668 / 2926` (91.18%)
- reference-signature match: `1559 / 2926` (53.28%)
- runnable but signature-wrong: `1114` (38.07% of all cells; 41.68% of executable outputs)
- gate-type count-map match: `1786` (61.04%)
- gate-count match: `2304` (78.74%)
- qubit-count match: `2578` (88.11%)
- classical-bit-count match: `2285` (78.09%)

| model | provider | execution | signature match | execution-structure gap | QASM3 |
| --- | --- | ---: | ---: | ---: | ---: |
| `gpt-5.6-sol` | OpenAI | 153/154 (99.35%) | 97/154 (62.99%) | 36.36 pp | 99.35% |
| `gpt-5.5` | OpenAI | 150/154 (97.40%) | 93/154 (60.39%) | 37.01 pp | 97.40% |
| `gpt-5.4-mini` | OpenAI | 151/154 (98.05%) | 93/154 (60.39%) | 37.66 pp | 97.40% |
| `claude-fable-5` | Anthropic | 151/154 (98.05%) | 97/154 (62.99%) | 35.06 pp | 98.05% |
| `claude-sonnet-4-6` | Anthropic | 153/154 (99.35%) | 91/154 (59.09%) | 40.26 pp | 99.35% |
| `claude-opus-4-8` | Anthropic | 154/154 (100.00%) | 92/154 (59.74%) | 40.26 pp | 99.35% |
| `gemini-2.5-pro` | Google | 136/154 (88.31%) | 83/154 (53.90%) | 34.42 pp | 88.31% |
| `gemini-3.1-pro-preview` | Google | 149/154 (96.75%) | 94/154 (61.04%) | 35.71 pp | 96.75% |
| `deepseek-v4-pro` | DeepSeek | 141/154 (91.56%) | 91/154 (59.09%) | 32.47 pp | 91.56% |
| `deepseek-v4-flash` | DeepSeek | 137/154 (88.96%) | 81/154 (52.60%) | 36.36 pp | 88.96% |
| `llama-3.3-70b-versatile` | Groq | 144/154 (93.51%) | 71/154 (46.10%) | 47.40 pp | 93.51% |
| `qwen/qwen3-32b` | Groq | 89/154 (57.79%) | 54/154 (35.06%) | 22.73 pp | 57.79% |
| `openai/gpt-oss-120b` | Groq | 149/154 (96.75%) | 82/154 (53.25%) | 43.51 pp | 96.10% |
| `openai/gpt-oss-20b` | Groq | 143/154 (92.86%) | 78/154 (50.65%) | 42.21 pp | 92.21% |
| `llama-3.1-8b-instant` | Groq | 125/154 (81.17%) | 54/154 (35.06%) | 46.10 pp | 81.17% |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Groq | 127/154 (82.47%) | 69/154 (44.81%) | 37.66 pp | 82.47% |
| `mistral-ai/codestral-2501` | GitHub Models | 144/154 (93.51%) | 86/154 (55.84%) | 37.66 pp | 93.51% |
| `qwen/qwen3-coder-next` | Hugging Face / Novita | 132/154 (85.71%) | 78/154 (50.65%) | 35.06 pp | 85.71% |
| `meta/llama-4-maverick-17b-128e-instruct-fp8` | GitHub Models | 145/154 (94.16%) | 75/154 (48.70%) | 45.45 pp | 93.51% |

## Difficulty And Failure Structure

- prompts missed structurally by every model: `36`
- prompts solved structurally by every model: `16`
- prompts with mixed model disagreement: `102`
- within the mixed region: `5` frontier-only and `10` non-frontier-only items
- dominant primary failure: gate-vocabulary mismatch (`887` cells)
- among executable nonmatches, the gate-type count map differs in `887` cases

Tier-level signature match is 59.22% for frontier APIs, 50.87% for strong open/code systems, and 38.31% for low/experimental systems. The Llama 8B row reaches 35.06%, 19.48 percentage points above the 15.58% instruction-copy baseline.
Qwen3-Coder-Next improves over the general Qwen3-32B row by 27.92 percentage points in executable-circuit success and 15.58 points in reference-signature match, but remains 5.19 points below Codestral. Code specialization therefore helps materially without closing the quantum structural-fidelity gap.

## Retrieval-Copy Baselines

| baseline | execution | signature match | QASM3 | role |
| --- | ---: | ---: | ---: | --- |
| `majority_train_code_copy` | 0.00% | 0.00% | 0.00% | degenerate control |
| `bm25_code_metadata_copy` | 75.32% | 5.84% | 75.32% | code/metadata sparse copy |
| `word_tfidf_code_metadata_copy` | 94.81% | 1.30% | 94.81% | code/metadata TF-IDF copy |
| `word_tfidf_train_instruction_copy` | 91.56% | 15.58% | 91.56% | best non-oracle copy baseline |
| `target_code_oracle` | 91.56% | 91.56% | 90.91% | strict-standalone evaluator audit, not a model |

## Source-Artifact Validity

- strict isolated execution: `665 / 734` (90.60%)
- conservative context recovery: all `69` NameError rows recovered, giving `734 / 734` execution (100.00%)
- combined source-signature agreement: `728 / 734` (99.18%)
- combined QASM3 export: `726 / 734` (98.91%)
- eligible small-circuit simulations: `165 / 165`

The 100% result is therefore a documented recoverability claim, not a claim that every source snippet is standalone without notebook or repository context.

## Prompt Identifiability And Signature Weighting

Four prompts (`0040`, `0117`, `0141`, `0142`) require hidden source details not entailed by their model inputs. They account for `76` model-prompt cells and `0` signature matches.
- full frozen matrix: execution `2673 / 2926` (91.35%); signature `1559 / 2926` (53.28%); ES-gap `38.07%`; signature-wrong given execution `41.68%`
- identifiable subset: execution `2619 / 2850` (91.89%); signature `1559 / 2850` (54.70%); ES-gap `37.19%`; signature-wrong given execution `40.47%`
- structural change: `+1.42 pp`; execution change: `+0.54 pp`
- every model's structural numerator is unchanged, so model ordering is unchanged
- signature-collapsed weighting: `53.28%` to `52.66%` (-0.62 pp)
- repeated-signature structure: `6` groups covering `16` prompts; largest group `4`

## Complexity Findings: Full Versus Identifiable

| analysis | 1-2 gate types | 3-4 gate types | 5+ gate types | gate entropy r | gate types r | gate count r | qubits r | no barrier | barrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full 154 | 72.31% | 54.67% | 19.30% | -0.440 | -0.418 | -0.233 | -0.046 | 65.87% | 29.29% |
| identifiable 150 | 72.31% | 56.68% | 20.04% | -0.434 | -0.418 | -0.193 | -0.045 | 67.20% | 30.44% |

The descriptive prompt-level linear probability model remains stable after exclusion: R-squared changes from `0.365` to `0.356`; gate entropy changes from `-11.41` to `-10.55` percentage points per SD, and the barrier contrast from `-28.33` to `-26.28` percentage points. In the prompt-model model, strong open/code and low/experimental tier offsets are `-8.35` and `-20.91` percentage points in the full matrix, versus `-8.58` and `-21.47` in the identifiable subset. These are descriptive effect sizes without causal interpretation.

## Completion And Recovery Diagnostics

- all 19 canonical rows are record-complete at 154/154
- targeted Codestral frequency-penalty calls converted prompts 0141 and 0142 from truncation to concise executable outputs, but neither matched the source signature
- low-effort Fable converted prompt 0040 from thinking-budget exhaustion to executable output, but not a signature match
- Fable prompt 0141 remains a reproducible provider-side `cyber` classifier refusal; it is a valid failure outcome, not missing data
- Qwen3-Coder-Next billing recovery filled all 15 initially missing provider outputs; its 17 superseded HTTP 402 records and precanonical log remain preserved in the recovery audit
- Llama 4 Maverick is complete at 154/154 canonical prompts with zero provider errors; three superseded recovery rows remain preserved in its audit
- Codestral and Fable decoding diagnostics are separately logged and do not modify their canonical scores

## Current Risks

1. Metric interpretation: `all-structure match` must be renamed `reference-signature match`; it does not test ordered gate tape, operands, unitary equivalence, or output-distribution equivalence.
2. Prompt identifiability: the four under-specified prompts cannot support exact hidden-signature correctness claims. Use the 150-item subset for confirmatory signature analysis.
3. Regression scope: the target-signature-clustered bootstrap and grouped cross-validation quantify release-bound uncertainty, but correlated descriptors and the fixed model panel still preclude causal or universal-law interpretations.
4. Source execution: 100% requires documented context recovery; strict standalone execution is 90.60%.
5. Transfer proofing: the synchronized Markdown and vector sources still require a final ACM-layout check for float placement, font size, and page breaks.

## Manuscript Synchronization Status

- active abstract: synchronized to 19 models x 154 prompts and 2,926 cells
- main model and inferential tables: synchronized to the final matrix
- supplement: final denominators, sensitivity analyses, and paired comparisons synchronized; the 70 x 15 table is retained only as labelled pilot provenance
- Figure 2 heatmap: regenerated from the canonical 19 x 154 matrix
- Figures 3-5 and supplemental analytical panels: regenerated from final analysis artifacts
- Figure 1 and benchmark-construction sections: substantially unaffected

## Required Next Actions

1. Preserve the reporting contract: full 154 for the frozen primary matrix and the identifiable 150 as a labelled sensitivity analysis.
2. Run the final denominator, figure-callout, table-number, and artifact-path audit.
3. Render and proof the ACM transfer package without editing the frozen analytical sources.
4. Package the prompts, canonical responses, evaluations, analysis artifacts, and environment information for the distinct PQID-Bench GitHub/Zenodo release.

## Publication Assessment

The study remains scientifically meaningful and publication-grade. Expansion strengthens precision, provider coverage, and benchmark differentiation. The central result is robust: strong systems usually return executable quantum circuits, yet exact source-signature recovery remains substantially harder, and gate heterogeneity/barrier staging remain stronger difficulty signals than width. No further API runs are required for the main evidence; remaining work is transfer rendering, proofing, and release packaging.
