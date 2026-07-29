"""Upload the PQID-Bench public tree to Hugging Face.

The command is inert unless --publish is supplied. Authentication uses the
standard Hugging Face token resolution; no local credential path is embedded.
Generated GitHub Pages assets are excluded from the dataset repository.
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "HUGGINGFACE_DATASET_CARD.md"
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
IGNORED_SUFFIXES = {".pyc", ".pyo", ".tmp"}
GENERATED_PREFIXES = {("docs", "interactive")}


def is_ignored_path(path: Path | PurePosixPath) -> bool:
    return (
        any(part in IGNORED_PARTS or part.endswith(".egg-info") for part in path.parts)
        or tuple(path.parts[:2]) in GENERATED_PREFIXES
        or path.suffix.lower() in IGNORED_SUFFIXES
    )


def package_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if is_ignored_path(relative):
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-id",
        default="Elias-Abebe-Gasparini/PQID-Bench",
    )
    parser.add_argument("--private", action="store_true")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Perform remote changes. Without this flag, only print the plan.",
    )
    args = parser.parse_args()

    files = package_files()
    total_bytes = sum(path.stat().st_size for path in files)
    print(f"Repository: {args.repo_id}")
    print(f"Files: {len(files):,}")
    print(f"Bytes: {total_bytes:,}")
    print(f"Dataset card: {CARD}")
    if not args.publish:
        print("Dry run only. Re-run with --publish to upload.")
        return

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="dataset",
        private=args.private,
        exist_ok=True,
    )
    stale_paths = [
        path
        for path in api.list_repo_files(args.repo_id, repo_type="dataset")
        if is_ignored_path(PurePosixPath(path))
    ]
    if stale_paths:
        api.delete_files(
            repo_id=args.repo_id,
            repo_type="dataset",
            delete_patterns=stale_paths,
            commit_message="Remove non-release cache files",
        )
        print(f"Removed stale remote cache files: {len(stale_paths)}")
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="dataset",
        folder_path=ROOT,
        ignore_patterns=[
            ".git/**",
            ".pytest_cache/**",
            ".ruff_cache/**",
            "__pycache__/**",
            ".ipynb_checkpoints/**",
            "*.egg-info/**",
            "build/**",
            "dist/**",
            "docs/interactive/**",
            "site/**",
            "*.pyc",
            "*.pyo",
            "*.tmp",
            "**/.git/**",
            "**/.pytest_cache/**",
            "**/.ruff_cache/**",
            "**/__pycache__/**",
            "**/.ipynb_checkpoints/**",
            "**/*.egg-info/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.tmp",
        ],
        commit_message=(
            "Synchronize pqid-bench v1.1.0 tooling with frozen "
            "PQID-Bench v1.0.0 evidence"
        ),
    )
    api.upload_file(
        repo_id=args.repo_id,
        repo_type="dataset",
        path_or_fileobj=CARD,
        path_in_repo="README.md",
        commit_message="Install PQID-Bench dataset card",
    )
    print("Upload complete.")


if __name__ == "__main__":
    main()
