"""Report generation -- formats reconciliation results as JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from engine import ItemDelta, ReconciliationResult
from parsing import InventoryItem, QualityIssue

logger = logging.getLogger(__name__)

REPORT_FILENAME = "reconciliation_report.json"


def _item_to_dict(item: InventoryItem) -> dict:
    return {
        "sku": item.sku,
        "name": item.name,
        "quantity": item.quantity,
        "location": item.location,
    }


def _delta_to_dict(delta: ItemDelta) -> dict:
    result: dict = {
        "sku": delta.sku,
        "quantity_before": delta.quantity_before,
        "quantity_after": delta.quantity_after,
        "quantity_delta": delta.quantity_delta,
    }

    if delta.name_before != delta.name_after:
        result["name_before"] = delta.name_before
        result["name_after"] = delta.name_after

    if delta.location_before != delta.location_after:
        result["location_before"] = delta.location_before
        result["location_after"] = delta.location_after

    return result


def _issue_to_dict(issue: QualityIssue) -> dict:
    return {
        "sku": issue.sku,
        "field": issue.field,
        "raw_value": issue.raw_value,
        "description": issue.description,
    }


def build_report(
    result: ReconciliationResult,
    before_path: str,
    after_path: str,
) -> dict:
    return {
        "summary": {
            "snapshot_before": before_path,
            "snapshot_after": after_path,
            "total_before": len(result.changed) + len(result.unchanged) + len(result.removed),
            "total_after": len(result.changed) + len(result.unchanged) + len(result.added),
            "changed": len(result.changed),
            "unchanged": len(result.unchanged),
            "removed": len(result.removed),
            "added": len(result.added),
            "quality_issues": len(result.quality_issues),
        },
        "changed": [_delta_to_dict(d) for d in result.changed],
        "unchanged": [_item_to_dict(i) for i in result.unchanged],
        "removed": [_item_to_dict(i) for i in result.removed],
        "added": [_item_to_dict(i) for i in result.added],
        "quality_issues": [_issue_to_dict(i) for i in result.quality_issues],
    }


def write_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / REPORT_FILENAME

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    logger.info("Report written to %s", report_path)
    return report_path
