"""Validate the public PQID-Bench v1.0.0 release package."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    SCRIPT_ROOT
    if (SCRIPT_ROOT / ".zenodo.json").is_file()
    else SCRIPT_ROOT / "PQID-Bench"
)

EXPECTED_VERSION = "1.0.0"
EXPECTED_PROMPTS = 154
EXPECTED_SIGNATURES = 144
EXPECTED_MODELS = 21
EXPECTED_CELLS = 3_234
EXPECTED_EXECUTIONS = 2_950
EXPECTED_ASSEMBLY_ADMISSIBLE = 2_944
EXPECTED_SIGNATURE_MATCHES = 1_703
EXPECTED_AS_GAP = 1_241
EXPECTED_REPEATABILITY_CELLS = 4_536

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".quality",
    ".ruff_cache",
    "__pycache__",
    ".ipynb_checkpoints",
    "build",
    "dist",
    "site",
}
IGNORED_FILES = {".coverage", "coverage.xml"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".tmp"}
GENERATED_PREFIXES = {
    (".github", "assets"),
    ("docs", "interactive"),
}
FORBIDDEN_RELEASE_PATHS = {
    "MANUSCRIPT_ACM_TABLES_COPY_READY.md",
    "MANUSCRIPT_ACM_TEXT_ONLY_PASTE_READY.md",
    "REFERENCES.bib",
    "SUPPLEMENTAL_DATA.md",
}
FORBIDDEN_RELEASE_TOP_LEVEL = {
    "figures",
    "notebooks",
    "paper",
    "spaces",
    "tables_copy_ready",
}
FORBIDDEN_RELEASE_SUFFIXES = {
    ".drawio",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
}
MANUSCRIPT_ONLY_SCRIPT_NAMES = {
    "build_acm_table_copy_bundle.py",
    "build_acm_transfer_ready.py",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> object:
    require(path.is_file(), f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, object]]:
    require(path.is_file(), f"Missing JSONL file: {path}")
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise AssertionError(
                    f"Invalid JSONL at {path}:{line_number}: {error}"
                ) from error
            require(isinstance(row, dict), f"Non-object JSONL row at {path}:{line_number}")
            rows.append(row)
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in PACKAGE.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(PACKAGE)
        if any(
            part in IGNORED_PARTS or part.endswith(".egg-info")
            for part in relative.parts
        ):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        if path.name in IGNORED_FILES:
            continue
        if tuple(relative.parts[:2]) in GENERATED_PREFIXES:
            continue
        if relative.as_posix() == "ARTIFACT_MANIFEST.tsv":
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(PACKAGE).as_posix())


def validate_metadata() -> None:
    zenodo = load_json(PACKAGE / ".zenodo.json")
    require(isinstance(zenodo, dict), ".zenodo.json must contain an object")
    require(zenodo.get("version") == EXPECTED_VERSION, "Zenodo version is not frozen v1.0.0")
    require(
        zenodo.get("publication_date") == "2026-07-23",
        "Zenodo publication date is not the frozen release date",
    )
    require(zenodo.get("upload_type") == "software", "Zenodo upload type must be software")
    require(zenodo.get("language") == "eng", "Zenodo language must be English")
    require(zenodo.get("license") == "cc-by-4.0", "Zenodo record license mismatch")

    description = zenodo.get("description")
    require(isinstance(description, str), "Zenodo description must be text")
    for expected in (
        "materialized training, validation, and test JSONL files",
        "E - Python execution",
        "A - quantum assembly execution",
        "M^sig - reference-signature recovery",
        "ES-Gap - Execution-Structure Gap",
        "AS-Gap - Assembly-Structure Gap",
        "pqid-bench 1.1.0",
        "pqid-bench verify RELEASE_DIR --full",
        "pqid-bench run-model",
        "pqid-bench replay",
        "pqid-bench-evaluator-1.1.0-safe-builtins",
        "pqid-bench-reference-signature-1.0.0-count-map",
    ):
        require(
            expected in description,
            f"Reader-facing Zenodo explanation is missing: {expected}",
        )

    related = zenodo.get("related_identifiers")
    require(isinstance(related, list), "Zenodo related identifiers must be a list")
    related_by_identifier = {
        item.get("identifier"): item.get("relation")
        for item in related
        if isinstance(item, dict)
    }
    expected_related = {
        "10.5281/zenodo.20674853": "isDerivedFrom",
        "https://github.com/Elias-Abebe-Gasparini/PQID-Bench": "isSupplementTo",
        "https://pypi.org/project/pqid-bench/": "isSupplementTo",
        "https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench": "isSupplementTo",
        "https://elias-abebe-gasparini.github.io/PQID-Bench/": "isDocumentedBy",
    }
    for identifier, relation in expected_related.items():
        require(
            related_by_identifier.get(identifier) == relation,
            f"Zenodo related identifier is missing or misclassified: {identifier}",
        )

    keywords = zenodo.get("keywords")
    require(isinstance(keywords, list), "Zenodo keywords must be a list")
    for expected in (
        "OpenQASM 3",
        "LLM evaluation",
        "benchmark dataset",
        "reproducible research",
        "Python package",
    ):
        require(expected in keywords, f"Zenodo discovery keyword is missing: {expected}")

    citation = (PACKAGE / "CITATION.cff").read_text(encoding="utf-8")
    require('version: "1.0.0"' in citation, "CITATION.cff version mismatch")
    require(
        "https://github.com/Elias-Abebe-Gasparini/PQID-Bench" in citation,
        "CITATION.cff GitHub endpoint mismatch",
    )

    for path in (
        PACKAGE / "README.md",
        PACKAGE / "HUGGINGFACE_DATASET_CARD.md",
        PACKAGE / "ZENODO_METADATA.md",
    ):
        text = path.read_text(encoding="utf-8")
        require("20024477" not in text, f"Stale source-dataset DOI remains in {path}")

    zenodo_sheet = (PACKAGE / "ZENODO_METADATA.md").read_text(encoding="utf-8")
    require(
        "reserved version DOI" not in zenodo_sheet,
        "Human-readable Zenodo metadata still describes the DOI as reserved",
    )
    for expected in (
        "The deposit is self-contained",
        "## Measurement Nomenclature",
        "## Python Package",
        "## Version Crosswalk",
        "10.5281/zenodo.21649752",
    ):
        require(
            expected in zenodo_sheet,
            f"Human-readable Zenodo metadata is missing: {expected}",
        )

    narrative_paths = (
        PACKAGE / ".zenodo.json",
        PACKAGE / "CITATION.cff",
        PACKAGE / "HUGGINGFACE_DATASET_CARD.md",
        PACKAGE / "ZENODO_METADATA.md",
        PACKAGE / "docs" / "RELEASE_NOTES_v1.0.0.md",
    )
    for path in narrative_paths:
        text = path.read_text(encoding="utf-8")
        for expected in ("2,944", "38.37", "99.52"):
            require(
                expected in text,
                f"Assembly-layer headline {expected} is missing from {path}",
            )


def validate_clean_population() -> None:
    rows = load_jsonl(PACKAGE / "data" / "pqid_bench_clean_generation_734.jsonl")
    require(len(rows) == 734, f"Expected 734 clean rows, found {len(rows)}")

    labels: Counter[str] = Counter()
    for row in rows:
        metadata = row.get("metadata")
        require(isinstance(metadata, dict), "Clean row is missing metadata")
        label = metadata.get("benchmark_view_membership")
        require(isinstance(label, str), "Clean row is missing benchmark view membership")
        labels[label] += 1
        require(
            metadata.get("pqid_bench_effective_release_bucket") == "public_open",
            "Clean row is not release-cleared",
        )
    require(labels == Counter({"strict_n8": 415, "extended_n8": 319}), str(labels))

    evaluator_rows = load_jsonl(PACKAGE / "data" / "pqid_bench_evaluator_source_734.jsonl")
    require(
        len(evaluator_rows) == 734,
        f"Expected 734 evaluator-source rows, found {len(evaluator_rows)}",
    )
    roles: Counter[str] = Counter()
    row_ids: set[str] = set()
    for row in evaluator_rows:
        metadata = row.get("metadata")
        require(isinstance(metadata, dict), "Evaluator-source row is missing metadata")
        role = metadata.get("seed_role")
        require(isinstance(role, str), "Evaluator-source row is missing seed_role")
        roles[role] += 1
        require(bool(str(row.get("input") or "").strip()), "Evaluator-source row has empty input")
        require(bool(str(row.get("output") or "").strip()), "Evaluator-source row has empty output")
        row_id = str(metadata.get("content_hash") or "")
        require(bool(row_id), "Evaluator-source row is missing content_hash")
        require(row_id not in row_ids, f"Duplicate evaluator-source content_hash: {row_id}")
        row_ids.add(row_id)
    require(
        roles == Counter({"gold_generation": 415, "broad_generation": 319}),
        f"Unexpected evaluator-source roles: {roles}",
    )


def validate_split() -> set[str]:
    split_dir = PACKAGE / "artifacts" / "test_split_154"
    manifest = load_json(split_dir / "pqid_bench_split_154_manifest.json")
    require(isinstance(manifest, dict), "Split manifest must contain an object")
    split_counts = manifest["split_counts"]
    require(split_counts["train"]["rows"] == 514, "Training split must contain 514 rows")
    require(split_counts["validation"]["rows"] == 66, "Validation split must contain 66 rows")
    require(split_counts["test"]["rows"] == EXPECTED_PROMPTS, "Test split must contain 154 rows")
    require(
        split_counts["test"]["unique_target_signatures"] == EXPECTED_SIGNATURES,
        "Test split must contain 144 target signatures",
    )
    require(
        manifest["group_overlap"]
        == {"train_test": 0, "train_validation": 0, "validation_test": 0},
        "Split-group overlap is nonzero",
    )

    evaluator_rows = load_jsonl(
        PACKAGE / "data" / "pqid_bench_evaluator_source_734.jsonl"
    )
    evaluator_by_id: dict[str, dict[str, object]] = {}
    source_order: list[str] = []
    for row in evaluator_rows:
        metadata = row.get("metadata")
        require(isinstance(metadata, dict), "Evaluator split source is missing metadata")
        row_id = str(metadata.get("content_hash") or "")
        require(bool(row_id), "Evaluator split source is missing content_hash")
        require(row_id not in evaluator_by_id, f"Duplicate evaluator-source ID: {row_id}")
        evaluator_by_id[row_id] = row
        source_order.append(row_id)

    assignments = manifest.get("assignments")
    require(isinstance(assignments, list), "Split manifest has no assignments array")
    split_by_id: dict[str, str] = {}
    for assignment in assignments:
        require(isinstance(assignment, dict), "Split assignment is not an object")
        row_id = str(assignment.get("row_id") or "")
        split = str(assignment.get("split") or "")
        require(split in {"train", "validation", "test"}, f"Unexpected split: {split}")
        require(bool(row_id), "Split assignment is missing row_id")
        require(row_id not in split_by_id, f"Duplicate split assignment: {row_id}")
        split_by_id[row_id] = split
    require(
        set(split_by_id) == set(evaluator_by_id),
        "Split assignments do not exactly cover the 734 evaluator records",
    )

    expected_counts = {"train": 514, "validation": 66, "test": 154}
    materialized_ids: set[str] = set()
    for split, expected_count in expected_counts.items():
        rows = load_jsonl(PACKAGE / "data" / "splits" / f"{split}.jsonl")
        expected_rows = [
            evaluator_by_id[row_id]
            for row_id in source_order
            if split_by_id[row_id] == split
        ]
        require(
            rows == expected_rows,
            f"Materialized {split} split differs from the frozen evaluator source",
        )
        require(
            len(rows) == expected_count,
            f"Materialized {split} split must contain {expected_count} rows",
        )
        split_ids = {
            str(row["metadata"]["content_hash"])
            for row in rows
            if isinstance(row.get("metadata"), dict)
        }
        require(
            len(split_ids) == expected_count,
            f"Materialized {split} split IDs are not unique",
        )
        require(
            materialized_ids.isdisjoint(split_ids),
            f"Materialized {split} split overlaps another split",
        )
        materialized_ids.update(split_ids)
    require(
        materialized_ids == set(evaluator_by_id),
        "Materialized splits do not form a complete 734-row partition",
    )

    prompts = load_jsonl(split_dir / "pqid_bench_external_generation_prompts_154.jsonl")
    prompt_ids = [row.get("prompt_id") for row in prompts]
    require(len(prompt_ids) == EXPECTED_PROMPTS, "Prompt file does not contain 154 rows")
    require(len(set(prompt_ids)) == EXPECTED_PROMPTS, "Prompt IDs are not unique")
    frozen_order = [row["prompt_id"] for row in manifest["test_prompt_order"]]
    require(prompt_ids == frozen_order, "Prompt file order differs from the frozen manifest")
    return set(prompt_ids)


def response_logs() -> list[Path]:
    external = PACKAGE / "artifacts" / "external_model_batches_154"
    paths = sorted(
        path
        for path in (external / "responses").glob("*_responses.jsonl")
        if "template" not in path.name
    )
    for control in ("qiskit_mistral", "mistral_parent_control"):
        control_paths = sorted(
            path
            for path in (external / control / "responses").glob("*_responses.jsonl")
            if "template" not in path.name
        )
        require(len(control_paths) == 1, f"Expected one canonical response log for {control}")
        paths.extend(control_paths)
    return paths


def validate_external_matrix(prompt_ids: set[str]) -> None:
    logs = response_logs()
    require(len(logs) == EXPECTED_MODELS, f"Expected 21 response logs, found {len(logs)}")
    seen_routes: set[tuple[object, object]] = set()
    for path in logs:
        rows = load_jsonl(path)
        ids = {row.get("prompt_id") for row in rows}
        require(ids == prompt_ids, f"Canonical prompt coverage mismatch in {path}")
        canonical_by_prompt: dict[object, dict[str, object]] = {}
        for row in rows:
            canonical_by_prompt[row.get("prompt_id")] = row
        require(
            len(canonical_by_prompt) == EXPECTED_PROMPTS,
            f"Canonical response count mismatch in {path}",
        )
        sample = rows[-1]
        route = (sample.get("provider"), sample.get("model") or sample.get("resolved_model"))
        require(route not in seen_routes, f"Duplicate provider/model route: {route}")
        seen_routes.add(route)

    analysis_path = (
        PACKAGE
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_item_failure_matrix_analysis_21.json"
    )
    analysis = load_json(analysis_path)
    require(isinstance(analysis, dict), "Final matrix analysis must contain an object")
    require(analysis["model_count"] == EXPECTED_MODELS, "Final analysis model count mismatch")
    require(analysis["prompt_count"] == EXPECTED_PROMPTS, "Final analysis prompt count mismatch")
    require(analysis["evaluation_count"] == EXPECTED_CELLS, "Final analysis cell count mismatch")
    require(analysis["overall"]["n"] == EXPECTED_CELLS, "Final overall denominator mismatch")

    by_model = analysis["by_model"]
    executions = sum(round(row["execution_success"] * row["n"]) for row in by_model)
    matches = sum(round(row["structural_all_match"] * row["n"]) for row in by_model)
    require(executions == EXPECTED_EXECUTIONS, f"Expected 2,950 executions, found {executions}")
    require(
        matches == EXPECTED_SIGNATURE_MATCHES,
        f"Expected 1,703 signature matches, found {matches}",
    )

    assembly_path = (
        PACKAGE
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_operational_assembly_layer_audit.json"
    )
    assembly = load_json(assembly_path)
    require(isinstance(assembly, dict), "Assembly-layer audit must contain an object")
    require(assembly["panel"]["cells"] == EXPECTED_CELLS, "Assembly audit denominator mismatch")
    require(assembly["counts"]["E"] == EXPECTED_EXECUTIONS, "Assembly audit E count mismatch")
    require(
        assembly["counts"]["A"] == EXPECTED_ASSEMBLY_ADMISSIBLE,
        "Assembly-admissibility count mismatch",
    )
    require(
        assembly["counts"]["M_sig"] == EXPECTED_SIGNATURE_MATCHES,
        "Assembly audit signature count mismatch",
    )
    require(assembly["counts"]["E_without_A"] == 6, "Expected six E=1, A=0 cells")
    require(
        assembly["counts"]["A_without_M_sig"] == 1_241,
        "AS-Gap count mismatch",
    )
    require(
        assembly["gaps"]["AS_signature_count"] == EXPECTED_AS_GAP,
        "Named AS-Gap audit count mismatch",
    )
    require(
        assembly["counts"]["M_sig_without_A"] == 0,
        "Expected zero M_sig=1, A=0 cells",
    )
    require(
        assembly["nesting"]
        == {
            "validated_chain": "M_sig <= A <= E",
            "A_not_E": 0,
            "M_sig_not_A": 0,
            "M_sig_not_E": 0,
        },
        "Assembly-layer pointwise nesting mismatch",
    )

    ordered_cells = load_jsonl(
        PACKAGE
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_ordered_operand_cell_audit.jsonl"
    )
    require(len(ordered_cells) == EXPECTED_CELLS, "Ordered cell audit denominator mismatch")
    require(
        sum(bool(row.get("report_assembly_admissible")) for row in ordered_cells)
        == EXPECTED_ASSEMBLY_ADMISSIBLE,
        "Ordered cell audit assembly count mismatch",
    )
    require(
        sum(
            bool(row.get("report_signature_match"))
            and not bool(row.get("report_assembly_admissible"))
            for row in ordered_cells
        )
        == 0,
        "Ordered cell audit has signature matches outside assembly admissibility",
    )

    matrix_path = (
        PACKAGE
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_model_by_prompt_structural_matrix_21.csv"
    )
    with matrix_path.open(encoding="utf-8", newline="") as handle:
        matrix_rows = list(csv.DictReader(handle))
    require(len(matrix_rows) == EXPECTED_PROMPTS, "Structural matrix row count mismatch")
    require(
        {row["prompt_id"] for row in matrix_rows} == prompt_ids,
        "Structural matrix prompt coverage mismatch",
    )
    model_names = {row["group"] for row in by_model}
    require(
        model_names.issubset(matrix_rows[0]),
        "Structural matrix does not expose all 21 model columns",
    )


def validate_repeatability() -> None:
    analysis_dir = (
        PACKAGE
        / "artifacts"
        / "stochastic_repeatability_21x72"
        / "consolidated"
        / "analysis"
    )
    path = analysis_dir / "pqid_bench_stochastic_repeatability_cell_outcomes.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(
        len(rows) == EXPECTED_REPEATABILITY_CELLS,
        f"Expected 4,536 repeatability cells, found {len(rows)}",
    )
    require(len({row["model"] for row in rows}) == 21, "Repeatability model count mismatch")
    require(len({row["prompt_id"] for row in rows}) == 72, "Repeatability prompt count mismatch")
    require({row["run"] for row in rows} == {"1", "2", "3"}, "Repeatability runs mismatch")
    provider_errors = sum(row["provider_error"] == "1" for row in rows)
    transport_affected = sum(row["transport_affected"] == "1" for row in rows)
    require(
        provider_errors == 432,
        f"Expected 432 preserved provider-error cells, found {provider_errors}",
    )
    require(
        transport_affected == 628,
        f"Expected 628 transport-affected cells, found {transport_affected}",
    )
    require(
        all(
            row["transport_affected"] == "1"
            for row in rows
            if row["provider_error"] == "1"
        ),
        "A provider-error cell is not marked as transport affected",
    )


def validate_manifest() -> None:
    manifest_path = PACKAGE / "ARTIFACT_MANIFEST.tsv"
    require(manifest_path.is_file(), "Missing ARTIFACT_MANIFEST.tsv")
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    expected_paths = {
        path.relative_to(PACKAGE).as_posix(): path for path in public_files()
    }
    manifest_paths = {row["path"] for row in rows}
    require(
        manifest_paths == set(expected_paths),
        "Artifact manifest paths do not exactly match the public package",
    )
    for row in rows:
        path = expected_paths[row["path"]]
        require(int(row["bytes"]) == path.stat().st_size, f"Byte count mismatch: {row['path']}")
        require(sha256(path) == row["sha256"], f"SHA-256 mismatch: {row['path']}")


def validate_release_scope() -> None:
    violations: list[str] = []
    for path in public_files():
        relative = path.relative_to(PACKAGE)
        top_level = relative.parts[0].lower() if relative.parts else ""
        if top_level in FORBIDDEN_RELEASE_TOP_LEVEL:
            violations.append(relative.as_posix())
        elif path.suffix.lower() in FORBIDDEN_RELEASE_SUFFIXES:
            violations.append(relative.as_posix())
        elif (
            path.name in FORBIDDEN_RELEASE_PATHS
            or path.name in MANUSCRIPT_ONLY_SCRIPT_NAMES
        ):
            violations.append(relative.as_posix())
    require(
        not violations,
        "Manuscript-facing source or publication output found in public "
        f"release: {sorted(set(violations))}",
    )


def validate_private_material() -> None:
    needles = (
        b"C:\\Users\\",
        b"C:/Users/",
        b"GITHUB_MODELS_API_KEY_2",
        b"ACM_TQC_API_KEY",
        b"OPENAI_API_KEY_PQID",
    )
    binary_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}
    violations: list[str] = []
    for path in public_files():
        if path.name in {
            Path(__file__).name,
            "build_pqid_bench_public_release.py",
        }:
            continue
        if path.suffix.lower() in binary_suffixes:
            continue
        payload = path.read_bytes()
        if any(needle in payload for needle in needles):
            violations.append(path.relative_to(PACKAGE).as_posix())
    require(not violations, f"Private path or credential marker found in: {violations}")


def main() -> None:
    require(PACKAGE.is_dir(), f"Release package not found: {PACKAGE}")
    validate_metadata()
    validate_clean_population()
    prompt_ids = validate_split()
    validate_external_matrix(prompt_ids)
    validate_repeatability()
    validate_release_scope()
    validate_manifest()
    validate_private_material()

    print(f"Validated release package: {PACKAGE}")
    print("Clean population: 734 (415 strict, 319 extended)")
    print("Split: 514 train / 66 validation / 154 test; 144 test signatures")
    print("Materialized split JSONLs: lossless 734-row partition verified")
    print("External matrix: 21 models x 154 prompts = 3,234 cells")
    print(
        "Headline counts: 2,950 executable circuits; "
        "2,944 assembly-admissible; 1,703 reference-signature matches"
    )
    print("Repeatability audit: 21 models x 72 prompts x 3 runs = 4,536 cells")
    print(f"Manifest entries: {len(public_files()):,}")
    print("Release-scope scan: manuscript source and publication derivatives excluded")
    print("Private-path scan: clear")


if __name__ == "__main__":
    main()
