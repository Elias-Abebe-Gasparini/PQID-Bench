"""Build the compact PQID-Bench distribution for benchmark users."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_RELEASE = "1.0.0"
PACKAGE_MINIMUM_VERSION = "1.2.0"
EVALUATOR_VERSION = "pqid-bench-evaluator-1.1.0-safe-builtins"
PREDICATE_VERSION = "pqid-bench-reference-signature-1.0.0-count-map"
SCHEMA_VERSION = "1.0.0"
ARCHIVE_NAME = f"PQID-Bench-v{BENCHMARK_RELEASE}-core.zip"
ARCHIVE_ROOT = f"PQID-Bench-v{BENCHMARK_RELEASE}-core"

HUGGING_FACE_URL = "https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench"
GITHUB_URL = "https://github.com/Elias-Abebe-Gasparini/PQID-Bench"
PYPI_URL = "https://pypi.org/project/pqid-bench/"
ZENODO_EVIDENCE_DOI = "10.5281/zenodo.21649753"
SOURCE_DATASET_DOI = "10.5281/zenodo.20674853"

EXPECTED_COUNTS = {
    "population": 734,
    "train": 514,
    "validation": 66,
    "test": 154,
    "test_signatures": 144,
}


@dataclass(frozen=True, slots=True)
class Payload:
    path: str
    data: bytes


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_text_bytes(path: Path) -> bytes:
    """Return cross-platform text bytes with canonical LF line endings."""

    payload = path.read_bytes()
    if b"\x00" in payload:
        raise RuntimeError(f"Core-bundle input is not a text file: {path}")
    return payload.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def jsonl_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(bool(line.strip()) for line in handle)


def physical_files() -> dict[str, Path]:
    files: dict[str, Path] = {
        "CITATION.cff": ROOT / "CITATION.cff",
        "LICENSE.md": ROOT / "LICENSE.md",
        "LICENSES/CC-BY-4.0.txt": ROOT / "LICENSES" / "CC-BY-4.0.txt",
        "LICENSES/MIT.txt": ROOT / "LICENSES" / "MIT.txt",
        "data/README.md": ROOT / "data" / "README.md",
        "data/pqid_bench_evaluator_source_734.jsonl": (
            ROOT / "data" / "pqid_bench_evaluator_source_734.jsonl"
        ),
        "data/splits/README.md": ROOT / "data" / "splits" / "README.md",
        "data/splits/train.jsonl": ROOT / "data" / "splits" / "train.jsonl",
        "data/splits/validation.jsonl": (
            ROOT / "data" / "splits" / "validation.jsonl"
        ),
        "data/splits/test.jsonl": ROOT / "data" / "splits" / "test.jsonl",
        (
            "artifacts/test_split_154/"
            "pqid_bench_external_generation_prompts_154.jsonl"
        ): (
            ROOT
            / "artifacts"
            / "test_split_154"
            / "pqid_bench_external_generation_prompts_154.jsonl"
        ),
        (
            "artifacts/test_split_154/"
            "pqid_bench_external_generation_response_template_154.jsonl"
        ): (
            ROOT
            / "artifacts"
            / "test_split_154"
            / "pqid_bench_external_generation_response_template_154.jsonl"
        ),
        "artifacts/test_split_154/pqid_bench_split_154_manifest.json": (
            ROOT
            / "artifacts"
            / "test_split_154"
            / "pqid_bench_split_154_manifest.json"
        ),
        "docker/evaluator/Dockerfile": ROOT / "docker" / "evaluator" / "Dockerfile",
        "docker/evaluator/README.md": ROOT / "docker" / "evaluator" / "README.md",
        "requirements/evaluator-container.txt": (
            ROOT / "requirements" / "evaluator-container.txt"
        ),
        "scripts/run_pqid_bench_external_model_generation_harness.py": (
            ROOT / "scripts" / "run_pqid_bench_external_model_generation_harness.py"
        ),
        "scripts/run_pqid_bench_generation_copy_baseline.py": (
            ROOT / "scripts" / "run_pqid_bench_generation_copy_baseline.py"
        ),
        "scripts/run_pqid_bench_executable_validity_check.py": (
            ROOT / "scripts" / "run_pqid_bench_executable_validity_check.py"
        ),
        "scripts/run_pqid_bench_retrieval_baseline.py": (
            ROOT / "scripts" / "run_pqid_bench_retrieval_baseline.py"
        ),
        "scripts/run_pqid_bench_tfidf_retrieval_baseline.py": (
            ROOT / "scripts" / "run_pqid_bench_tfidf_retrieval_baseline.py"
        ),
    }
    for schema in sorted((ROOT / "src" / "pqid_bench" / "schemas").glob("*.json")):
        files[f"schemas/{schema.name}"] = schema
    missing = [target for target, source in files.items() if not source.is_file()]
    if missing:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Core-bundle inputs are missing:\n{joined}")
    return files


def validate_source_counts(files: dict[str, Path]) -> None:
    observed = {
        "population": jsonl_count(files["data/pqid_bench_evaluator_source_734.jsonl"]),
        "train": jsonl_count(files["data/splits/train.jsonl"]),
        "validation": jsonl_count(files["data/splits/validation.jsonl"]),
        "test": jsonl_count(files["data/splits/test.jsonl"]),
    }
    expected = {key: EXPECTED_COUNTS[key] for key in observed}
    if observed != expected:
        raise RuntimeError(
            f"Frozen source counts changed: expected {expected}, observed {observed}"
        )


def benchmark_metadata() -> dict[str, object]:
    return {
        "name": "PQID-Bench",
        "benchmark_release": BENCHMARK_RELEASE,
        "distribution_profile": "core",
        "package_minimum_version": PACKAGE_MINIMUM_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "predicate_version": PREDICATE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "counts": EXPECTED_COUNTS,
        "paths": {
            "evaluator_source": "data/pqid_bench_evaluator_source_734.jsonl",
            "train": "data/splits/train.jsonl",
            "validation": "data/splits/validation.jsonl",
            "test": "data/splits/test.jsonl",
            "test_prompts": (
                "artifacts/test_split_154/"
                "pqid_bench_external_generation_prompts_154.jsonl"
            ),
            "response_template": (
                "artifacts/test_split_154/"
                "pqid_bench_external_generation_response_template_154.jsonl"
            ),
            "split_manifest": (
                "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
            ),
        },
        "supported_workflows": [
            "verify",
            "run-model",
            "replay",
            "evaluate",
        ],
        "evidence_only_workflows": [
            "reproduce",
            "compare",
            "dashboard",
        ],
        "links": {
            "hugging_face": HUGGING_FACE_URL,
            "github": GITHUB_URL,
            "pypi": PYPI_URL,
            "zenodo_evidence_doi": ZENODO_EVIDENCE_DOI,
            "source_dataset_doi": SOURCE_DATASET_DOI,
        },
    }


def candidate_run_manifest() -> dict[str, str]:
    return {
        "package_version": PACKAGE_MINIMUM_VERSION,
        "benchmark_release": BENCHMARK_RELEASE,
        "evaluator_version": EVALUATOR_VERSION,
        "predicate_version": PREDICATE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "artifact_manifest_version": BENCHMARK_RELEASE,
        "run_type": "supplied_evaluation",
    }


def core_readme() -> str:
    return f"""# PQID-Bench {BENCHMARK_RELEASE} Core

This is the compact operational distribution of PQID-Bench. It contains the
frozen train, validation, and test records, the 154 model-facing prompts, the
local target and split contract, response schemas, and the isolated evaluator.
It intentionally excludes archived model results, manuscript analyses,
repeatability evidence, figures, and repository administration.

## Install

```bash
python -m pip install "pqid-bench>={PACKAGE_MINIMUM_VERSION},<2"
pqid-bench verify .
```

## Run a model

Dry-run and inspect the request plan first:

```bash
pqid-bench run-model \\
  --release-dir . \\
  --output-dir candidate-run \\
  --provider openai-compatible \\
  --base-url https://provider.example/v1 \\
  --model MODEL_ID \\
  --api-key-env PROVIDER_API_KEY \\
  --dry-run
```

After reviewing provider retention and cost terms, remove `--dry-run` and add
`--acknowledge-third-party-prompt-export`.

## Evaluate safely

Generated Python must not be executed in the caller process. Build and use the
pinned Docker evaluator:

```bash
pqid-bench replay \\
  --release-dir . \\
  --responses candidate-run/responses.jsonl \\
  --output-dir candidate-evaluation \\
  --build-image \\
  --acknowledge-code-execution

pqid-bench evaluate \\
  --evaluations candidate-evaluation/pqid_bench_canonical_evaluations.jsonl \\
  --format text
```

Exact response and evaluation filenames are also reported by each command.

## Distribution boundary

This core profile supports `verify`, `run-model`, `replay`, and `evaluate`.
Use the Zenodo evidence archive, DOI `{ZENODO_EVIDENCE_DOI}`, for frozen-roster
comparison, manuscript-result reproduction, repeatability analysis, and the
interactive evidence dashboard.
"""


def benchmark_card() -> str:
    return f"""# PQID-Bench Core Benchmark Card

## Scope

PQID-Bench {BENCHMARK_RELEASE} evaluates quantum-program generation under a
frozen prompt, evaluator, and structural-predicate contract. Python execution
and OpenQASM 3 assembly admissibility are operational endpoints.
Reference-signature recovery compares qubit count, classical-bit count, and
the complete operation-type count map. Passing this predicate does not prove
unitary, distributional, or semantic equivalence.

## Data

| Split | Rows |
| --- | ---: |
| Train | {EXPECTED_COUNTS["train"]} |
| Validation | {EXPECTED_COUNTS["validation"]} |
| Test | {EXPECTED_COUNTS["test"]} |
| Total | {EXPECTED_COUNTS["population"]} |

The test split contains {EXPECTED_COUNTS["test_signatures"]} evaluator-facing
reference signatures. The model-facing prompt file and evaluator target
records remain separate so that runners transmit only prompt text.

## Versions

| Object | Version |
| --- | --- |
| Benchmark | {BENCHMARK_RELEASE} |
| Minimum Python toolkit | {PACKAGE_MINIMUM_VERSION} |
| Evaluator | `{EVALUATOR_VERSION}` |
| Structural predicate | `{PREDICATE_VERSION}` |
| Schema | {SCHEMA_VERSION} |

## Safety

Live testing exports prompts to the selected provider and may incur retention
and billing risks. Replay generated code only in the pinned, network-disabled
Docker evaluator.

## Evidence

The complete frozen 21-model results, robustness analyses, and repeatability
records are intentionally excluded from this adoption bundle and preserved in
the evidence archive: <https://doi.org/{ZENODO_EVIDENCE_DOI}>.
"""


def virtual_payloads() -> list[Payload]:
    return [
        Payload("README.md", core_readme().encode("utf-8")),
        Payload("BENCHMARK_CARD.md", benchmark_card().encode("utf-8")),
        Payload(
            "benchmark.json",
            (
                json.dumps(benchmark_metadata(), indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8"),
        ),
        Payload(
            "templates/candidate-run-manifest.json",
            (
                json.dumps(candidate_run_manifest(), indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8"),
        ),
    ]


def all_payloads() -> list[Payload]:
    files = physical_files()
    validate_source_counts(files)
    payloads = virtual_payloads()
    payloads.extend(
        Payload(target, canonical_text_bytes(source))
        for target, source in sorted(files.items())
    )
    paths = [payload.path for payload in payloads]
    if len(paths) != len(set(paths)):
        raise RuntimeError("Duplicate path in core-bundle payload")
    return sorted(payloads, key=lambda payload: payload.path)


def artifact_manifest(payloads: list[Payload]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("path", "bytes", "sha256"))
    for payload in payloads:
        writer.writerow((payload.path, len(payload.data), sha256_bytes(payload.data)))
    return output.getvalue().encode("utf-8")


def write_zip_payload(
    handle: zipfile.ZipFile,
    relative: str,
    payload: bytes,
) -> None:
    info = zipfile.ZipInfo(
        f"{ARCHIVE_ROOT}/{relative}",
        date_time=(2026, 7, 31, 0, 0, 0),
    )
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    handle.writestr(info, payload, compress_type=zipfile.ZIP_STORED)


def build(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / ARCHIVE_NAME
    payloads = all_payloads()
    manifest = artifact_manifest(payloads)
    with zipfile.ZipFile(
        archive,
        "w",
        compression=zipfile.ZIP_STORED,
    ) as handle:
        for payload in payloads:
            write_zip_payload(handle, payload.path, payload.data)
        write_zip_payload(handle, "ARTIFACT_MANIFEST.tsv", manifest)
    sidecar = archive.with_suffix(archive.suffix + ".sha256")
    sidecar.write_text(
        f"{sha256_file(archive)}  {archive.name}\n",
        encoding="ascii",
        newline="\n",
    )
    return archive, sidecar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist" / "core",
    )
    args = parser.parse_args()
    archive, sidecar = build(args.output_dir.resolve())
    print(f"Core archive: {archive}")
    print(f"Files: {len(all_payloads()) + 1}")
    print(f"SHA-256: {sha256_file(archive)}")
    print(f"Sidecar: {sidecar}")


if __name__ == "__main__":
    main()
