"""Inspect a live-model request plan without contacting a provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pqid_bench import LiveRunConfig, plan_live_model_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="Provider preset name.")
    parser.add_argument("--model", required=True, help="Provider model identifier.")
    parser.add_argument("--limit", type=int, default=3, help="Number of prompts to select.")
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="PQID-Bench evidence root (default: repository root).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("live-runs") / "planned-run",
        help="Prospective output directory recorded in the plan.",
    )
    args = parser.parse_args()

    config = LiveRunConfig(
        release_dir=args.release_dir,
        output_dir=args.output_dir,
        provider=args.provider,
        model=args.model,
        limit=args.limit,
    )
    print(json.dumps(plan_live_model_run(config), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
