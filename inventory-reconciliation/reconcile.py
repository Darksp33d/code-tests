"""Inventory reconciliation CLI -- compares two warehouse snapshots."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = Path(__file__).parent / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"

SNAPSHOT_BEFORE = DEFAULT_SNAPSHOT_DIR / "snapshot_1.csv"
SNAPSHOT_AFTER = DEFAULT_SNAPSHOT_DIR / "snapshot_2.csv"

LOG_FORMAT = "%(levelname)s: %(message)s"


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=level, stream=sys.stderr)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconcile two inventory snapshots and produce a change report.",
    )
    parser.add_argument(
        "before",
        nargs="?",
        type=Path,
        default=SNAPSHOT_BEFORE,
        help="Path to the earlier snapshot CSV (default: data/snapshot_1.csv)",
    )
    parser.add_argument(
        "after",
        nargs="?",
        type=Path,
        default=SNAPSHOT_AFTER,
        help="Path to the later snapshot CSV (default: data/snapshot_2.csv)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the reconciliation report (default: output/)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    configure_logging(args.verbose)
    logging.info("Reconciliation not yet implemented")


if __name__ == "__main__":
    main()
