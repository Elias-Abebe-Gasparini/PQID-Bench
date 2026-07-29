"""Run dependency-free retrieval baselines for the PQID-Bench clean slice.

This script evaluates instruction-to-code retrieval over the source-code seed
artifact. The seed artifact predates the later `benchmark_view_membership`
field, so it reconstructs the clean generation slices from `seed_role`:

- `gold_generation` -> `strict_n8`
- `broad_generation` -> `extended_n8`

The baselines are intentionally simple BM25-style rankers so the reviewer
artifact can run without installing search or ML dependencies.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
PQID_DIR = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
DEFAULT_INPUT = (
    PQID_DIR / "data" / "processed" / "seed_drafts_quality_aware_source_code_v1.jsonl"
)
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts"

CLEAN_ROLE_TO_LABEL = {
    "gold_generation": "strict_n8",
    "broad_generation": "extended_n8",
}

LABEL_ORDER = ["strict_n8", "extended_n8"]

GATE_TOKENS = {
    "h",
    "x",
    "y",
    "z",
    "s",
    "t",
    "rx",
    "ry",
    "rz",
    "rxx",
    "ryy",
    "rzz",
    "cx",
    "cy",
    "cz",
    "ccx",
    "swap",
    "cswap",
    "measure",
    "barrier",
    "reset",
    "phase",
    "u",
    "u1",
    "u2",
    "u3",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "both",
    "by",
    "create",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "make",
    "of",
    "on",
    "or",
    "that",
    "the",
    "then",
    "this",
    "to",
    "using",
    "with",
}

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?")

ALGORITHM_KEYWORDS = {
    "adder",
    "bell",
    "deutsch",
    "des",
    "e91",
    "grover",
    "iris",
    "permutation",
    "qft",
    "qkd",
    "siamese",
    "teleportation",
    "vqc",
}

FAILURE_CATEGORY_DESCRIPTIONS = {
    "same_source_register_or_subcircuit": (
        "same source lineage and same gate signature, but the retrieved subcircuit "
        "targets a different register, role, or named component"
    ),
    "same_source_lineage_neighbor": (
        "same file, notebook lineage, or source context, but the retrieved fragment "
        "is not the requested target"
    ),
    "exact_gate_signature_ambiguity": (
        "different source context with the same gate multiset, leaving lexical BM25 "
        "unable to identify the intended register/name semantics"
    ),
    "scaled_family_variant": (
        "same circuit family or gate vocabulary, but with different width, depth, "
        "parameter count, or repeated block scale"
    ),
    "algorithm_family_confusion": (
        "same named algorithm/protocol family, but the retrieved implementation is "
        "a different variant"
    ),
    "size_or_complexity_distractor": (
        "shared gate vocabulary but a large width/depth/gate-count mismatch"
    ),
    "gate_vocabulary_distractor": (
        "shared low-level gate vocabulary without enough semantic information to "
        "recover the exact source record"
    ),
    "lexical_metadata_distractor": (
        "remaining lexical or metadata attraction without a simple structural match"
    ),
}


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def split_identifier(token: str) -> list[str]:
    pieces: list[str] = []
    for chunk in token.split("_"):
        chunk = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", chunk)
        pieces.extend(part for part in chunk.split() if part)
    return pieces


def normalize_text(text: object) -> str:
    if text is None:
        return ""
    normalized = str(text)
    replacements = {
        "\u03c0": " pi ",
        "\u03b8": " theta ",
        "\u03bb": " lambda ",
        "\u03c6": " phi ",
        "\u03a6": " phi ",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def tokenize(text: object) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(normalize_text(text)):
        for part in split_identifier(raw):
            token = part.lower()
            if token in STOPWORDS and token not in GATE_TOKENS:
                continue
            if len(token) <= 1 and token not in GATE_TOKENS:
                continue
            tokens.append(token)
    return tokens


def metadata_terms(metadata: dict) -> str:
    pieces: list[str] = []

    for field in [
        "repo_owner",
        "repo_name",
        "file_path",
        "source",
        "retrieval_strategy",
        "benchmark_difficulty",
        "circuit_expressiveness",
        "size_class",
    ]:
        value = metadata.get(field)
        if value:
            pieces.append(str(value))

    for field in [
        "num_qubits",
        "num_clbits",
        "gate_count",
        "circuit_depth",
        "measurement_count",
    ]:
        value = metadata.get(field)
        if value is not None:
            pieces.append(f"{field}_{value}")

    for field in [
        "has_measurement",
        "has_entangling_gates",
        "has_rotation_gates",
        "has_clifford_only",
        "is_parameterized",
    ]:
        value = metadata.get(field)
        if value is not None:
            pieces.append(f"{field}_{value}")

    gate_types = metadata.get("gate_types")
    if isinstance(gate_types, dict):
        for gate, count in sorted(gate_types.items()):
            pieces.append(f"gate_{gate}")
            repeat_count = min(int(count or 1), 3)
            pieces.extend([str(gate)] * repeat_count)

    return " ".join(pieces)


def clean_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    role_counts = Counter()
    skipped_missing_text = 0

    for raw in iter_jsonl(path):
        metadata = raw.get("metadata", {})
        role = metadata.get("seed_role")
        role_counts[role] += 1
        if role not in CLEAN_ROLE_TO_LABEL:
            continue

        query = (raw.get("input") or "").strip()
        code = (raw.get("output") or "").strip()
        if not query or not code:
            skipped_missing_text += 1
            continue

        row_id = metadata.get("content_hash") or f"clean_{len(rows):04d}"
        rows.append(
            {
                "row_id": str(row_id),
                "label": CLEAN_ROLE_TO_LABEL[role],
                "seed_role": role,
                "query": query,
                "code": code,
                "metadata": metadata,
            }
        )

    if skipped_missing_text:
        raise ValueError(f"Skipped {skipped_missing_text} clean rows with missing query/code text")

    return rows


def doc_text(row: dict, mode: str) -> str:
    if mode == "code_only":
        return row["code"]
    if mode == "metadata_only":
        return metadata_terms(row["metadata"])
    if mode == "code_plus_metadata":
        return f"{row['code']}\n{metadata_terms(row['metadata'])}"
    if mode == "instruction_upper_bound":
        return row["query"]
    raise ValueError(f"Unknown document mode: {mode}")


class BM25Index:
    def __init__(self, docs: list[dict], mode: str, k1: float = 1.5, b: float = 0.75) -> None:
        self.docs = docs
        self.mode = mode
        self.k1 = k1
        self.b = b
        self.term_counts: list[Counter] = []
        self.doc_lengths: list[int] = []
        df: Counter = Counter()

        for row in docs:
            counts = Counter(tokenize(doc_text(row, mode)))
            self.term_counts.append(counts)
            length = sum(counts.values())
            self.doc_lengths.append(length)
            df.update(counts.keys())

        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        n_docs = len(self.docs)
        self.idf = {
            term: math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def score_terms(self, query_terms: Counter, doc_index: int) -> float:
        counts = self.term_counts[doc_index]
        doc_length = self.doc_lengths[doc_index] or 1
        denominator_norm = self.k1 * (
            1.0 - self.b + self.b * doc_length / (self.avg_doc_length or 1.0)
        )

        score = 0.0
        for term, query_count in query_terms.items():
            tf = counts.get(term, 0)
            if not tf:
                continue
            idf = self.idf.get(term, 0.0)
            score += query_count * idf * (tf * (self.k1 + 1.0)) / (tf + denominator_norm)
        return score

    def rank_terms(self, query_terms: Counter) -> list[tuple[str, float]]:
        scored = [
            (row["row_id"], self.score_terms(query_terms, index))
            for index, row in enumerate(self.docs)
        ]
        return sorted(scored, key=lambda item: (-item[1], item[0]))


def evaluate(rows: list[dict], mode: str) -> tuple[dict, list[dict]]:
    index = BM25Index(rows, mode)
    by_id = {row["row_id"]: row for row in rows}
    ranks: list[int] = []
    records: list[dict] = []

    for row in rows:
        ranked = index.rank_terms(Counter(tokenize(row["query"])))
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
    for label in LABEL_ORDER:
        label_ranks = [record["rank"] for record in records if record["label"] == label]
        per_label[label] = rank_metrics(label_ranks)
    metrics["per_label"] = per_label
    return metrics, records


def rank_metrics(ranks: list[int]) -> dict:
    if not ranks:
        return {
            "queries": 0,
            "recall_at_1": 0.0,
            "recall_at_5": 0.0,
            "recall_at_10": 0.0,
            "mrr": 0.0,
            "mean_rank": 0.0,
            "median_rank": 0.0,
        }
    return {
        "queries": len(ranks),
        "recall_at_1": sum(1 for rank in ranks if rank <= 1) / len(ranks),
        "recall_at_5": sum(1 for rank in ranks if rank <= 5) / len(ranks),
        "recall_at_10": sum(1 for rank in ranks if rank <= 10) / len(ranks),
        "mrr": sum(1.0 / rank for rank in ranks) / len(ranks),
        "mean_rank": sum(ranks) / len(ranks),
        "median_rank": statistics.median(ranks),
    }


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def short(text: str, limit: int = 220) -> str:
    one_line = " ".join(text.split())
    return one_line if len(one_line) <= limit else one_line[: limit - 3] + "..."


def failure_examples(records: list[dict], limit: int = 12) -> list[dict]:
    failures = [record for record in records if not record["top1_correct"]]
    failures.sort(key=lambda record: (-record["target_score"], record["rank"], record["row_id"]))
    examples = []
    for record in failures[:limit]:
        expected = record["expected_metadata"]
        retrieved = record["retrieved_metadata"]
        category = classify_failure(record)
        examples.append(
            {
                "row_id": record["row_id"],
                "label": record["label"],
                "rank": record["rank"],
                "top1_label": record["top1_label"],
                "failure_category": category,
                "failure_description": FAILURE_CATEGORY_DESCRIPTIONS[category],
                "query": short(record["query"]),
                "expected_code": short(record["expected_code"]),
                "retrieved_code": short(record["retrieved_code"]),
                "expected_gate_types": expected.get("gate_types"),
                "retrieved_gate_types": retrieved.get("gate_types"),
                "expected_file": expected.get("file_path"),
                "retrieved_file": retrieved.get("file_path"),
            }
        )
    return examples


def gate_counter(metadata: dict) -> Counter:
    gate_types = metadata.get("gate_types")
    if not isinstance(gate_types, dict):
        return Counter()
    return Counter({str(gate).lower(): int(count or 0) for gate, count in gate_types.items()})


def gate_jaccard(left: Counter, right: Counter) -> float:
    left_keys = set(left)
    right_keys = set(right)
    if not left_keys and not right_keys:
        return 0.0
    return len(left_keys & right_keys) / len(left_keys | right_keys)


def numeric(metadata: dict, field: str) -> float | None:
    value = metadata.get(field)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ratio_mismatch(left: float | None, right: float | None, threshold: float) -> bool:
    if left is None or right is None:
        return False
    smaller = max(min(abs(left), abs(right)), 1.0)
    larger = max(abs(left), abs(right), 1.0)
    return larger / smaller >= threshold


def path_tokens(path: object) -> set[str]:
    if not path:
        return set()
    return set(tokenize(str(path).replace("/", " ").replace("\\", " ")))


def basename(path: object) -> str:
    if not path:
        return ""
    return str(path).replace("\\", "/").rsplit("/", maxsplit=1)[-1].lower()


def same_source_context(expected_path: object, retrieved_path: object) -> bool:
    if not expected_path or not retrieved_path:
        return False
    expected = str(expected_path).replace("\\", "/").lower()
    retrieved = str(retrieved_path).replace("\\", "/").lower()
    if expected == retrieved:
        return True
    if expected.endswith(retrieved) or retrieved.endswith(expected):
        return True
    if basename(expected) and basename(expected) == basename(retrieved):
        return True

    left_tokens = path_tokens(expected)
    right_tokens = path_tokens(retrieved)
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
    return overlap >= 0.75


def algorithm_terms(*texts: object) -> set[str]:
    tokens: set[str] = set()
    for text in texts:
        tokens.update(tokenize(text))
    joined = " ".join(str(text or "").lower() for text in texts)
    found = {token for token in tokens if token in ALGORITHM_KEYWORDS}
    if "teleport" in joined:
        found.add("teleportation")
    if "quantum key distribution" in joined:
        found.add("qkd")
    if "half-adder" in joined or "half adder" in joined:
        found.add("adder")
    return found


def classify_failure(record: dict) -> str:
    expected = record["expected_metadata"]
    retrieved = record["retrieved_metadata"]
    expected_gates = gate_counter(expected)
    retrieved_gates = gate_counter(retrieved)
    gates_exact = bool(expected_gates) and expected_gates == retrieved_gates
    gate_overlap = gate_jaccard(expected_gates, retrieved_gates)
    same_context = same_source_context(expected.get("file_path"), retrieved.get("file_path"))

    width_mismatch = ratio_mismatch(
        numeric(expected, "num_qubits"),
        numeric(retrieved, "num_qubits"),
        threshold=1.75,
    )
    gate_count_mismatch = ratio_mismatch(
        numeric(expected, "gate_count"),
        numeric(retrieved, "gate_count"),
        threshold=1.75,
    )
    large_size_mismatch = ratio_mismatch(
        numeric(expected, "gate_count"),
        numeric(retrieved, "gate_count"),
        threshold=3.0,
    ) or ratio_mismatch(
        numeric(expected, "num_qubits"),
        numeric(retrieved, "num_qubits"),
        threshold=3.0,
    )

    expected_terms = algorithm_terms(
        record["query"], expected.get("file_path"), record["expected_code"]
    )
    retrieved_terms = algorithm_terms(retrieved.get("file_path"), record["retrieved_code"])
    shared_algorithm = bool(expected_terms & retrieved_terms)

    if same_context and gates_exact:
        return "same_source_register_or_subcircuit"
    if same_context:
        return "same_source_lineage_neighbor"
    if gates_exact:
        return "exact_gate_signature_ambiguity"
    if shared_algorithm and (width_mismatch or gate_count_mismatch or gate_overlap >= 0.55):
        return "scaled_family_variant"
    if shared_algorithm:
        return "algorithm_family_confusion"
    if large_size_mismatch and gate_overlap >= 0.25:
        return "size_or_complexity_distractor"
    if gate_overlap >= 0.40:
        return "gate_vocabulary_distractor"
    return "lexical_metadata_distractor"


def failure_taxonomy(records: list[dict], limit_examples: int = 2) -> list[dict]:
    failures = [record for record in records if not record["top1_correct"]]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for record in failures:
        by_category[classify_failure(record)].append(record)

    taxonomy = []
    for category, category_records in by_category.items():
        label_counts = Counter(record["label"] for record in category_records)
        examples = []
        ordered_examples = sorted(
            category_records,
            key=lambda record: (record["rank"], -record["target_score"], record["row_id"]),
        )
        for record in ordered_examples[:limit_examples]:
            expected = record["expected_metadata"]
            retrieved = record["retrieved_metadata"]
            examples.append(
                {
                    "query": short(record["query"], 160),
                    "rank": record["rank"],
                    "slice": record["label"],
                    "expected_file": expected.get("file_path"),
                    "retrieved_file": retrieved.get("file_path"),
                    "expected_gate_types": expected.get("gate_types"),
                    "retrieved_gate_types": retrieved.get("gate_types"),
                }
            )
        taxonomy.append(
            {
                "category": category,
                "description": FAILURE_CATEGORY_DESCRIPTIONS[category],
                "failures": len(category_records),
                "share_of_top1_failures": len(category_records) / len(failures)
                if failures
                else 0.0,
                "strict_n8": label_counts["strict_n8"],
                "extended_n8": label_counts["extended_n8"],
                "examples": examples,
            }
        )

    return sorted(taxonomy, key=lambda row: (-row["failures"], row["category"]))


def write_outputs(
    output_dir: Path,
    input_path: Path,
    rows: list[dict],
    results: list[dict],
    failures: list[dict],
    taxonomy: list[dict],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_retrieval_baseline_report.md"
    json_path = output_dir / "pqid_bench_retrieval_baseline_report.json"
    label_counts = Counter(row["label"] for row in rows)

    lines = [
        "# PQID-Bench Retrieval Baseline Report",
        "",
        f"- input file: `{display_path(input_path)}`",
        f"- clean source-code queries: `{len(rows):,}`",
        "- slice reconstruction: `seed_role == gold_generation` -> `strict_n8`; `seed_role == broad_generation` -> `extended_n8`",
        "",
        "## Clean Retrieval Pool",
        "",
        "| slice | rows |",
        "| --- | ---: |",
    ]
    for label in LABEL_ORDER:
        lines.append(f"| `{label}` | {label_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## BM25 Retrieval Baselines",
            "",
            "`instruction_upper_bound` indexes the instruction text itself and is included only as a leakage/ceiling sanity check. The fair lightweight baselines index code and/or non-instruction metadata.",
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

    lines.extend(
        [
            "",
            "## Slice Breakdown",
            "",
            "| baseline | slice | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        for label in LABEL_ORDER:
            metrics = result["metrics"]["per_label"][label]
            lines.append(
                f"| `{result['name']}` | `{label}` | {pct(metrics['recall_at_1'])} | "
                f"{pct(metrics['recall_at_5'])} | {pct(metrics['recall_at_10'])} | "
                f"{metrics['mrr']:.4f} | {metrics['median_rank']:.1f} |"
            )

    lines.extend(
        [
            "",
            "## Code+Metadata Top-1 Failure Taxonomy",
            "",
            "The taxonomy is computed over all top-1 misses from the strongest fair lightweight baseline (`code_plus_metadata_bm25`). Categories are heuristic and mutually exclusive; they are intended to guide the manuscript failure-mode table and later embedding/model-based retrieval experiments.",
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
            "## Representative Code+Metadata Top-1 Failures",
            "",
            "These examples show cases where the best fair lightweight baseline retrieved the wrong top candidate. They are useful for later failure taxonomy work.",
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
                    f"- expected code: `{example['expected_code']}`",
                    f"- retrieved code: `{example['retrieved_code']}`",
                    "",
                ]
            )

    payload = {
        "input_file": display_path(input_path),
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "slice_reconstruction": CLEAN_ROLE_TO_LABEL,
        "results": results,
        "code_plus_metadata_failure_taxonomy": taxonomy,
        "code_plus_metadata_failures": failures,
    }

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {display_path(report_path)}")
    print(f"Wrote {display_path(json_path)}")


def run(input_path: Path, output_dir: Path) -> None:
    rows = clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(
            f"Expected 734 clean source-code rows from seed_role labels, found {len(rows)}"
        )

    modes = [
        (
            "code_only_bm25",
            "code only",
            "code_only",
        ),
        (
            "metadata_only_bm25",
            "non-instruction metadata only",
            "metadata_only",
        ),
        (
            "code_plus_metadata_bm25",
            "code plus non-instruction metadata",
            "code_plus_metadata",
        ),
        (
            "instruction_upper_bound_bm25",
            "instruction text upper bound",
            "instruction_upper_bound",
        ),
    ]

    results = []
    selected_records: list[dict] = []
    for name, description, mode in modes:
        metrics, records = evaluate(rows, mode)
        results.append(
            {
                "name": name,
                "description": description,
                "metrics": metrics,
            }
        )
        if name == "code_plus_metadata_bm25":
            selected_records = records

    taxonomy = failure_taxonomy(selected_records)
    failures = failure_examples(selected_records)
    write_outputs(output_dir, input_path, rows, results, failures, taxonomy)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
