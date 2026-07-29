# PQID-Bench Structural-Signature Sensitivity Report

This report checks whether repeated target-metadata signatures drive the headline external-generation result. The signature used here is conservative and evaluator-facing: `(num_qubits, num_clbits, gate_count, gate-type multiset)`. It does not claim full quantum semantic equivalence, but it identifies prompt variants that share the same frozen structural metadata used by the all-structure scorer.

## Summary

- held-out prompt instances: `154`
- completed named external model rows: `21`
- prompt-model cells: `3234`
- unique target-metadata signatures: `144`
- duplicate-signature groups: `6`
- prompt instances in duplicate-signature groups: `16`
- largest duplicate-signature group: `4`
- prompt-level structural match: `52.66%`
- signature-collapsed structural match: `51.96%`
- collapsed-minus-prompt delta: `-0.70 pp`

## Per-Model Sensitivity

| model | prompt-level structural | signature-collapsed structural | delta |
| --- | ---: | ---: | ---: |
| `gpt-5.6-sol` | 62.99% | 62.50% | -0.49 pp |
| `gpt-5.5` | 60.39% | 59.72% | -0.67 pp |
| `gpt-5.4-mini` | 60.39% | 59.72% | -0.67 pp |
| `claude-fable-5` | 62.99% | 62.50% | -0.49 pp |
| `claude-sonnet-4-6` | 59.09% | 58.33% | -0.76 pp |
| `claude-opus-4-8` | 59.74% | 59.03% | -0.71 pp |
| `gemini-2.5-pro` | 53.90% | 53.47% | -0.42 pp |
| `gemini-3.1-pro-preview` | 61.04% | 60.42% | -0.62 pp |
| `deepseek-v4-pro` | 59.09% | 58.68% | -0.41 pp |
| `deepseek-v4-flash` | 52.60% | 51.74% | -0.86 pp |
| `mistral-ai/codestral-2501` | 55.84% | 55.21% | -0.64 pp |
| `qwen/qwen3-coder-next` | 50.65% | 49.65% | -1.00 pp |
| `meta/llama-4-maverick-17b-128e-instruct-fp8` | 48.70% | 47.22% | -1.48 pp |
| `llama-3.3-70b-versatile` | 46.10% | 45.14% | -0.97 pp |
| `openai/gpt-oss-120b` | 53.25% | 52.78% | -0.47 pp |
| `openai/gpt-oss-20b` | 50.65% | 50.00% | -0.65 pp |
| `mistralai/mistral-small-3.2-24b-instruct` | 48.70% | 47.22% | -1.48 pp |
| `qiskit/mistral-small-3.2-24b-qiskit` | 44.81% | 43.40% | -1.40 pp |
| `qwen/qwen3-32b` | 35.06% | 35.42% | +0.35 pp |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 44.81% | 44.62% | -0.19 pp |
| `llama-3.1-8b-instant` | 35.06% | 34.38% | -0.69 pp |

## Duplicate Metadata-Signature Groups

| group | target-metadata signature | prompt ids | prompt-level structural means |
| ---: | --- | --- | --- |
| 1 | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | `pqid_bench_external_gen_0004`, `pqid_bench_external_gen_0028`, `pqid_bench_external_gen_0063`, `pqid_bench_external_gen_0064` | 0004=0.00%, 0028=0.00%, 0063=0.00%, 0064=0.00% |
| 2 | 2q/2c; 4 gates; cx:1, h:1, measure:2 | `pqid_bench_external_gen_0019`, `pqid_bench_external_gen_0054`, `pqid_bench_external_gen_0055`, `pqid_bench_external_gen_0058` | 0019=100.00%, 0054=90.48%, 0055=100.00%, 0058=95.24% |
| 3 | 2q/2c; 2 gates; h:1, x:1 | `pqid_bench_external_gen_0017`, `pqid_bench_external_gen_0018` | 0017=71.43%, 0018=61.90% |
| 4 | 2q/2c; 6 gates; cx:1, measure:2, x:3 | `pqid_bench_external_gen_0044`, `pqid_bench_external_gen_0045` | 0044=85.71%, 0045=85.71% |
| 5 | 3q/3c; 5 gates; h:2, measure:3 | `pqid_bench_external_gen_0003`, `pqid_bench_external_gen_0035` | 0003=100.00%, 0035=85.71% |
| 6 | 3q/3c; 5 gates; cx:1, h:1, measure:3 | `pqid_bench_external_gen_0015`, `pqid_bench_external_gen_0039` | 0015=90.48%, 0039=95.24% |
