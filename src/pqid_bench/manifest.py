"""SHA-256 release-manifest verification."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ManifestVerification:
    manifest_path: str
    checked: int
    missing: tuple[str, ...]
    size_mismatches: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not (self.missing or self.size_mismatches or self.hash_mismatches)

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "checked": self.checked,
            "valid": self.valid,
            "missing": list(self.missing),
            "size_mismatches": list(self.size_mismatches),
            "hash_mismatches": list(self.hash_mismatches),
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(path: Path) -> tuple[ManifestEntry, ...]:
    if not path.is_file():
        raise FileNotFoundError(path)
    entries: list[ManifestEntry] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["path", "bytes", "sha256"]:
            raise ValueError(f"Unexpected manifest header in {path}")
        for row in reader:
            relative = row["path"]
            if not relative or relative in seen:
                raise ValueError(f"Duplicate or empty manifest path: {relative!r}")
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError(f"Unsafe manifest path: {relative}")
            seen.add(relative)
            entries.append(
                ManifestEntry(
                    path=relative,
                    bytes=int(row["bytes"]),
                    sha256=row["sha256"].lower(),
                )
            )
    return tuple(entries)


def verify_manifest(release_dir: Path) -> ManifestVerification:
    release_dir = release_dir.resolve()
    manifest_path = release_dir / "ARTIFACT_MANIFEST.tsv"
    entries = read_manifest(manifest_path)
    missing: list[str] = []
    sizes: list[str] = []
    hashes: list[str] = []
    for entry in entries:
        target = release_dir / Path(entry.path)
        if not target.is_file():
            missing.append(entry.path)
            continue
        if target.stat().st_size != entry.bytes:
            sizes.append(entry.path)
            continue
        if sha256_file(target) != entry.sha256:
            hashes.append(entry.path)
    return ManifestVerification(
        manifest_path=str(manifest_path),
        checked=len(entries),
        missing=tuple(missing),
        size_mismatches=tuple(sizes),
        hash_mismatches=tuple(hashes),
    )

