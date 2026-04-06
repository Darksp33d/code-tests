"""Inventory reconciliation CLI -- compares two warehouse snapshots."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from engine import reconcile
from parsing import SNAPSHOT_1_COLUMNS, SNAPSHOT_2_COLUMNS, parse_snapshot
from reporting import build_report, write_report

DEFAULT_SNAPSHOT_DIR = Path(__file__).parent / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"

SNAPSHOT_BEFORE = DEFAULT_SNAPSHOT_DIR / "snapshot_1.csv"
SNAPSHOT_AFTER = DEFAULT_SNAPSHOT_DIR / "snapshot_2.csv"

LOG_FORMAT = "%(levelname)s: %(message)s"

logger = logging.getLogger(__name__)


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


def detect_column_mapping(csv_path: Path) -> dict[str, str]:
    with open(csv_path, encoding="utf-8") as fh:
        header = fh.readline().strip()

    if "product_name" in header or "qty" in header:
        return SNAPSHOT_2_COLUMNS
    return SNAPSHOT_1_COLUMNS


def main() -> None:
    args = build_argument_parser().parse_args()
    configure_logging(args.verbose)

    before_mapping = detect_column_mapping(args.before)
    after_mapping = detect_column_mapping(args.after)

    logger.info("Parsing %s", args.before.name)
    before_snapshot = parse_snapshot(args.before, before_mapping)

    logger.info("Parsing %s", args.after.name)
    after_snapshot = parse_snapshot(args.after, after_mapping)

    logger.info("Reconciling snapshots")
    result = reconcile(before_snapshot, after_snapshot)

    report = build_report(result, args.before.name, args.after.name)

    report_path = write_report(report, args.output_dir)

    summary = report["summary"]
    logger.info(
        "Done -- %d changed, %d unchanged, %d removed, %d added, %d quality issues",
        summary["changed"],
        summary["unchanged"],
        summary["removed"],
        summary["added"],
        summary["quality_issues"],
    )


if __name__ == "__main__":
    main()
