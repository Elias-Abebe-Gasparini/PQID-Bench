"""Run first model-facing generation baselines for PQID-Bench.

The baselines are intentionally local and deterministic. They use the clean
source-code seed slice, split by source-file group, and generate code for held-
out test instructions by copying the nearest training example. This establishes
the first instruction-to-code generation evaluation harness before introducing
external LLMs or neural retrievers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import run_pqid_bench_executable_validity_check as validity
import run_pqid_bench_retrieval_baseline as retrieval
import run_pqid_bench_tfidf_retrieval_baseline as tfidf


DEFAULT_INPUT = retrieval.DEFAULT_INPUT
DEFAULT_OUTPUT_DIR = retrieval.DEFAULT_OUTPUT_DIR
LABEL_ORDER = retrieval.LABEL_ORDER


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def source_group_id(row: dict) -> str:
    metadata = row["metadata"]
    pieces = [
        metadata.get("repo_owner") or "<owner>",
        metadata.get("repo_name") or "<repo>",
        metadata.get("file_path") or row["row_id"],
    ]
    return "|".join(str(piece) for piece in pieces)


def clean_rows(path: Path) -> list[dict]:
    rows = retrieval.clean_rows(path)
    for row in rows:
        row["_group_id"] = source_group_id(row)
    return rows


def split_rows(
    rows: list[dict],
    split_manifest_path: Path | None = None,
) -> dict[str, list[dict]]:
    if split_manifest_path is not None:
        return split_rows_from_manifest(rows, split_manifest_path)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["_group_id"]].append(row)

    label_rank = {label: index for index, label in enumerate(LABEL_ORDER)}
    groups_by_label: dict[str, list[str]] = defaultdict(list)
    for group_id, group_rows in grouped.items():
        counts = Counter(row["label"] for row in group_rows)
        majority_label = sorted(
            counts,
            key=lambda label: (-counts[label], label_rank.get(label, len(LABEL_ORDER)), label),
        )[0]
        groups_by_label[majority_label].append(group_id)

    split_for_group: dict[str, str] = {}
    for label, group_ids in groups_by_label.items():
        ordered = sorted(group_ids, key=lambda group_id: stable_int(f"{label}:{group_id}"))
        train_cut = int(0.8 * len(ordered))
        validation_cut = int(0.9 * len(ordered))
        for index, group_id in enumerate(ordered):
            if index < train_cut:
                split = "train"
            elif index < validation_cut:
                split = "validation"
            else:
                split = "test"
            split_for_group[group_id] = split

    splits = {"train": [], "validation": [], "test": []}
    for row in rows:
        splits[split_for_group[row["_group_id"]]].append(row)
    return splits


def split_rows_from_manifest(
    rows: list[dict],
    split_manifest_path: Path,
) -> dict[str, list[dict]]:
    payload = json.loads(split_manifest_path.read_text(encoding="utf-8"))
    assignments = payload.get("assignments") or []
    assignment_by_id = {}
    for assignment in assignments:
        row_id = str(assignment.get("row_id") or "")
        split = str(assignment.get("split") or "")
        if not row_id or split not in {"train", "validation", "test"}:
            raise ValueError(f"Invalid split assignment: {assignment}")
        if row_id in assignment_by_id:
            raise ValueError(f"Duplicate row assignment in split manifest: {row_id}")
        assignment_by_id[row_id] = assignment

    row_ids = {row["row_id"] for row in rows}
    if set(assignment_by_id) != row_ids:
        missing = sorted(row_ids - set(assignment_by_id))
        extra = sorted(set(assignment_by_id) - row_ids)
        raise ValueError(
            f"Split manifest row IDs do not match clean pool; missing={missing[:5]}, extra={extra[:5]}"
        )

    splits = {"train": [], "validation": [], "test": []}
    group_splits: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        assignment = assignment_by_id[row["row_id"]]
        split = assignment["split"]
        expected_group = str(assignment.get("group_id") or "")
        if expected_group and expected_group != row["_group_id"]:
            raise ValueError(f"Group mismatch for row {row['row_id']}")
        splits[split].append(row)
        group_splits[row["_group_id"]].add(split)

    leaking = sorted(group_id for group_id, values in group_splits.items() if len(values) != 1)
    if leaking:
        raise ValueError(f"Split manifest divides source groups across splits: {leaking[:5]}")

    prompt_order = payload.get("test_prompt_order") or []
    if prompt_order:
        ordered_ids = [
            str(item.get("row_id") if isinstance(item, dict) else item)
            for item in prompt_order
        ]
        if set(ordered_ids) != {row["row_id"] for row in splits["test"]}:
            raise ValueError("Split manifest test_prompt_order does not match test assignments")
        order = {row_id: index for index, row_id in enumerate(ordered_ids)}
        splits["test"].sort(key=lambda row: order[row["row_id"]])
    return splits


class MajorityCodeGenerator:
    def __init__(self, train_rows: list[dict]) -> None:
        counts = Counter(row["code"] for row in train_rows)
        code = sorted(counts, key=lambda value: (-counts[value], value))[0]
        candidates = [row for row in train_rows if row["code"] == code]
        self.row = sorted(candidates, key=lambda row: row["row_id"])[0]

    def predict(self, query: str) -> tuple[dict, float, int]:
        return self.row, 1.0, 1


class RankCopyGenerator:
    def __init__(self, train_rows: list[dict], ranker: object) -> None:
        self.by_id = {row["row_id"]: row for row in train_rows}
        self.ranker = ranker

    def predict(self, query: str) -> tuple[dict, float, int]:
        ranked = self.ranker.rank(query)
        if not ranked:
            raise ValueError("Ranker returned no candidates")
        row_id, score = ranked[0]
        return self.by_id[row_id], score, 1


def import_qiskit() -> dict:
    return validity.import_qiskit()


def execute_generated_code(
    target_row: dict,
    generated_code: str,
    context_metadata: dict,
    qiskit_env: dict,
) -> dict:
    namespace = validity.execution_namespace(context_metadata, qiskit_env)
    try:
        exec(generated_code, namespace, namespace)
    except Exception as exc:
        return {
            "execution_success": False,
            "execution_error_type": type(exc).__name__,
            "execution_error_message": str(exc),
            "circuit_found": False,
        }

    circuits = validity.collect_circuits(namespace, qiskit_env)
    circuit_name, circuit = validity.choose_circuit(circuits, context_metadata)
    if circuit is None:
        return {
            "execution_success": True,
            "execution_error_type": None,
            "circuit_found": False,
            "circuit_count": 0,
        }

    return {
        "execution_success": True,
        "execution_error_type": None,
        "circuit_found": True,
        "circuit_count": len(circuits),
        "selected_circuit_name": circuit_name,
        "structural": validity.structural_result(circuit, target_row["metadata"]),
        "qasm3_export": validity.qasm_export_result(circuit, qiskit_env),
        "simulation": validity.simulation_result(circuit, qiskit_env),
    }


def normalize_code(code: str) -> str:
    return " ".join(str(code or "").split())


def prediction_record(
    target_row: dict,
    predicted_row: dict,
    score: float,
    qiskit_env: dict,
) -> dict:
    execution = execute_generated_code(
        target_row=target_row,
        generated_code=predicted_row["code"],
        context_metadata=predicted_row["metadata"],
        qiskit_env=qiskit_env,
    )
    structural = execution.get("structural", {})
    checks = structural.get("checks", {})
    return {
        "row_id": target_row["row_id"],
        "label": target_row["label"],
        "group_id": target_row["_group_id"],
        "query": target_row["query"],
        "target_file": target_row["metadata"].get("file_path"),
        "predicted_row_id": predicted_row["row_id"],
        "predicted_label": predicted_row["label"],
        "predicted_group_id": predicted_row["_group_id"],
        "predicted_file": predicted_row["metadata"].get("file_path"),
        "score": score,
        "same_label": predicted_row["label"] == target_row["label"],
        "same_group": predicted_row["_group_id"] == target_row["_group_id"],
        "exact_code_match": normalize_code(predicted_row["code"])
        == normalize_code(target_row["code"]),
        "execution": execution,
        "structural_checks": checks,
        "target_metadata": {
            "num_qubits": target_row["metadata"].get("num_qubits"),
            "num_clbits": target_row["metadata"].get("num_clbits"),
            "gate_count": target_row["metadata"].get("gate_count"),
            "gate_types": target_row["metadata"].get("gate_types"),
        },
        "predicted_metadata": {
            "num_qubits": predicted_row["metadata"].get("num_qubits"),
            "num_clbits": predicted_row["metadata"].get("num_clbits"),
            "gate_count": predicted_row["metadata"].get("gate_count"),
            "gate_types": predicted_row["metadata"].get("gate_types"),
        },
    }


def oracle_record(target_row: dict, qiskit_env: dict) -> dict:
    execution = execute_generated_code(
        target_row=target_row,
        generated_code=target_row["code"],
        context_metadata=target_row["metadata"],
        qiskit_env=qiskit_env,
    )
    checks = execution.get("structural", {}).get("checks", {})
    return {
        "row_id": target_row["row_id"],
        "label": target_row["label"],
        "group_id": target_row["_group_id"],
        "query": target_row["query"],
        "target_file": target_row["metadata"].get("file_path"),
        "predicted_row_id": target_row["row_id"],
        "predicted_label": target_row["label"],
        "predicted_group_id": target_row["_group_id"],
        "predicted_file": target_row["metadata"].get("file_path"),
        "score": 1.0,
        "same_label": True,
        "same_group": True,
        "exact_code_match": True,
        "execution": execution,
        "structural_checks": checks,
        "target_metadata": {
            "num_qubits": target_row["metadata"].get("num_qubits"),
            "num_clbits": target_row["metadata"].get("num_clbits"),
            "gate_count": target_row["metadata"].get("gate_count"),
            "gate_types": target_row["metadata"].get("gate_types"),
        },
        "predicted_metadata": {
            "num_qubits": target_row["metadata"].get("num_qubits"),
            "num_clbits": target_row["metadata"].get("num_clbits"),
            "gate_count": target_row["metadata"].get("gate_count"),
            "gate_types": target_row["metadata"].get("gate_types"),
        },
    }


def rate(count: int, denom: int) -> float:
    return count / denom if denom else 0.0


def summarize_records(records: list[dict]) -> dict:
    total = len(records)

    def count_execution(path: list[str], expected: object = True) -> int:
        count = 0
        for record in records:
            value: object = record
            for key in path:
                value = value.get(key, {}) if isinstance(value, dict) else {}
            if value == expected:
                count += 1
        return count

    summary = {
        "rows": total,
        "same_label": sum(1 for record in records if record["same_label"]),
        "same_group": sum(1 for record in records if record["same_group"]),
        "exact_code_match": sum(1 for record in records if record["exact_code_match"]),
        "execution_success": count_execution(["execution", "execution_success"]),
        "circuit_found": count_execution(["execution", "circuit_found"]),
        "structural_all_match": count_execution(["structural_checks", "all_match"]),
        "num_qubits_match": count_execution(["structural_checks", "num_qubits_match"]),
        "num_clbits_match": count_execution(["structural_checks", "num_clbits_match"]),
        "gate_count_match": count_execution(["structural_checks", "gate_count_match"]),
        "gate_types_match": count_execution(["structural_checks", "gate_types_match"]),
        "qasm3_export_success": count_execution(["execution", "qasm3_export", "success"]),
        "simulation_eligible": count_execution(["execution", "simulation", "eligible"]),
        "simulation_success": count_execution(["execution", "simulation", "success"]),
    }
    summary["rates"] = {
        key: rate(value, total)
        for key, value in summary.items()
        if key not in {"rows", "rates"} and isinstance(value, int)
    }
    summary["rates"]["simulation_success_among_eligible"] = rate(
        summary["simulation_success"], summary["simulation_eligible"]
    )

    by_label = {}
    for label in LABEL_ORDER:
        subset = [record for record in records if record["label"] == label]
        by_label[label] = summarize_records_without_by_label(subset)
    summary["by_label"] = by_label

    summary["execution_errors"] = dict(
        Counter(
            record["execution"].get("execution_error_type")
            for record in records
            if not record["execution"].get("execution_success")
        )
    )
    summary["structural_mismatch_checks"] = dict(
        Counter(
            check
            for record in records
            if record["execution"].get("circuit_found")
            and not record.get("structural_checks", {}).get("all_match")
            for check, passed in record.get("structural_checks", {}).items()
            if check != "all_match" and not passed
        )
    )
    return summary


def summarize_records_without_by_label(records: list[dict]) -> dict:
    total = len(records)
    if not total:
        return {
            "rows": 0,
            "rates": {},
        }

    fields = [
        "same_label",
        "same_group",
        "exact_code_match",
        "execution_success",
        "circuit_found",
        "structural_all_match",
        "num_qubits_match",
        "num_clbits_match",
        "gate_count_match",
        "gate_types_match",
        "qasm3_export_success",
    ]

    counts = {
        "rows": total,
        "same_label": sum(1 for record in records if record["same_label"]),
        "same_group": sum(1 for record in records if record["same_group"]),
        "exact_code_match": sum(1 for record in records if record["exact_code_match"]),
        "execution_success": sum(
            1 for record in records if record["execution"].get("execution_success")
        ),
        "circuit_found": sum(1 for record in records if record["execution"].get("circuit_found")),
        "structural_all_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("all_match")
        ),
        "num_qubits_match": sum(
            1
            for record in records
            if record.get("structural_checks", {}).get("num_qubits_match")
        ),
        "num_clbits_match": sum(
            1
            for record in records
            if record.get("structural_checks", {}).get("num_clbits_match")
        ),
        "gate_count_match": sum(
            1
            for record in records
            if record.get("structural_checks", {}).get("gate_count_match")
        ),
        "gate_types_match": sum(
            1
            for record in records
            if record.get("structural_checks", {}).get("gate_types_match")
        ),
        "qasm3_export_success": sum(
            1
            for record in records
            if record["execution"].get("qasm3_export", {}).get("success")
        ),
    }
    counts["rates"] = {field: rate(counts[field], total) for field in fields}
    return counts


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def short(text: object, limit: int = 180) -> str:
    rendered = " ".join(str(text or "").split())
    return rendered if len(rendered) <= limit else rendered[: limit - 3] + "..."


def classify_generation_failure(record: dict) -> str:
    if not record["execution"].get("execution_success"):
        return "execution_failed"
    if not record["execution"].get("circuit_found"):
        return "no_circuit_found"
    checks = record.get("structural_checks", {})
    if checks.get("all_match"):
        return "structural_match"
    if not checks.get("num_qubits_match"):
        return "width_mismatch"
    if not checks.get("gate_types_match"):
        return "gate_type_mismatch"
    if not checks.get("gate_count_match"):
        return "gate_count_mismatch"
    if not checks.get("num_clbits_match"):
        return "classical_width_mismatch"
    return "other_structural_mismatch"


def failure_taxonomy(records: list[dict]) -> list[dict]:
    failures = [record for record in records if not record.get("structural_checks", {}).get("all_match")]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for record in failures:
        by_category[classify_generation_failure(record)].append(record)

    taxonomy = []
    for category, category_records in by_category.items():
        label_counts = Counter(record["label"] for record in category_records)
        taxonomy.append(
            {
                "category": category,
                "failures": len(category_records),
                "share_of_failures": rate(len(category_records), len(failures)),
                "strict_n8": label_counts["strict_n8"],
                "extended_n8": label_counts["extended_n8"],
            }
        )
    return sorted(taxonomy, key=lambda row: (-row["failures"], row["category"]))


def representative_failures(records: list[dict], limit: int = 8) -> list[dict]:
    failures = [record for record in records if not record.get("structural_checks", {}).get("all_match")]
    ordered = sorted(
        failures,
        key=lambda record: (
            classify_generation_failure(record),
            record["label"],
            record["row_id"],
        ),
    )
    examples = []
    for record in ordered[:limit]:
        examples.append(
            {
                "row_id": record["row_id"],
                "label": record["label"],
                "failure_category": classify_generation_failure(record),
                "query": short(record["query"]),
                "target_file": record["target_file"],
                "predicted_file": record["predicted_file"],
                "predicted_label": record["predicted_label"],
                "checks": record.get("structural_checks", {}),
                "target_metadata": record["target_metadata"],
                "predicted_metadata": record["predicted_metadata"],
            }
        )
    return examples


def split_summary(splits: dict[str, list[dict]]) -> dict:
    summary = {}
    for split, rows in splits.items():
        labels = Counter(row["label"] for row in rows)
        summary[split] = {
            "rows": len(rows),
            "groups": len({row["_group_id"] for row in rows}),
            "labels": {label: labels[label] for label in LABEL_ORDER},
        }
    return summary


def group_overlap(splits: dict[str, list[dict]]) -> dict:
    groups = {
        split: {row["_group_id"] for row in rows}
        for split, rows in splits.items()
    }
    return {
        "train_validation": len(groups["train"] & groups["validation"]),
        "train_test": len(groups["train"] & groups["test"]),
        "validation_test": len(groups["validation"] & groups["test"]),
    }


def run_generators(
    train_rows: list[dict],
    test_rows: list[dict],
    qiskit_env: dict,
) -> tuple[list[dict], dict[str, list[dict]]]:
    generators = [
        (
            "majority_train_code_copy",
            "copy the most frequent code string in the training split",
            MajorityCodeGenerator(train_rows),
        ),
        (
            "bm25_code_metadata_copy",
            "copy nearest training code by BM25 over code plus non-instruction metadata",
            RankCopyGenerator(train_rows, tfidf.BM25Ranker(train_rows, "code_plus_metadata")),
        ),
        (
            "word_tfidf_code_metadata_copy",
            "copy nearest training code by word unigram/bigram TF-IDF over code plus non-instruction metadata",
            RankCopyGenerator(
                train_rows,
                tfidf.TfidfIndex(train_rows, "code_plus_metadata", tfidf.word_unigram_bigram_tokens),
            ),
        ),
        (
            "word_tfidf_train_instruction_copy",
            "copy nearest training code by word unigram/bigram TF-IDF over training instructions",
            RankCopyGenerator(
                train_rows,
                tfidf.TfidfIndex(train_rows, "instruction_upper_bound", tfidf.word_unigram_bigram_tokens),
            ),
        ),
    ]

    results = []
    records_by_name: dict[str, list[dict]] = {}
    for name, description, generator in generators:
        records = []
        for row in test_rows:
            predicted, score, rank = generator.predict(row["query"])
            record = prediction_record(row, predicted, score, qiskit_env)
            record["candidate_rank"] = rank
            records.append(record)
        summary = summarize_records(records)
        results.append(
            {
                "name": name,
                "description": description,
                "test_rows": len(test_rows),
                "summary": summary,
            }
        )
        records_by_name[name] = records

    oracle_records = [oracle_record(row, qiskit_env) for row in test_rows]
    results.append(
        {
            "name": "target_code_oracle",
            "description": "execute the held-out target code itself; included only as an evaluator upper-bound audit",
            "test_rows": len(test_rows),
            "summary": summarize_records(oracle_records),
        }
    )
    records_by_name["target_code_oracle"] = oracle_records
    return results, records_by_name


def best_generated_result(results: list[dict]) -> dict:
    candidates = [result for result in results if result["name"] != "target_code_oracle"]
    return max(
        candidates,
        key=lambda result: (
            result["summary"]["rates"]["structural_all_match"],
            result["summary"]["rates"]["gate_types_match"],
            result["summary"]["rates"]["execution_success"],
        ),
    )


def write_outputs(
    output_dir: Path,
    input_path: Path,
    rows: list[dict],
    splits: dict[str, list[dict]],
    qiskit_env: dict,
    results: list[dict],
    records_by_name: dict[str, list[dict]],
    split_manifest_path: Path | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_generation_copy_baseline_report.md"
    json_path = output_dir / "pqid_bench_generation_copy_baseline_report.json"
    split_stats = split_summary(splits)
    overlap = group_overlap(splits)
    label_counts = Counter(row["label"] for row in rows)
    best = best_generated_result(results)
    best_records = records_by_name[best["name"]]
    taxonomy = failure_taxonomy(best_records)
    failures = representative_failures(best_records)

    split_policy = (
        f"frozen split manifest `{retrieval.display_path(split_manifest_path)}`"
        if split_manifest_path is not None
        else "deterministic 80/10/10 split by source-file group, stratified by majority clean-slice label"
    )
    lines = [
        "# PQID-Bench Retrieval-Copy Generation Baseline Report",
        "",
        f"- input file: `{retrieval.display_path(input_path)}`",
        f"- clean source-code rows: `{len(rows):,}`",
        f"- split policy: {split_policy}",
        f"- group overlap: train/validation `{overlap['train_validation']}`, train/test `{overlap['train_test']}`, validation/test `{overlap['validation_test']}`",
        f"- qiskit available: `{qiskit_env.get('available')}`; version: `{qiskit_env.get('version')}`",
        "",
        "## Clean Pool",
        "",
        "| slice | rows |",
        "| --- | ---: |",
    ]
    for label in LABEL_ORDER:
        lines.append(f"| `{label}` | {label_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## Split Summary",
            "",
            "| split | rows | groups | strict_n8 | extended_n8 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for split in ["train", "validation", "test"]:
        stats = split_stats[split]
        labels = stats["labels"]
        lines.append(
            f"| `{split}` | {stats['rows']:,} | {stats['groups']:,} | "
            f"{labels['strict_n8']:,} | {labels['extended_n8']:,} |"
        )

    lines.extend(
        [
            "",
            "## Generation Baselines On Held-Out Test Instructions",
            "",
            "Each non-oracle baseline generates code by copying one training example. The copied code is executed with the copied example's source metadata context, then compared against the held-out target metadata. The oracle row executes the held-out target code itself and is included only to calibrate the evaluator.",
            "",
            "| baseline | test rows | exact code | execution | circuit found | structural match | gate types | gate count | qubits | QASM3 export |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        summary = result["summary"]
        rates = summary["rates"]
        lines.append(
            f"| `{result['name']}` | {summary['rows']:,} | {pct(rates['exact_code_match'])} | "
            f"{pct(rates['execution_success'])} | {pct(rates['circuit_found'])} | "
            f"{pct(rates['structural_all_match'])} | {pct(rates['gate_types_match'])} | "
            f"{pct(rates['gate_count_match'])} | {pct(rates['num_qubits_match'])} | "
            f"{pct(rates['qasm3_export_success'])} |"
        )

    lines.extend(
        [
            "",
            "## Best Non-Oracle Baseline By Slice",
            "",
            f"Selected baseline: `{best['name']}`.",
            "",
            "| slice | rows | structural match | gate types | gate count | qubits | execution |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in LABEL_ORDER:
        stats = best["summary"]["by_label"][label]
        rates = stats.get("rates", {})
        lines.append(
            f"| `{label}` | {stats['rows']:,} | {pct(rates.get('structural_all_match', 0.0))} | "
            f"{pct(rates.get('gate_types_match', 0.0))} | "
            f"{pct(rates.get('gate_count_match', 0.0))} | "
            f"{pct(rates.get('num_qubits_match', 0.0))} | "
            f"{pct(rates.get('execution_success', 0.0))} |"
        )

    lines.extend(
        [
            "",
            "## Best Non-Oracle Failure Taxonomy",
            "",
            "| category | failures | share | strict_n8 | extended_n8 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in taxonomy:
        lines.append(
            f"| `{row['category']}` | {row['failures']:,} | "
            f"{pct(row['share_of_failures'])} | {row['strict_n8']:,} | "
            f"{row['extended_n8']:,} |"
        )

    lines.extend(
        [
            "",
            "## Representative Best-Baseline Failures",
            "",
        ]
    )
    for index, example in enumerate(failures, start=1):
        lines.extend(
            [
                f"### Failure {index}",
                "",
                f"- slice: `{example['label']}`; category: `{example['failure_category']}`",
                f"- query: {example['query']}",
                f"- target file: `{example['target_file']}`",
                f"- copied file: `{example['predicted_file']}` (`{example['predicted_label']}`)",
                f"- checks: `{example['checks']}`",
                f"- target metadata: `{example['target_metadata']}`",
                f"- copied metadata: `{example['predicted_metadata']}`",
                "",
            ]
        )

    payload = {
        "input_file": retrieval.display_path(input_path),
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "split_policy": split_policy,
        "split_manifest": retrieval.display_path(split_manifest_path) if split_manifest_path else None,
        "split_summary": split_stats,
        "group_overlap": overlap,
        "qiskit_available": qiskit_env.get("available"),
        "qiskit_version": qiskit_env.get("version"),
        "results": results,
        "best_non_oracle_baseline": best["name"],
        "best_non_oracle_failure_taxonomy": taxonomy,
        "best_non_oracle_failures": failures,
    }
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {retrieval.display_path(report_path)}")
    print(f"Wrote {retrieval.display_path(json_path)}")


def run(input_path: Path, output_dir: Path, split_manifest_path: Path | None = None) -> None:
    rows = clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(f"Expected 734 clean source-code rows, found {len(rows)}")

    splits = split_rows(rows, split_manifest_path=split_manifest_path)
    qiskit_env = import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is unavailable: {qiskit_env.get('error')}")

    results, records_by_name = run_generators(
        train_rows=splits["train"],
        test_rows=splits["test"],
        qiskit_env=qiskit_env,
    )
    write_outputs(
        output_dir,
        input_path,
        rows,
        splits,
        qiskit_env,
        results,
        records_by_name,
        split_manifest_path=split_manifest_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--split-manifest", type=Path, default=None)
    args = parser.parse_args()

    run(args.input, args.output_dir, split_manifest_path=args.split_manifest)


if __name__ == "__main__":
    main()
