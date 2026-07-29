"""Run dependency-free TF-IDF retrieval baselines for PQID-Bench.

This companion to `run_pqid_bench_retrieval_baseline.py` strengthens the
instruction-to-code retrieval evidence without adding neural embedding or
search dependencies. It evaluates sparse vector-space rankers over the same
734 clean source-code records and includes a reciprocal-rank fusion condition
that combines the original BM25 ranker with TF-IDF word and character views.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable

import run_pqid_bench_retrieval_baseline as bm25


DEFAULT_INPUT = bm25.DEFAULT_INPUT
DEFAULT_OUTPUT_DIR = bm25.DEFAULT_OUTPUT_DIR
DEFAULT_BM25_REPORT = DEFAULT_OUTPUT_DIR / "pqid_bench_retrieval_baseline_report.json"

TokenBuilder = Callable[[object], list[str]]


def word_unigram_bigram_tokens(text: object) -> list[str]:
    tokens = bm25.tokenize(text)
    bigrams = [f"{left}__{right}" for left, right in zip(tokens, tokens[1:])]
    return tokens + bigrams


def char_ngram_tokens(text: object, min_n: int = 3, max_n: int = 5) -> list[str]:
    normalized = " ".join(bm25.normalize_text(text).lower().split())
    if not normalized:
        return []
    padded = f" {normalized} "
    grams: list[str] = []
    for size in range(min_n, max_n + 1):
        if len(padded) < size:
            continue
        grams.extend(padded[index : index + size] for index in range(len(padded) - size + 1))
    return grams


class TfidfIndex:
    def __init__(
        self,
        rows: list[dict],
        mode: str,
        token_builder: TokenBuilder,
    ) -> None:
        self.rows = rows
        self.mode = mode
        self.token_builder = token_builder

        document_counts: list[Counter] = []
        df: Counter = Counter()
        for row in rows:
            counts = Counter(token_builder(bm25.doc_text(row, mode)))
            document_counts.append(counts)
            df.update(counts.keys())

        self.idf = {
            term: math.log((len(rows) + 1.0) / (freq + 1.0)) + 1.0
            for term, freq in df.items()
        }
        self.doc_vectors = [self._weighted_vector(counts) for counts in document_counts]
        self.doc_norms = [self._norm(vector) for vector in self.doc_vectors]
        self.postings: dict[str, list[tuple[int, float]]] = {}
        for doc_index, vector in enumerate(self.doc_vectors):
            norm = self.doc_norms[doc_index]
            if not norm:
                continue
            for term, weight in vector.items():
                self.postings.setdefault(term, []).append((doc_index, weight / norm))

    def _weighted_vector(self, counts: Counter) -> dict[str, float]:
        vector: dict[str, float] = {}
        for term, count in counts.items():
            idf = self.idf.get(term)
            if idf is None:
                continue
            vector[term] = (1.0 + math.log(count)) * idf
        return vector

    @staticmethod
    def _norm(vector: dict[str, float]) -> float:
        return math.sqrt(sum(weight * weight for weight in vector.values()))

    def _query_vector(self, text: object) -> tuple[dict[str, float], float]:
        counts = Counter(self.token_builder(text))
        vector = self._weighted_vector(counts)
        return vector, self._norm(vector)

    def score_vector(
        self,
        query_vector: dict[str, float],
        query_norm: float,
        doc_index: int,
    ) -> float:
        if not query_norm or not self.doc_norms[doc_index]:
            return 0.0
        doc_vector = self.doc_vectors[doc_index]
        if len(query_vector) < len(doc_vector):
            numerator = sum(
                weight * doc_vector.get(term, 0.0)
                for term, weight in query_vector.items()
            )
        else:
            numerator = sum(
                weight * query_vector.get(term, 0.0)
                for term, weight in doc_vector.items()
            )
        return numerator / (query_norm * self.doc_norms[doc_index])

    def rank(self, query_text: object) -> list[tuple[str, float]]:
        query_vector, query_norm = self._query_vector(query_text)
        if query_norm:
            scores: dict[int, float] = {}
            for term, weight in query_vector.items():
                query_weight = weight / query_norm
                for doc_index, doc_weight in self.postings.get(term, []):
                    scores[doc_index] = scores.get(doc_index, 0.0) + query_weight * doc_weight
        else:
            scores = {}
        scored = [
            (row["row_id"], scores.get(index, 0.0))
            for index, row in enumerate(self.rows)
        ]
        return sorted(scored, key=lambda item: (-item[1], item[0]))


class BM25Ranker:
    def __init__(self, rows: list[dict], mode: str) -> None:
        self.index = bm25.BM25Index(rows, mode)

    def rank(self, query_text: object) -> list[tuple[str, float]]:
        return self.index.rank_terms(Counter(bm25.tokenize(query_text)))


class ReciprocalRankFusion:
    def __init__(
        self,
        rankers: list[object],
        k: int = 60,
        weights: list[float] | None = None,
    ) -> None:
        self.rankers = rankers
        self.k = k
        self.weights = weights or [1.0] * len(rankers)
        if len(self.weights) != len(self.rankers):
            raise ValueError("RRF weights must match ranker count")

    def rank(self, query_text: object) -> list[tuple[str, float]]:
        scores: Counter = Counter()
        for weight, ranker in zip(self.weights, self.rankers):
            for rank, (row_id, _score) in enumerate(ranker.rank(query_text), start=1):
                scores[row_id] += weight / (self.k + rank)
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def rank_metrics(ranks: list[int]) -> dict:
    return bm25.rank_metrics(ranks)


def evaluate_ranker(rows: list[dict], ranker: object) -> tuple[dict, list[dict]]:
    by_id = {row["row_id"]: row for row in rows}
    ranks: list[int] = []
    records: list[dict] = []

    for row in rows:
        ranked = ranker.rank(row["query"])
        target_rank = 0
        target_score = 0.0
        for rank, (row_id, score) in enumerate(ranked, start=1):
            if row_id == row["row_id"]:
                target_rank = rank
                target_score = score
                break
        if target_rank == 0:
            raise ValueError(f"Target row disappeared from ranking: {row['row_id']}")
        ranks.append(target_rank)
        top_id, top_score = ranked[0]
        records.append(
            {
                "row_id": row["row_id"],
                "label": row["label"],
                "rank": target_rank,
                "top1_id": top_id,
                "top1_correct": top_id == row["row_id"],
                "top1_score": top_score,
                "target_score": target_score,
                "top1_label": by_id[top_id]["label"],
                "query": row["query"],
                "expected_code": row["code"],
                "retrieved_code": by_id[top_id]["code"],
                "expected_metadata": row["metadata"],
                "retrieved_metadata": by_id[top_id]["metadata"],
            }
        )

    metrics = rank_metrics(ranks)
    per_label = {}
    for label in bm25.LABEL_ORDER:
        label_ranks = [record["rank"] for record in records if record["label"] == label]
        per_label[label] = rank_metrics(label_ranks)
    metrics["per_label"] = per_label
    return metrics, records


def load_bm25_reference(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for result in payload.get("results", []):
        if result.get("name") == "code_plus_metadata_bm25":
            return result
    return None


def pct(value: float) -> str:
    return bm25.pct(value)


def format_delta(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}{abs(100 * value):.2f} pp"


def short_failure_examples(records: list[dict]) -> list[dict]:
    return bm25.failure_examples(records, limit=10)


def best_fair_result(results: list[dict]) -> dict:
    fair_results = [result for result in results if result.get("fair")]
    return max(
        fair_results,
        key=lambda result: (
            result["metrics"]["recall_at_1"],
            result["metrics"]["recall_at_5"],
            result["metrics"]["mrr"],
        ),
    )


def write_outputs(
    output_dir: Path,
    input_path: Path,
    rows: list[dict],
    results: list[dict],
    records_by_name: dict[str, list[dict]],
    bm25_reference: dict | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_tfidf_retrieval_baseline_report.md"
    json_path = output_dir / "pqid_bench_tfidf_retrieval_baseline_report.json"
    label_counts = Counter(row["label"] for row in rows)
    best = best_fair_result(results)
    best_records = records_by_name[best["name"]]
    taxonomy = bm25.failure_taxonomy(best_records)
    failures = short_failure_examples(best_records)

    lines = [
        "# PQID-Bench TF-IDF Retrieval Strengthening Report",
        "",
        f"- input file: `{bm25.display_path(input_path)}`",
        f"- clean source-code queries: `{len(rows):,}`",
        "- scope: dependency-free sparse vector-space retrieval over the same clean pool as the BM25 baseline",
        "- slice reconstruction: `seed_role == gold_generation` -> `strict_n8`; `seed_role == broad_generation` -> `extended_n8`",
        "",
        "## Clean Retrieval Pool",
        "",
        "| slice | rows |",
        "| --- | ---: |",
    ]
    for label in bm25.LABEL_ORDER:
        lines.append(f"| `{label}` | {label_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## Vector-Space And Fusion Baselines",
            "",
            "These baselines do not use the target instruction as candidate text, except for the explicitly marked upper-bound sanity check. The reciprocal-rank fusion condition combines the original BM25 code+metadata ranker with TF-IDF word and character views.",
            "",
            "| baseline | indexed candidate text | queries | Recall@1 | Recall@5 | Recall@10 | MRR | median rank | mean rank |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        metrics = result["metrics"]
        lines.append(
            f"| `{result['name']}` | {result['description']} | {metrics['queries']:,} | "
            f"{pct(metrics['recall_at_1'])} | {pct(metrics['recall_at_5'])} | "
            f"{pct(metrics['recall_at_10'])} | {metrics['mrr']:.4f} | "
            f"{metrics['median_rank']:.1f} | {metrics['mean_rank']:.1f} |"
        )

    if bm25_reference is not None:
        reference_metrics = bm25_reference["metrics"]
        best_metrics = best["metrics"]
        lines.extend(
            [
                "",
                "## Comparison With BM25 Code+Metadata",
                "",
                "| comparison | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
                f"| `code_plus_metadata_bm25` | {pct(reference_metrics['recall_at_1'])} | {pct(reference_metrics['recall_at_5'])} | {pct(reference_metrics['recall_at_10'])} | {reference_metrics['mrr']:.4f} | {reference_metrics['median_rank']:.1f} |",
                f"| `{best['name']}` | {pct(best_metrics['recall_at_1'])} ({format_delta(best_metrics['recall_at_1'] - reference_metrics['recall_at_1'])}) | {pct(best_metrics['recall_at_5'])} ({format_delta(best_metrics['recall_at_5'] - reference_metrics['recall_at_5'])}) | {pct(best_metrics['recall_at_10'])} ({format_delta(best_metrics['recall_at_10'] - reference_metrics['recall_at_10'])}) | {best_metrics['mrr']:.4f} ({best_metrics['mrr'] - reference_metrics['mrr']:+.4f}) | {best_metrics['median_rank']:.1f} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Best Fair Baseline Slice Breakdown",
            "",
            f"Selected by Recall@1 among non-instruction candidate representations: `{best['name']}`.",
            "",
            "| slice | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in bm25.LABEL_ORDER:
        metrics = best["metrics"]["per_label"][label]
        lines.append(
            f"| `{label}` | {pct(metrics['recall_at_1'])} | {pct(metrics['recall_at_5'])} | "
            f"{pct(metrics['recall_at_10'])} | {metrics['mrr']:.4f} | {metrics['median_rank']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Best Fair Baseline Top-1 Failure Taxonomy",
            "",
            "| category | failures | share | strict_n8 | extended_n8 | interpretation |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in taxonomy:
        lines.append(
            f"| `{row['category']}` | {row['failures']:,} | "
            f"{pct(row['share_of_top1_failures'])} | {row['strict_n8']:,} | "
            f"{row['extended_n8']:,} | {row['description']} |"
        )

    lines.extend(
        [
            "",
            "## Representative Best-Fair Top-1 Failures",
            "",
        ]
    )
    if not failures:
        lines.append("No top-1 failures for the selected baseline.")
    else:
        for index, example in enumerate(failures, start=1):
            lines.extend(
                [
                    f"### Failure {index}",
                    "",
                    f"- slice: `{example['label']}`; target rank: `{example['rank']}`; top-1 slice: `{example['top1_label']}`",
                    f"- taxonomy: `{example['failure_category']}` - {example['failure_description']}",
                    f"- query: {example['query']}",
                    f"- expected file: `{example['expected_file']}`",
                    f"- retrieved file: `{example['retrieved_file']}`",
                    f"- expected gates: `{example['expected_gate_types']}`",
                    f"- retrieved gates: `{example['retrieved_gate_types']}`",
                    "",
                ]
            )

    payload = {
        "input_file": bm25.display_path(input_path),
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "slice_reconstruction": bm25.CLEAN_ROLE_TO_LABEL,
        "bm25_reference": bm25_reference,
        "results": results,
        "best_fair_baseline": best["name"],
        "best_fair_failure_taxonomy": taxonomy,
        "best_fair_failures": failures,
    }

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {bm25.display_path(report_path)}")
    print(f"Wrote {bm25.display_path(json_path)}")


def run(input_path: Path, output_dir: Path, bm25_report: Path) -> None:
    rows = bm25.clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(
            f"Expected 734 clean source-code rows from seed_role labels, found {len(rows)}"
        )

    word_code = TfidfIndex(rows, "code_only", word_unigram_bigram_tokens)
    word_code_metadata = TfidfIndex(rows, "code_plus_metadata", word_unigram_bigram_tokens)
    char_code_metadata = TfidfIndex(rows, "code_plus_metadata", char_ngram_tokens)
    upper_bound = TfidfIndex(rows, "instruction_upper_bound", word_unigram_bigram_tokens)
    fusion = ReciprocalRankFusion(
        [
            BM25Ranker(rows, "code_plus_metadata"),
            word_code_metadata,
            char_code_metadata,
        ],
        weights=[1.0, 1.0, 0.75],
    )

    rankers = [
        (
            "word_tfidf_code_only",
            "word unigram/bigram TF-IDF over code only",
            word_code,
            True,
        ),
        (
            "word_tfidf_code_plus_metadata",
            "word unigram/bigram TF-IDF over code plus non-instruction metadata",
            word_code_metadata,
            True,
        ),
        (
            "char_tfidf_code_plus_metadata",
            "character 3-5 gram TF-IDF over code plus non-instruction metadata",
            char_code_metadata,
            True,
        ),
        (
            "rrf_bm25_word_char_code_plus_metadata",
            "reciprocal-rank fusion of BM25, word TF-IDF, and character TF-IDF over code plus non-instruction metadata",
            fusion,
            True,
        ),
        (
            "instruction_upper_bound_word_tfidf",
            "instruction text upper bound with word unigram/bigram TF-IDF",
            upper_bound,
            False,
        ),
    ]

    results = []
    records_by_name: dict[str, list[dict]] = {}
    for name, description, ranker, fair in rankers:
        metrics, records = evaluate_ranker(rows, ranker)
        results.append(
            {
                "name": name,
                "description": description,
                "fair": fair,
                "metrics": metrics,
            }
        )
        records_by_name[name] = records

    write_outputs(
        output_dir=output_dir,
        input_path=input_path,
        rows=rows,
        results=results,
        records_by_name=records_by_name,
        bm25_reference=load_bm25_reference(bm25_report),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bm25-report", type=Path, default=DEFAULT_BM25_REPORT)
    args = parser.parse_args()

    run(args.input, args.output_dir, args.bm25_report)


if __name__ == "__main__":
    main()
