"""Build a standalone interactive dashboard from frozen PQID-Bench evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from pqid_bench import build_dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="PQID-Bench evidence root (default: repository root).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pqid-bench-dashboard.html"),
        help="Destination HTML file.",
    )
    parser.add_argument(
        "--plotlyjs",
        choices=("cdn", "inline"),
        default="cdn",
        help="Use the Plotly CDN or embed Plotly for a fully offline report.",
    )
    args = parser.parse_args()

    data = build_dashboard(args.release_dir, args.output, plotlyjs=args.plotlyjs)
    print(f"Wrote {args.output.resolve()}")
    print(f"Models: {len(data.models)}; cells: {data.summary['cells']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
