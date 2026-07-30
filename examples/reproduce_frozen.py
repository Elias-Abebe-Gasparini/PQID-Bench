"""Reproduce the frozen PQID-Bench summary without executing generated code."""

from __future__ import annotations

import argparse
from pathlib import Path

from pqid_bench import reproduce_release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="PQID-Bench evidence root (default: repository root).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "csv", "json"),
        default="text",
        help="Report format.",
    )
    args = parser.parse_args()

    summary = reproduce_release(args.release_dir)
    if args.format == "json":
        import json

        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        print(summary.render(output_format=args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
