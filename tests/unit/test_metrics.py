from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from pqid_bench.metrics import (
    iter_jsonl,
    summarize_evaluation_records,
    validate_repeatability,
)


class MetricTests(unittest.TestCase):
    def test_nested_endpoints_and_rates(self) -> None:
        rows = [
            {
                "model": "a",
                "prompt_id": "p1",
                "report_executable": True,
                "report_assembly_admissible": True,
                "report_signature_match": True,
                "ordered_wire_tape_match": True,
                "parameter_aware_tape_match": False,
            },
            {
                "model": "a",
                "prompt_id": "p2",
                "report_executable": True,
                "report_assembly_admissible": True,
                "report_signature_match": False,
                "ordered_wire_tape_match": False,
                "parameter_aware_tape_match": False,
            },
            {
                "model": "b",
                "prompt_id": "p1",
                "report_executable": False,
                "report_assembly_admissible": False,
                "report_signature_match": False,
            },
        ]
        summary = summarize_evaluation_records(rows)
        self.assertEqual(summary.cells, 3)
        self.assertEqual(summary.models, 2)
        self.assertEqual(summary.prompts, 2)
        self.assertEqual(summary.execution_count, 2)
        self.assertEqual(summary.assembly_count, 2)
        self.assertEqual(summary.signature_count, 1)
        self.assertEqual(summary.ordered_count, 1)
        self.assertEqual(summary.parameter_count, 0)
        self.assertEqual(summary.es_gap_count, 1)
        self.assertEqual(summary.execution_to_assembly_attrition_count, 0)
        self.assertEqual(summary.as_gap_count, 1)
        self.assertEqual(summary.assembly_without_signature_count, 1)
        self.assertEqual(summary.signature_without_assembly_count, 0)
        self.assertAlmostEqual(summary.as_gap_share_of_es_gap or 0.0, 1.0)
        self.assertAlmostEqual(summary.executable_signature_disagreement_rate, 0.5)

    def test_rejects_signature_without_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "signature => execution"):
            summarize_evaluation_records(
                [
                    {
                        "model": "a",
                        "prompt_id": "p1",
                        "report_executable": False,
                        "report_signature_match": True,
                    }
                ]
            )

    def test_reports_optional_stricter_layers_as_unavailable(self) -> None:
        summary = summarize_evaluation_records(
            [
                {
                    "model": "a",
                    "prompt_id": "p1",
                    "execution": 1,
                    "signature": 0,
                }
            ]
        )
        self.assertIsNone(summary.ordered_count)
        self.assertIsNone(summary.parameter_count)
        self.assertIsNone(summary.assembly_count)
        self.assertIsNone(summary.as_gap_count)

    def test_rejects_assembly_without_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "assembly => execution"):
            summarize_evaluation_records(
                [
                    {
                        "model": "a",
                        "prompt_id": "p1",
                        "report_executable": False,
                        "report_assembly_admissible": True,
                        "report_signature_match": False,
                    }
                ]
            )

    def test_reports_signature_without_assembly_without_rejecting_it(self) -> None:
        summary = summarize_evaluation_records(
            [
                {
                    "model": "a",
                    "prompt_id": "p1",
                    "report_executable": True,
                    "report_assembly_admissible": False,
                    "report_signature_match": True,
                }
            ]
        )
        self.assertEqual(summary.signature_without_assembly_count, 1)
        self.assertEqual(summary.assembly_without_signature_count, 0)
        self.assertEqual(summary.as_gap_count, -1)

    def test_rejects_partial_assembly_coverage(self) -> None:
        rows = [
            {
                "model": "a",
                "prompt_id": "p1",
                "report_executable": True,
                "report_assembly_admissible": True,
                "report_signature_match": False,
            },
            {
                "model": "a",
                "prompt_id": "p2",
                "report_executable": True,
                "report_signature_match": False,
            },
        ]
        with self.assertRaisesRegex(ValueError, "present for every evaluation record"):
            summarize_evaluation_records(rows)

    def test_rejects_conflicting_endpoint_aliases(self) -> None:
        with self.assertRaisesRegex(ValueError, "Conflicting aliases"):
            summarize_evaluation_records(
                [
                    {
                        "model": "a",
                        "prompt_id": "p1",
                        "report_executable": True,
                        "execution": False,
                        "report_signature_match": False,
                    }
                ]
            )

    def test_accepts_consistent_endpoint_aliases(self) -> None:
        summary = summarize_evaluation_records(
            [
                {
                    "model": "a",
                    "prompt_id": "p1",
                    "report_executable": True,
                    "execution": 1,
                    "report_signature_match": False,
                    "signature": 0,
                }
            ]
        )
        self.assertEqual(summary.execution_count, 1)
        self.assertEqual(summary.signature_count, 0)

    def test_rejects_duplicate_model_prompt_key(self) -> None:
        row = {
            "model": "a",
            "prompt_id": "p1",
            "report_executable": True,
            "report_signature_match": False,
        }
        with self.assertRaisesRegex(ValueError, "Duplicate model-prompt key"):
            summarize_evaluation_records([row, dict(row)])

    def test_rejects_missing_prompt_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "lacks model or prompt_id"):
            summarize_evaluation_records(
                [
                    {
                        "model": "a",
                        "report_executable": True,
                        "report_signature_match": False,
                    }
                ]
            )

    def test_rejects_malformed_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.jsonl"
            path.write_text('{"prompt_id": "p1"}\n{bad json}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSONL"):
                list(iter_jsonl(path))

    def test_rejects_corrupted_repeatability_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = (
                root
                / "artifacts"
                / "stochastic_repeatability_21x72"
                / "consolidated"
                / "analysis"
                / "pqid_bench_stochastic_repeatability_cell_outcomes.csv"
            )
            path.parent.mkdir(parents=True)
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=("model", "prompt_id", "run"),
                )
                writer.writeheader()
                writer.writerow({"model": "a", "prompt_id": "p1", "run": "1"})
            errors = validate_repeatability(root)
            self.assertEqual(len(errors), 4)


if __name__ == "__main__":
    unittest.main()
