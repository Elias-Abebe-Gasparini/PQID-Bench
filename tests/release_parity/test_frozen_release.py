from __future__ import annotations

import unittest
from pathlib import Path

from pqid_bench.metrics import (
    reproduce_release,
    validate_canonical_summary,
    validate_repeatability,
)


RELEASE = Path(__file__).resolve().parents[2]


class FrozenReleaseParityTests(unittest.TestCase):
    def test_all_primary_cells_and_endpoints(self) -> None:
        summary = reproduce_release(RELEASE)
        self.assertEqual(validate_canonical_summary(summary), ())

    def test_all_repeatability_cells(self) -> None:
        self.assertEqual(validate_repeatability(RELEASE), ())


if __name__ == "__main__":
    unittest.main()

