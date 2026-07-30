from __future__ import annotations

import unittest
from pathlib import Path

from pqid_bench.metrics import iter_jsonl, prepare_comparison, reproduce_release

RELEASE = Path(__file__).resolve().parents[2]


class ReleaseReproductionIntegrationTests(unittest.TestCase):
    def test_headline_reproduction(self) -> None:
        summary = reproduce_release(RELEASE)
        self.assertEqual(summary.cells, 3234)
        self.assertEqual(summary.execution_count, 2950)
        self.assertEqual(summary.assembly_count, 2944)
        self.assertEqual(summary.signature_count, 1703)
        self.assertEqual(summary.es_gap_count, 1247)
        self.assertEqual(summary.execution_to_assembly_attrition_count, 6)
        self.assertEqual(summary.as_gap_count, 1241)
        self.assertEqual(summary.assembly_without_signature_count, 1241)
        self.assertEqual(summary.signature_without_assembly_count, 0)
        self.assertAlmostEqual(summary.as_gap_share_of_es_gap or 0.0, 1241 / 1247)
        self.assertAlmostEqual(summary.structural_hallucination_rate or 0.0, 1187 / 2890)

    def test_comparison_requires_aligned_prompt_denominator(self) -> None:
        audit = (
            RELEASE
            / "artifacts"
            / "analysis_154"
            / "pqid_bench_ordered_operand_cell_audit.jsonl"
        )
        rows = [
            row for row in iter_jsonl(audit) if row["model"] == "gpt-5.6-sol"
        ]
        self.assertEqual(len(rows), 154)

        candidate, frozen, scope = prepare_comparison(
            RELEASE,
            rows,
            allow_partial=False,
        )
        self.assertEqual(scope.mode, "full_test_set")
        self.assertEqual(scope.prompt_count, 154)
        self.assertEqual(candidate.cells, 154)
        self.assertEqual(frozen.cells, 3234)

        partial = rows[:-1]
        with self.assertRaisesRegex(ValueError, "prompt denominator"):
            prepare_comparison(RELEASE, partial, allow_partial=False)

        candidate, frozen, scope = prepare_comparison(
            RELEASE,
            partial,
            allow_partial=True,
        )
        self.assertEqual(scope.mode, "matched_subset")
        self.assertEqual(scope.prompt_count, 153)
        self.assertEqual(candidate.cells, 153)
        self.assertEqual(frozen.cells, 21 * 153)


if __name__ == "__main__":
    unittest.main()
