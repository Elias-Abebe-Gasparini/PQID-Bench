from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from pqid_bench.visualization import (
    benchmark_split_svg,
    build_dashboard,
    ecosystem_flow_svg,
    endpoint_rates_svg,
    load_dashboard_data,
    measurement_ladder_svg,
    write_site_assets,
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
        split = benchmark_split_svg()
        endpoints = endpoint_rates_svg(self.data.summary)
        for document in (workflow, ladder, split, endpoints):
            self.assertTrue(document.startswith("<svg"))
            self.assertIn("<title", document)
            self.assertIn("<desc", document)
            self.assertIn('role="img"', document)
        self.assertIn("514 training", split)
        self.assertIn("91.22%", endpoints)

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

    @unittest.skipUnless(PLOTLY_AVAILABLE, "Plotly optional dependency not installed")
    def test_site_builder_writes_all_static_overview_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "interactive"
            write_site_assets(ROOT, output, plotlyjs="cdn")
            for name in (
                "ecosystem-flow.svg",
                "measurement-ladder.svg",
                "benchmark-split.svg",
                "endpoint-rates.svg",
            ):
                path = output / "assets" / name
                self.assertTrue(path.is_file(), name)
                self.assertIn("<title", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
