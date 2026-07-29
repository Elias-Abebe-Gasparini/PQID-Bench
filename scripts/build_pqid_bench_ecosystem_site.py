#!/usr/bin/env python3
"""Build Pages-only interactive and static PQID-Bench visual assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    SCRIPT_ROOT
    if (SCRIPT_ROOT / "pyproject.toml").is_file()
    else SCRIPT_ROOT / "PQID-Bench"
)
SRC = PACKAGE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pqid_bench.visualization import write_site_assets


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser()
    command.add_argument("--release-dir", type=Path, default=PACKAGE)
    command.add_argument(
        "--output-dir",
        type=Path,
        default=PACKAGE / "docs" / "interactive",
    )
    command.add_argument(
        "--plotlyjs",
        choices=("embed", "cdn"),
        default="cdn",
    )
    return command


def main() -> int:
    args = parser().parse_args()
    data = write_site_assets(
        args.release_dir,
        args.output_dir,
        plotlyjs=args.plotlyjs,
    )
    print(
        f"Wrote interactive site assets for {len(data.models)} models to "
        f"{args.output_dir.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
