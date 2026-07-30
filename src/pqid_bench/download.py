"""Verified acquisition of compact PQID-Bench benchmark releases."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO

from .manifest import verify_manifest
from .version import BENCHMARK_RELEASE, PACKAGE_VERSION

MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_EXPANDED_BYTES = 4 * 1024 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 20_000


@dataclass(frozen=True, slots=True)
class CoreRelease:
    """One immutable compact benchmark distribution."""

    version: str
    url: str
    sha256: str
    archive_name: str
    root_name: str


@dataclass(frozen=True, slots=True)
class DownloadResult:
    """Result of downloading or reusing a verified core release."""

    version: str
    release_dir: str
    archive_path: str
    source_url: str
    sha256: str
    manifest_entries: int
    downloaded: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "release_dir": self.release_dir,
            "archive_path": self.archive_path,
            "source_url": self.source_url,
            "sha256": self.sha256,
            "manifest_entries": self.manifest_entries,
            "downloaded": self.downloaded,
            "reused": not self.downloaded,
        }


OFFICIAL_CORE_RELEASES: dict[str, CoreRelease] = {
    "1.0.0": CoreRelease(
        version="1.0.0",
        url=(
            "https://huggingface.co/datasets/Elias-Abebe-Gasparini/"
            "PQID-Bench/resolve/main/downloads/PQID-Bench-v1.0.0-core.zip"
        ),
        sha256=(
            "d6df084c7acf7a06bc4800f25b952e26f9903ee4a69ce851ab83b7723970c647"
        ),
        archive_name="PQID-Bench-v1.0.0-core.zip",
        root_name="PQID-Bench-v1.0.0-core",
    )
}


def default_cache_root() -> Path:
    """Return the user-overridable cache root."""

    configured = os.environ.get("PQID_BENCH_CACHE_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "pqid-bench"


def _normalized_sha256(value: str) -> str:
    digest = value.strip().lower()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("SHA-256 must contain exactly 64 hexadecimal characters")
    return digest


def _validate_https_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Benchmark downloads require an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError("Download URL must not embed credentials")


def _release_metadata(release_dir: Path, version: str) -> tuple[int, dict[str, object]]:
    metadata_path = release_dir / "benchmark.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Core release lacks benchmark.json: {release_dir}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Core release has invalid benchmark.json: {release_dir}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("Core release benchmark.json must contain a JSON object")
    if metadata.get("benchmark_release") != version:
        raise ValueError(
            "Core release version mismatch: "
            f"expected {version!r}, observed {metadata.get('benchmark_release')!r}"
        )
    if metadata.get("distribution_profile") != "core":
        raise ValueError("Downloaded artifact is not a PQID-Bench core distribution")
    verification = verify_manifest(release_dir)
    if not verification.valid:
        details = verification.to_dict()
        raise ValueError(f"Core release manifest verification failed: {details}")
    return verification.checked, metadata


def _download_archive(
    url: str,
    destination: Path,
    *,
    expected_sha256: str,
    timeout_seconds: int,
) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"pqid-bench/{PACKAGE_VERSION}"},
    )
    digest = hashlib.sha256()
    bytes_written = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            _validate_https_url(final_url)
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > MAX_ARCHIVE_BYTES:
                raise RuntimeError("Remote core archive exceeds the download safety limit")
            with destination.open("wb") as handle:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    bytes_written += len(block)
                    if bytes_written > MAX_ARCHIVE_BYTES:
                        raise RuntimeError(
                            "Core archive exceeds the download safety limit"
                        )
                    digest.update(block)
                    handle.write(block)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Unable to download PQID-Bench core release: {exc}") from exc
    observed = digest.hexdigest()
    if observed != expected_sha256:
        raise RuntimeError(
            "Downloaded archive SHA-256 mismatch: "
            f"expected {expected_sha256}, observed {observed}"
        )


def _safe_member_path(info: zipfile.ZipInfo) -> PurePosixPath:
    name = info.filename
    if not name or "\x00" in name or "\\" in name:
        raise ValueError(f"Unsafe ZIP member name: {name!r}")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    if not relative.parts or ":" in relative.parts[0]:
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode):
        raise ValueError(f"Symbolic links are not allowed in core archives: {name}")
    return relative


def _copy_member(source: IO[bytes], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        shutil.copyfileobj(source, output, length=1024 * 1024)


def _extract_verified_archive(
    archive: Path,
    destination: Path,
    *,
    expected_root: str,
) -> Path:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    normalized_names: set[str] = set()
    roots: set[str] = set()
    expanded_bytes = 0
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise ValueError("Core archive contains too many members")
            for info in members:
                relative = _safe_member_path(info)
                normalized = relative.as_posix().rstrip("/").casefold()
                if normalized in normalized_names:
                    raise ValueError(
                        f"Core archive contains a duplicate member: {info.filename}"
                    )
                normalized_names.add(normalized)
                roots.add(relative.parts[0])
                expanded_bytes += info.file_size
                if expanded_bytes > MAX_EXPANDED_BYTES:
                    raise ValueError("Expanded core archive exceeds the safety limit")
                target = (destination / Path(*relative.parts)).resolve()
                if target != destination and destination not in target.parents:
                    raise ValueError(f"ZIP member escapes extraction root: {info.filename}")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                with bundle.open(info, "r") as source:
                    _copy_member(source, target)
    except (OSError, zipfile.BadZipFile) as exc:
        raise RuntimeError(f"Unable to extract PQID-Bench core archive: {exc}") from exc
    if roots != {expected_root}:
        raise ValueError(
            f"Core archive root mismatch: expected {expected_root!r}, observed {sorted(roots)}"
        )
    release_dir = destination / expected_root
    if not release_dir.is_dir():
        raise ValueError(f"Core archive lacks expected root directory: {expected_root}")
    return release_dir


def _safe_remove_tree(path: Path, parent: Path) -> None:
    resolved = path.resolve()
    expected_parent = parent.resolve()
    if resolved.parent != expected_parent or path.is_symlink():
        raise RuntimeError(f"Refusing to remove unexpected path: {path}")
    shutil.rmtree(resolved)


def download_core_release(
    *,
    version: str = BENCHMARK_RELEASE,
    output_dir: Path | None = None,
    url: str | None = None,
    sha256: str | None = None,
    force: bool = False,
    timeout_seconds: int = 120,
) -> DownloadResult:
    """Download, authenticate, extract, and verify one compact release."""

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    official = OFFICIAL_CORE_RELEASES.get(version)
    if official is None:
        raise ValueError(
            f"Unsupported benchmark release {version!r}; "
            f"available releases: {', '.join(sorted(OFFICIAL_CORE_RELEASES))}"
        )
    if (url is None) != (sha256 is None):
        raise ValueError("Custom downloads require both --url and --sha256")

    source_url = url or official.url
    expected_sha256 = _normalized_sha256(sha256 or official.sha256)
    _validate_https_url(source_url)

    output_root = (output_dir or (default_cache_root() / "releases" / version))
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    release_dir = output_root / official.root_name
    archive_path = output_root / official.archive_name

    if release_dir.exists():
        if release_dir.is_symlink() or not release_dir.is_dir():
            raise ValueError(f"Release destination is not a regular directory: {release_dir}")
        try:
            checked, _ = _release_metadata(release_dir, version)
        except (FileNotFoundError, ValueError) as exc:
            if not force:
                raise ValueError(
                    f"Existing release is invalid; inspect it or rerun with --force: {exc}"
                ) from exc
        else:
            if not force:
                return DownloadResult(
                    version=version,
                    release_dir=str(release_dir),
                    archive_path=str(archive_path),
                    source_url=source_url,
                    sha256=expected_sha256,
                    manifest_entries=checked,
                    downloaded=False,
                )

    with tempfile.TemporaryDirectory(
        prefix=".pqid-bench-download-",
        dir=output_root,
    ) as temporary:
        staging = Path(temporary)
        staged_archive = staging / official.archive_name
        _download_archive(
            source_url,
            staged_archive,
            expected_sha256=expected_sha256,
            timeout_seconds=timeout_seconds,
        )
        staged_extract = staging / "extracted"
        staged_release = _extract_verified_archive(
            staged_archive,
            staged_extract,
            expected_root=official.root_name,
        )
        checked, _ = _release_metadata(staged_release, version)

        backup: Path | None = None
        if release_dir.exists():
            backup = output_root / f".{official.root_name}.backup-{uuid.uuid4().hex}"
            release_dir.rename(backup)
        try:
            staged_release.rename(release_dir)
        except OSError:
            if backup is not None and backup.exists() and not release_dir.exists():
                backup.rename(release_dir)
            raise
        if backup is not None:
            _safe_remove_tree(backup, output_root)
        os.replace(staged_archive, archive_path)

    return DownloadResult(
        version=version,
        release_dir=str(release_dir),
        archive_path=str(archive_path),
        source_url=source_url,
        sha256=expected_sha256,
        manifest_entries=checked,
        downloaded=True,
    )
