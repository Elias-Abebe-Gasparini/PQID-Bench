# PQID-Bench Structural-Signature Sensitivity Report

This report checks whether repeated target-metadata signatures drive the headline external-generation result. The signature used here is conservative and evaluator-facing: `(num_qubits, num_clbits, gate_count, gate-type multiset)`. It does not claim full quantum semantic equivalence, but it identifies prompt variants that share the same frozen structural metadata used by the all-structure scorer.

## Summary

- held-out prompt instances: `70`
- completed named external model rows: `15`
- prompt-model cells: `1050`
- unique target-metadata signatures: `60`
- duplicate-signature groups: `6`
- prompt instances in duplicate-signature groups: `16`
- largest duplicate-signature group: `4`
- prompt-level structural match: `53.71%`
- signature-collapsed structural match: `52.83%`
- collapsed-minus-prompt delta: `-0.88 pp`

## Per-Model Sensitivity

| model | prompt-level structural | signature-collapsed structural | delta |
| --- | ---: | ---: | ---: |
| `gpt-5.5` | 62.86% | 61.67% | -1.19 pp |
| `gpt-5.4-mini` | 64.29% | 63.33% | -0.95 pp |
| `claude-sonnet-4-6` | 61.43% | 60.00% | -1.43 pp |
| `claude-opus-4-8` | 61.43% | 60.00% | -1.43 pp |
| `gemini-2.5-pro` | 62.86% | 63.33% | +0.48 pp |
| `gemini-3.1-pro-preview` | 62.86% | 61.67% | -1.19 pp |
| `deepseek-v4-pro` | 58.57% | 57.50% | -1.07 pp |
| `deepseek-v4-flash` | 58.57% | 57.50% | -1.07 pp |
| `mistral-ai/codestral-2501` | 58.57% | 57.50% | -1.07 pp |
| `llama-3.3-70b-versatile` | 50.00% | 48.33% | -1.67 pp |
| `openai/gpt-oss-120b` | 52.86% | 51.67% | -1.19 pp |
| `openai/gpt-oss-20b` | 51.43% | 50.83% | -0.60 pp |
| `qwen/qwen3-32b` | 38.57% | 40.00% | +1.43 pp |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 38.57% | 38.75% | +0.18 pp |
| `llama-3.1-8b-instant` | 22.86% | 20.42% | -2.44 pp |

## Duplicate Metadata-Signature Groups

| group | target-metadata signature | prompt ids | prompt-level structural means |
| ---: | --- | --- | --- |
| 1 | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | `pqid_bench_external_gen_0004`, `pqid_bench_external_gen_0028`, `pqid_bench_external_gen_0063`, `pqid_bench_external_gen_0064` | 0004=0.00%, 0028=0.00%, 0063=0.00%, 0064=0.00% |
| 2 | 2q/2c; 4 gates; cx:1, h:1, measure:2 | `pqid_bench_external_gen_0019`, `pqid_bench_external_gen_0054`, `pqid_bench_external_gen_0055`, `pqid_bench_external_gen_0058` | 0019=93.33%, 0054=86.67%, 0055=100.00%, 0058=93.33% |
| 3 | 2q/2c; 2 gates; h:1, x:1 | `pqid_bench_external_gen_0017`, `pqid_bench_external_gen_0018` | 0017=60.00%, 0018=60.00% |
| 4 | 2q/2c; 6 gates; cx:1, measure:2, x:3 | `pqid_bench_external_gen_0044`, `pqid_bench_external_gen_0045` | 0044=80.00%, 0045=73.33% |
| 5 | 3q/3c; 5 gates; h:2, measure:3 | `pqid_bench_external_gen_0003`, `pqid_bench_external_gen_0035` | 0003=100.00%, 0035=73.33% |
| 6 | 3q/3c; 5 gates; cx:1, h:1, measure:3 | `pqid_bench_external_gen_0015`, `pqid_bench_external_gen_0039` | 0015=80.00%, 0039=93.33% |
