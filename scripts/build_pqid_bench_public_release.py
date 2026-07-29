"""Build the public PQID-Bench v1.0.0 release package.

The builder keeps the archived PQID v1.0.2 dataset separate from the benchmark
companion. It copies only the public scientific evidence and canonical
external-model traces needed for the reported matrix, materializes the
repository-cleared 734-row clean generation view, and writes a complete
SHA-256 manifest. Unpublished manuscript source and manuscript-facing
publication derivatives are excluded by policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

try:
    from materialize_pqid_bench_splits import materialize_splits
except ModuleNotFoundError:
    from scripts.materialize_pqid_bench_splits import materialize_splits


ROOT = Path(__file__).resolve().parents[1]
PQID_ROOT = ROOT.parents[1]
PACKAGE = ROOT / "PQID-Bench"
RELEASES = ROOT / "releases"
VERSION = "1.0.0"

SOURCE_DATA = (
    PQID_ROOT
    / "data"
    / "processed"
    / "pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl"
)
SEEDED_EVALUATOR_SOURCE = (
    PQID_ROOT
    / "data"
    / "processed"
    / "seed_drafts_quality_aware_source_code_v1.jsonl"
)

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

EXTERNAL_PRIMARY_DIRS = (
    "requests",
    "responses",
    "evaluations",
    "manifests",
    "audit",
    "canonicalization_audit",
)

EXTERNAL_CONTROL_DIRS = (
    "requests",
    "responses",
    "evaluations",
    "manifests",
)

PUBLIC_PREREGISTRATION_DIRS = (
    "contract",
    "panel",
    "protocol",
    "requests",
)

IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".ipynb_checkpoints",
    "build",
    "dist",
    "site",
}

IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(source)
    ignore_patterns = tuple(f"*{suffix}" for suffix in FORBIDDEN_RELEASE_SUFFIXES)
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*ignore_patterns),
    )


def copy_matching(source: Path, destination: Path, patterns: tuple[str, ...]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for pattern in patterns:
        for path in sorted(source.glob(pattern)):
            if path.is_file():
                copy_file(path, destination / path.name)


def reset_generated_mirrors() -> None:
    """Remove generated mirrors so obsolete files cannot survive a rebuild."""

    for relative in (
        "artifacts",
        "data",
        "figures",
        "notebooks",
        "paper",
        "scripts",
        "spaces",
        "tables_copy_ready",
    ):
        destination = PACKAGE / relative
        if destination.exists():
            shutil.rmtree(destination)


def sync_reproducibility_map() -> None:
    copy_file(ROOT / "REPRODUCIBILITY_ARTIFACTS.md", PACKAGE / "REPRODUCIBILITY_ARTIFACTS.md")


def sync_scripts() -> None:
    destination = PACKAGE / "scripts"
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "scripts").glob("*.py")):
        if source.name not in MANUSCRIPT_ONLY_SCRIPT_NAMES:
            copy_file(source, destination / source.name)
    copy_file(
        PQID_ROOT / "scripts" / "05_benchmarking" / "build_pqid_bench_tables.py",
        destination / "build_pqid_bench_tables.py",
    )


def sync_root_artifacts() -> None:
    source = ROOT / "artifacts"
    destination = PACKAGE / "artifacts"
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv", ".tsv", ".md"}:
            copy_file(path, destination / path.name)


def sync_frozen_artifacts() -> None:
    source = ROOT / "artifacts"
    destination = PACKAGE / "artifacts"
    copy_tree(source / "analysis_154", destination / "analysis_154")
    copy_tree(source / "test_split_154", destination / "test_split_154")
    copy_tree(source / "external_model_batches", destination / "external_model_batches")

    external_source = source / "external_model_batches_154"
    external_destination = destination / "external_model_batches_154"
    external_destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(external_source.iterdir()):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".csv", ".tsv"}:
            copy_file(path, external_destination / path.name)

    for directory in EXTERNAL_PRIMARY_DIRS:
        copy_tree(external_source / directory, external_destination / directory)

    for control in ("qiskit_mistral", "mistral_parent_control"):
        for directory in EXTERNAL_CONTROL_DIRS:
            copy_tree(
                external_source / control / directory,
                external_destination / control / directory,
            )

    repeat_source = source / "stochastic_repeatability_21x72"
    repeat_destination = destination / "stochastic_repeatability_21x72"
    copy_tree(repeat_source / "consolidated", repeat_destination / "consolidated")
    copy_tree(repeat_source / "panel", repeat_destination / "panel")
    for filename in (
        "PRESPECIFIED_AUGMENTATION_PROTOCOL.md",
        "RUN_STOCHASTIC_REPEATABILITY_AUGMENTATION.md",
    ):
        source_file = repeat_source / filename
        if source_file.is_file():
            copy_file(source_file, repeat_destination / filename)

    prereg_source = repeat_source / "preregistration_bundle_20260716_pretransmission"
    prereg_destination = repeat_destination / "preregistration_bundle_20260716_pretransmission"
    for directory in PUBLIC_PREREGISTRATION_DIRS:
        copy_tree(prereg_source / directory, prereg_destination / directory)
    copy_file(
        prereg_source / "audit" / "pretransmission_empty_assertion.json",
        prereg_destination / "audit" / "pretransmission_empty_assertion.json",
    )
    for filename in ("README.md", "BUNDLE_MANIFEST.json", "SHA256SUMS.txt"):
        copy_file(prereg_source / filename, prereg_destination / filename)


def sanitize_public_metadata() -> None:
    """Remove machine-local path prefixes from public metadata copies."""

    split_manifest = (
        PACKAGE
        / "artifacts"
        / "test_split_154"
        / "pqid_bench_split_154_manifest.json"
    )
    payload = split_manifest.read_text(encoding="utf-8")
    marker = "/PQID/"
    data = json.loads(payload)

    def visit(value: object) -> object:
        if isinstance(value, dict):
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, str):
            normalized = value.replace("\\", "/")
            if marker in normalized and (
                normalized.startswith("C:/Users/")
                or normalized.startswith("C:/Users\\")
            ):
                return "PQID/" + normalized.split(marker, 1)[1]
        return value

    split_manifest.write_text(
        json.dumps(visit(data), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def materialize_clean_generation_view() -> None:
    output_dir = PACKAGE / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "pqid_bench_clean_generation_734.jsonl"
    evaluator_output = output_dir / "pqid_bench_evaluator_source_734.jsonl"

    counts = {"strict_n8": 0, "extended_n8": 0}
    with SOURCE_DATA.open("r", encoding="utf-8") as source, output.open(
        "w", encoding="utf-8", newline="\n"
    ) as destination:
        for line in source:
            row = json.loads(line)
            metadata = row.get("metadata") or {}
            label = metadata.get("benchmark_view_membership")
            if label not in counts:
                continue
            counts[label] += 1
            metadata["pqid_bench_effective_release_bucket"] = "public_open"
            metadata["pqid_bench_release_clearance_basis"] = (
                "repository-level license evidence documented in "
                "artifacts/pqid_bench_readiness_and_packaging_report"
            )
            row["metadata"] = metadata
            destination.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    if counts != {"strict_n8": 415, "extended_n8": 319}:
        raise AssertionError(f"Unexpected clean generation counts: {counts}")

    evaluator_role_counts = {"gold_generation": 0, "broad_generation": 0}
    with SEEDED_EVALUATOR_SOURCE.open("r", encoding="utf-8") as source, evaluator_output.open(
        "w", encoding="utf-8", newline="\n"
    ) as destination:
        for line in source:
            row = json.loads(line)
            metadata = row.get("metadata") or {}
            role = metadata.get("seed_role")
            if role not in evaluator_role_counts:
                continue
            evaluator_role_counts[role] += 1
            destination.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    if evaluator_role_counts != {"gold_generation": 415, "broad_generation": 319}:
        raise AssertionError(f"Unexpected evaluator source counts: {evaluator_role_counts}")

    materialize_splits(
        evaluator_output,
        PACKAGE
        / "artifacts"
        / "test_split_154"
        / "pqid_bench_split_154_manifest.json",
        output_dir / "splits",
    )

    data_readme = """# PQID-Bench Clean Generation View

`pqid_bench_clean_generation_734.jsonl` contains the frozen clean generation
population used to construct PQID-Bench:

- `415` `strict_n8` rows;
- `319` `extended_n8` rows;
- `734` rows in total.

`pqid_bench_evaluator_source_734.jsonl` contains the corresponding seeded
prompt/code records used by the frozen split and executable evaluator. It
contains `415` `gold_generation` and `319` `broad_generation` records. The two
files are deliberately separate: the first preserves the governance view,
while the second preserves the exact evaluator input contract.

`splits/train.jsonl`, `splits/validation.jsonl`, and `splits/test.jsonl`
materialize the complete evaluator source as a lossless `514/66/154`
partition. They are generated from the frozen assignment manifest by matching
its `row_id` to each evaluator record's `metadata.content_hash`. The three
files contain every evaluator record exactly once.

Historical row-level release fields are retained for audit. The added
`pqid_bench_effective_release_bucket` and
`pqid_bench_release_clearance_basis` fields record the repository-level
clearance decision used by the benchmark package. The deterministic
train/validation/test assignment remains authoritative under
`artifacts/test_split_154/`; the separate JSONL files are convenience views.
No parent PQID download is required to use the frozen benchmark or its splits.
The source PQID v1.0.2 dataset remains a separately versioned object with DOI
`10.5281/zenodo.20674853`.
"""
    (output_dir / "README.md").write_text(data_readme, encoding="utf-8", newline="\n")


def public_files() -> list[Path]:
    files = []
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
        if relative.as_posix() == "ARTIFACT_MANIFEST.tsv":
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(PACKAGE).as_posix())


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
    if violations:
        joined = "\n".join(f"- {path}" for path in sorted(set(violations)))
        raise RuntimeError(
            "Manuscript-facing source or publication output is forbidden "
            "in the public release:\n"
            f"{joined}"
        )


def write_manifest() -> None:
    lines = ["path\tbytes\tsha256"]
    for path in public_files():
        relative = path.relative_to(PACKAGE).as_posix()
        lines.append(f"{relative}\t{path.stat().st_size}\t{sha256(path)}")
    (PACKAGE / "ARTIFACT_MANIFEST.tsv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


def scan_private_paths() -> None:
    violations: list[str] = []
    needles = (
        b"C:\\Users\\",
        b"C:/Users/",
        b"GITHUB_MODELS_API_KEY_2",
        b"ACM_TQC_API_KEY",
        b"OPENAI_API_KEY_PQID",
    )
    for path in public_files():
        if path.name in {
            Path(__file__).name,
            "validate_pqid_bench_public_release.py",
        }:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc"}:
            continue
        payload = path.read_bytes()
        if any(needle in payload for needle in needles):
            violations.append(path.relative_to(PACKAGE).as_posix())
    if violations:
        joined = "\n".join(f"- {path}" for path in violations)
        raise RuntimeError(f"Private local-path material remains in the package:\n{joined}")


def create_archive() -> Path:
    RELEASES.mkdir(parents=True, exist_ok=True)
    archive = RELEASES / f"PQID-Bench-v{VERSION}-frozen.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
        for path in public_files() + [PACKAGE / "ARTIFACT_MANIFEST.tsv"]:
            relative = Path(f"PQID-Bench-v{VERSION}") / path.relative_to(PACKAGE)
            handle.write(path, relative.as_posix())
    checksum = RELEASES / f"PQID-Bench-v{VERSION}-frozen.zip.sha256"
    checksum.write_text(
        f"{sha256(archive)}  {archive.name}\n", encoding="ascii", newline="\n"
    )
    return archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Also create the frozen ZIP and its SHA-256 sidecar.",
    )
    args = parser.parse_args()

    reset_generated_mirrors()
    sync_reproducibility_map()
    sync_scripts()
    sync_root_artifacts()
    sync_frozen_artifacts()
    sanitize_public_metadata()
    materialize_clean_generation_view()
    validate_release_scope()
    scan_private_paths()
    write_manifest()

    print(f"Release package synchronized: {PACKAGE}")
    print(f"Manifest entries: {len(public_files()):,}")
    if args.archive:
        archive = create_archive()
        print(f"Archive: {archive}")
        print(f"Archive SHA-256: {sha256(archive)}")


if __name__ == "__main__":
    main()
