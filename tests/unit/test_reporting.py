from __future__ import annotations

import csv
import io
import json
import unittest

from pqid_bench import (
    BenchmarkSummary,
    render_comparison,
    render_summary,
    summary_rows,
)
from pqid_bench.version import version_record


def benchmark_summary() -> BenchmarkSummary:
    return BenchmarkSummary(
        cells=4,
        models=2,
        prompts=2,
        execution_count=3,
        signature_count=2,
        ordered_count=1,
        parameter_count=1,
        es_gap_count=1,
        execution_rate=0.75,
        signature_rate=0.5,
        es_gap_rate=0.25,
        executable_signature_disagreement_rate=1 / 3,
        identifiable_cells=2,
        identifiable_execution_count=2,
        identifiable_signature_count=1,
        identifiable_disagreement_count=1,
        structural_hallucination_rate=0.5,
        assembly_count=3,
        assembly_rate=0.75,
        execution_to_assembly_attrition_count=0,
        execution_to_assembly_attrition_rate=0.0,
        as_gap_count=1,
        as_gap_rate=0.25,
        assembly_without_signature_count=1,
        signature_without_assembly_count=0,
        as_gap_share_of_es_gap=1.0,
    )


class SummaryReportingTests(unittest.TestCase):
    def test_text_report_prints_counts_denominators_and_rates(self) -> None:
        report = benchmark_summary().to_text()
        self.assertIn("PQID-Bench Evaluation Summary", report)
        signature_line = next(
            line
            for line in report.splitlines()
            if line.startswith("Reference-signature match")
        )
        self.assertEqual(signature_line.split()[-3:], ["2", "4", "50.00%"])
        assembly_line = next(
            line
            for line in report.splitlines()
            if line.startswith("Quantum-assembly admissibility")
        )
        self.assertEqual(assembly_line.split()[-3:], ["3", "4", "75.00%"])
        hallucination_line = next(
            line
            for line in report.splitlines()
            if line.startswith("Structural hallucination")
        )
        self.assertEqual(hallucination_line.split()[-3:], ["1", "2", "50.00%"])

    def test_print_uses_compact_text_report(self) -> None:
        self.assertEqual(str(benchmark_summary()), benchmark_summary().to_text())

    def test_markdown_report_is_copy_ready(self) -> None:
        report = benchmark_summary().to_markdown()
        self.assertTrue(report.startswith("# PQID-Bench Evaluation Summary"))
        self.assertIn("| Endpoint | Count | Denominator | Rate |", report)
        self.assertIn("| ES-Gap | 1 | 4 | 25.00% |", report)
        self.assertIn(
            "| Assembly-Structure Gap (AS-Gap) | 1 | 4 | 25.00% |",
            report,
        )

    def test_csv_report_is_tidy_and_preserves_raw_rates(self) -> None:
        rows = list(csv.DictReader(io.StringIO(benchmark_summary().to_csv())))
        execution = next(row for row in rows if row["metric_key"] == "execution")
        self.assertEqual(execution["count"], "3")
        self.assertEqual(execution["denominator"], "4")
        self.assertEqual(execution["rate"], "0.75")
        self.assertEqual(execution["rate_percent"], "75")

    def test_tidy_rows_need_no_dataframe_dependency(self) -> None:
        rows = summary_rows(benchmark_summary())
        ersd = next(row for row in rows if row["metric_key"] == "ersd")
        self.assertEqual(ersd["count"], 1)
        self.assertEqual(ersd["denominator"], 3)
        self.assertAlmostEqual(ersd["rate"], 1 / 3)

    def test_unavailable_layers_are_not_rendered_as_zero(self) -> None:
        payload = benchmark_summary().to_dict()
        payload["ordered_count"] = None
        payload["parameter_count"] = None
        report = render_summary(payload, output_format="text")
        ordered_line = next(
            line
            for line in report.splitlines()
            if line.startswith("Ordered operation-and-operand tape")
        )
        self.assertIn("N/A", ordered_line)
        self.assertNotIn("0.00%", ordered_line)

    def test_json_remains_machine_readable(self) -> None:
        payload = json.loads(
            render_summary(benchmark_summary(), output_format="json")
        )
        self.assertEqual(payload["cells"], 4)
        self.assertEqual(payload["es_gap_count"], 1)

    def test_invalid_format_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported report format"):
            render_summary(benchmark_summary(), output_format="pdf")


class ComparisonReportingTests(unittest.TestCase):
    def comparison_payload(self) -> dict[str, object]:
        candidate = benchmark_summary()
        frozen = BenchmarkSummary(
            **{
                **{
                    name: getattr(candidate, name)
                    for name in candidate.__dataclass_fields__
                },
                "execution_count": 2,
                "execution_rate": 0.5,
                "assembly_count": 2,
                "assembly_rate": 0.5,
                "as_gap_count": 0,
                "as_gap_rate": 0.0,
                "assembly_without_signature_count": 0,
                "as_gap_share_of_es_gap": None,
                "es_gap_count": 0,
                "es_gap_rate": 0.0,
                "executable_signature_disagreement_rate": 0.0,
            }
        )
        return {
            **version_record(run_type="supplied_evaluation"),
            "comparison_label": "matched-subset comparison",
            "candidate_source": "candidate.jsonl",
            "comparison_scope": {
                "mode": "matched_subset",
                "prompt_count": 2,
                "candidate_models": 2,
                "candidate_cells": 4,
                "frozen_models": 2,
                "frozen_cells": 4,
            },
            "candidate": candidate.to_dict(run_type="supplied_evaluation"),
            "frozen": frozen.to_dict(),
            "candidate_minus_frozen": {},
        }

    def test_text_comparison_uses_aligned_candidate_and_frozen_columns(self) -> None:
        report = render_comparison(self.comparison_payload(), output_format="text")
        self.assertIn("PQID-Bench Candidate Comparison", report)
        self.assertIn("3/4 (75.00%)", report)
        self.assertIn("2/4 (50.00%)", report)
        self.assertIn("+25.00 pp", report)

    def test_comparison_csv_contains_numerical_delta(self) -> None:
        report = render_comparison(self.comparison_payload(), output_format="csv")
        rows = list(csv.DictReader(io.StringIO(report)))
        execution = next(row for row in rows if row["metric_key"] == "execution")
        self.assertEqual(execution["candidate_rate"], "0.75")
        self.assertEqual(execution["frozen_rate"], "0.5")
        self.assertEqual(execution["delta_percentage_points"], "25")


if __name__ == "__main__":
    unittest.main()
