from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from pqid_bench.visualization import (
    build_dashboard,
    ecosystem_flow_svg,
    load_dashboard_data,
    measurement_ladder_svg,
)

ROOT = Path(__file__).resolve().parents[2]
PLOTLY_AVAILABLE = importlib.util.find_spec("plotly") is not None


class VisualizationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_dashboard_data(ROOT)

    def test_dashboard_data_matches_frozen_panel(self) -> None:
        self.assertEqual(len(self.data.models), 21)
        self.assertEqual(self.data.summary["cells"], 3234)
        self.assertEqual(
            sum(row["execution_count"] for row in self.data.models),
            2950,
        )
        self.assertEqual(
            sum(row["assembly_count"] for row in self.data.models),
            2944,
        )
        self.assertEqual(
            sum(row["signature_count"] for row in self.data.models),
            1703,
        )

    def test_static_fallbacks_are_accessible_svg(self) -> None:
        workflow = ecosystem_flow_svg()
        ladder = measurement_ladder_svg(self.data.summary)
        for document in (workflow, ladder):
            self.assertTrue(document.startswith("<svg"))
            self.assertIn("<title", document)
            self.assertIn("<desc", document)
            self.assertIn('role="img"', document)

    @unittest.skipUnless(PLOTLY_AVAILABLE, "Plotly optional dependency not installed")
    def test_standalone_dashboard_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dashboard.html"
            observed = build_dashboard(ROOT, output, plotlyjs="cdn")
            rendered = output.read_text(encoding="utf-8")
            self.assertEqual(len(observed.models), 21)
            self.assertIn("PQID-Bench Interactive Explorer", rendered)
            self.assertIn("pqid-bench-heatmap", rendered)
            self.assertIn("cdn.plot.ly", rendered)
            self.assertIn('class="plot-wrap plot-models"', rendered)
            self.assertIn("Scroll horizontally to inspect", rendered)
            self.assertIn('id="data-table"', rendered)


if __name__ == "__main__":
    unittest.main()
