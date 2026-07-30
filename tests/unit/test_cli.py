from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pqid_bench.cli import _load_candidate_run_manifest, main
from pqid_bench.download import DownloadResult
from pqid_bench.version import (
    ARTIFACT_MANIFEST_VERSION,
    BENCHMARK_RELEASE,
    EVALUATOR_VERSION,
    PACKAGE_VERSION,
    PREDICATE_VERSION,
    SCHEMA_VERSION,
)


def candidate_manifest() -> dict[str, str]:
    return {
        "package_version": PACKAGE_VERSION,
        "benchmark_release": BENCHMARK_RELEASE,
        "evaluator_version": EVALUATOR_VERSION,
        "predicate_version": PREDICATE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "artifact_manifest_version": ARTIFACT_MANIFEST_VERSION,
        "run_type": "supplied_evaluation",
    }


class CliContractTests(unittest.TestCase):
    def _write_manifest(self, root: Path, payload: dict[str, str]) -> Path:
        path = root / "run-manifest.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_accepts_compatible_candidate_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_manifest(Path(directory), candidate_manifest())
            observed = _load_candidate_run_manifest(path)
            self.assertEqual(observed["predicate_version"], PREDICATE_VERSION)

    def test_rejects_incompatible_predicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = candidate_manifest()
            payload["predicate_version"] = "different-predicate"
            path = self._write_manifest(Path(directory), payload)
            with self.assertRaisesRegex(ValueError, "predicate_version"):
                _load_candidate_run_manifest(path)

    def test_rejects_incompatible_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = candidate_manifest()
            payload["schema_version"] = "2.0.0"
            path = self._write_manifest(Path(directory), payload)
            with self.assertRaisesRegex(ValueError, "schema_version"):
                _load_candidate_run_manifest(path)

    def test_verify_returns_nonzero_for_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "record.txt"
            target.write_text("changed\n", encoding="utf-8")
            expected = hashlib.sha256(b"frozen\n").hexdigest()
            (root / "ARTIFACT_MANIFEST.tsv").write_text(
                f"path\tbytes\tsha256\nrecord.txt\t{target.stat().st_size}\t{expected}\n",
                encoding="utf-8",
            )
            self.assertEqual(main(["verify", str(root)]), 1)

    def test_download_prints_verified_release_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = DownloadResult(
                version="1.0.0",
                release_dir=str(root / "PQID-Bench-v1.0.0-core"),
                archive_path=str(root / "PQID-Bench-v1.0.0-core.zip"),
                source_url="https://example.test/core.zip",
                sha256="a" * 64,
                manifest_entries=31,
                downloaded=True,
            )
            stdout = io.StringIO()
            with patch(
                "pqid_bench.cli.download_core_release",
                return_value=receipt,
            ) as operation:
                with redirect_stdout(stdout):
                    status = main(
                        [
                            "download",
                            "--version",
                            "1.0.0",
                            "--output-dir",
                            str(root),
                        ]
                    )
            self.assertEqual(status, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["downloaded"])
            self.assertFalse(payload["reused"])
            self.assertEqual(payload["manifest_entries"], 31)
            operation.assert_called_once()

    def test_evaluate_keeps_json_as_the_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluations = root / "evaluations.jsonl"
            evaluations.write_text(
                json.dumps(
                    {
                        "model": "model-a",
                        "prompt_id": "prompt-1",
                        "report_executable": True,
                        "report_signature_match": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = main(["evaluate", "--evaluations", str(evaluations)])
            self.assertEqual(status, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["cells"], 1)
            self.assertEqual(payload["es_gap_count"], 1)

    def test_evaluate_writes_and_prints_selected_human_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluations = root / "evaluations.jsonl"
            report = root / "reports" / "summary.md"
            evaluations.write_text(
                json.dumps(
                    {
                        "model": "model-a",
                        "prompt_id": "prompt-1",
                        "report_executable": True,
                        "report_signature_match": True,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = main(
                    [
                        "evaluate",
                        "--evaluations",
                        str(evaluations),
                        "--format",
                        "markdown",
                        "--output",
                        str(report),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertTrue(report.is_file())
            self.assertEqual(report.read_text(encoding="utf-8"), stdout.getvalue())
            self.assertIn("# PQID-Bench Evaluation Summary", stdout.getvalue())

    def test_run_model_dry_run_contacts_no_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt_path = (
                root
                / "artifacts"
                / "test_split_154"
                / "pqid_bench_external_generation_prompts_154.jsonl"
            )
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text(
                json.dumps(
                    {
                        "prompt_id": "pqid_bench_external_gen_0001",
                        "row_id": "row-1",
                        "prompt": "Build a circuit.",
                        "messages": [
                            {"role": "user", "content": "Build a circuit."}
                        ],
                        "target_metadata": {"gate_count": 1},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            relative = prompt_path.relative_to(root).as_posix()
            (root / "ARTIFACT_MANIFEST.tsv").write_text(
                "path\tbytes\tsha256\n"
                f"{relative}\t{prompt_path.stat().st_size}\t{digest}\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = main(
                    [
                        "run-model",
                        "--release-dir",
                        str(root),
                        "--output-dir",
                        str(root / "output"),
                        "--provider",
                        "local",
                        "--model",
                        "local-model",
                        "--dry-run",
                    ]
                )
            self.assertEqual(status, 0)
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["contacts_provider"])
            self.assertFalse(payload["target_metadata_exported"])

    def test_run_model_without_acknowledgement_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                status = main(
                    [
                        "run-model",
                        "--release-dir",
                        str(root),
                        "--output-dir",
                        str(root / "output"),
                        "--provider",
                        "local",
                        "--model",
                        "local-model",
                    ]
                )
            self.assertEqual(status, 2)
            self.assertIn(
                "--acknowledge-third-party-prompt-export",
                stderr.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
