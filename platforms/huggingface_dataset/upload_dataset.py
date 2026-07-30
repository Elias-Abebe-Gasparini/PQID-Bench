"""Stage and publish the adoption-focused PQID-Bench dataset repository.

The command is inert unless ``--publish`` is supplied. The upload set is an
explicit allowlist and never mirrors the surrounding source repository.
Remote publication opens a Hugging Face pull request unless ``--direct`` is
also supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "HUGGINGFACE_DATASET_CARD.md"
CORE_RELEASE_DIR = ROOT.parent / "releases" / "core"
CORE_ARCHIVE_NAME = "PQID-Bench-v1.0.0-core.zip"
CORE_ARCHIVE = CORE_RELEASE_DIR / CORE_ARCHIVE_NAME
CORE_SIDECAR = CORE_RELEASE_DIR / f"{CORE_ARCHIVE_NAME}.sha256"
CORE_ROOT = "PQID-Bench-v1.0.0-core"
CORE_SHA256 = "d6df084c7acf7a06bc4800f25b952e26f9903ee4a69ce851ab83b7723970c647"

SOURCE_FILES: tuple[tuple[str, str], ...] = (
    ("HUGGINGFACE_DATASET_CARD.md", "README.md"),
    ("CITATION.cff", "CITATION.cff"),
    ("LICENSE.md", "LICENSE.md"),
    ("LICENSES/CC-BY-4.0.txt", "LICENSES/CC-BY-4.0.txt"),
    ("LICENSES/MIT.txt", "LICENSES/MIT.txt"),
    (
        "data/pqid_bench_clean_generation_734.jsonl",
        "data/pqid_bench_clean_generation_734.jsonl",
    ),
    (
        "data/pqid_bench_evaluator_source_734.jsonl",
        "data/pqid_bench_evaluator_source_734.jsonl",
    ),
    ("data/README.md", "data/README.md"),
    ("data/splits/README.md", "data/splits/README.md"),
    ("data/splits/train.jsonl", "data/splits/train.jsonl"),
    ("data/splits/validation.jsonl", "data/splits/validation.jsonl"),
    ("data/splits/test.jsonl", "data/splits/test.jsonl"),
    (
        "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl",
        "prompts/test_prompts_154.jsonl",
    ),
    (
        "artifacts/test_split_154/"
        "pqid_bench_external_generation_response_template_154.jsonl",
        "templates/response_template_154.jsonl",
    ),
    (
        "artifacts/test_split_154/pqid_bench_split_154_manifest.json",
        "metadata/split_manifest_154.json",
    ),
    (
        "src/pqid_bench/schemas/benchmark-record.schema.json",
        "schemas/benchmark-record.schema.json",
    ),
    (
        "src/pqid_bench/schemas/evaluation.schema.json",
        "schemas/evaluation.schema.json",
    ),
    (
        "src/pqid_bench/schemas/prompt.schema.json",
        "schemas/prompt.schema.json",
    ),
    (
        "src/pqid_bench/schemas/provider-attempt.schema.json",
        "schemas/provider-attempt.schema.json",
    ),
    (
        "src/pqid_bench/schemas/response.schema.json",
        "schemas/response.schema.json",
    ),
    (
        "src/pqid_bench/schemas/run-manifest.schema.json",
        "schemas/run-manifest.schema.json",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _core_digest(sidecar: Path) -> str:
    try:
        digest = sidecar.read_text(encoding="utf-8").split()[0].lower()
    except (FileNotFoundError, IndexError):
        raise RuntimeError(f"Core checksum sidecar is missing or empty: {sidecar}") from None
    if digest != CORE_SHA256:
        raise RuntimeError(
            f"Core checksum sidecar is not pinned to {CORE_SHA256}: {digest}"
        )
    return digest


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def stage_dataset(
    stage_dir: Path,
    *,
    core_archive: Path = CORE_ARCHIVE,
    core_sidecar: Path = CORE_SIDECAR,
) -> tuple[Path, ...]:
    """Create one exact, reviewable Hugging Face upload tree."""

    stage_dir = stage_dir.resolve()
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise RuntimeError(f"Staging directory must be empty: {stage_dir}")
    stage_dir.mkdir(parents=True, exist_ok=True)

    for source_name, destination_name in SOURCE_FILES:
        _copy(ROOT / source_name, stage_dir / destination_name)

    expected_digest = _core_digest(core_sidecar)
    observed_digest = sha256_file(core_archive)
    if observed_digest != expected_digest:
        raise RuntimeError(
            "Core archive checksum mismatch: "
            f"expected {expected_digest}, observed {observed_digest}"
        )
    _copy(core_archive, stage_dir / "downloads" / CORE_ARCHIVE_NAME)
    _copy(
        core_sidecar,
        stage_dir / "downloads" / f"{CORE_ARCHIVE_NAME}.sha256",
    )

    metadata_member = f"{CORE_ROOT}/benchmark.json"
    try:
        with zipfile.ZipFile(core_archive) as bundle:
            metadata = bundle.read(metadata_member)
    except (KeyError, zipfile.BadZipFile) as exc:
        raise RuntimeError(
            f"Core archive lacks valid metadata member {metadata_member}"
        ) from exc
    metadata_path = stage_dir / "benchmark.json"
    metadata_path.write_bytes(metadata)

    files = sorted(
        (path for path in stage_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(stage_dir).as_posix(),
    )
    inventory = stage_dir / "DATASET_FILES.tsv"
    lines = ["path\tbytes\tsha256"]
    for path in files:
        relative = path.relative_to(stage_dir).as_posix()
        lines.append(f"{relative}\t{path.stat().st_size}\t{sha256_file(path)}")
    inventory.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tuple([*files, inventory])


def print_plan(repo_id: str, stage_dir: Path, files: tuple[Path, ...]) -> None:
    total_bytes = sum(path.stat().st_size for path in files)
    print(f"Repository: {repo_id}")
    print(f"Staging directory: {stage_dir}")
    print(f"Files: {len(files):,}")
    print(f"Bytes: {total_bytes:,}")
    for path in files:
        print(f"  {path.relative_to(stage_dir).as_posix()}")


def publish_dataset(
    *,
    repo_id: str,
    stage_dir: Path,
    private: bool,
    direct: bool,
) -> object:
    """Replace the remote mirror with the staged dataset-only tree."""

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=private,
        exist_ok=True,
    )
    return api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=stage_dir,
        delete_patterns=["*"],
        create_pr=not direct,
        commit_message=(
            "Publish adoption-focused PQID-Bench v1.0.0 dataset distribution"
        ),
    )


def _run(args: argparse.Namespace, stage_dir: Path) -> None:
    stage_dir = stage_dir.resolve()
    files = stage_dataset(stage_dir)
    print_plan(args.repo_id, stage_dir, files)
    if not args.publish:
        print("Dry run only. Re-run with --publish to open a dataset update PR.")
        return
    result = publish_dataset(
        repo_id=args.repo_id,
        stage_dir=stage_dir,
        private=args.private,
        direct=args.direct,
    )
    print(f"Upload result: {result}")
    if not args.direct:
        print("Review and merge the Hugging Face pull request before using the URL.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-id",
        default="Elias-Abebe-Gasparini/PQID-Bench",
    )
    parser.add_argument("--private", action="store_true")
    parser.add_argument(
        "--stage-dir",
        type=Path,
        help="Preserve the exact upload tree in a new or empty directory",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Perform remote changes. Without this flag, only stage and print.",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Commit directly to main instead of opening a reviewable PR",
    )
    args = parser.parse_args()
    if args.direct and not args.publish:
        parser.error("--direct requires --publish")

    if args.stage_dir is not None:
        _run(args, args.stage_dir)
        return
    with tempfile.TemporaryDirectory(prefix="pqid-bench-hf-stage-") as directory:
        _run(args, Path(directory))


if __name__ == "__main__":
    main()
