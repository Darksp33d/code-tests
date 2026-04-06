"""CSV snapshot parsing, schema normalization, and data validation."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)

SKU_PATTERN = re.compile(r"^(sku)-?(\d+)$", re.IGNORECASE)
US_DATE_PATTERN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

SNAPSHOT_1_COLUMNS = {
    "sku": "sku",
    "name": "name",
    "quantity": "quantity",
    "location": "location",
    "last_counted": "counted_at",
}

SNAPSHOT_2_COLUMNS = {
    "sku": "sku",
    "product_name": "name",
    "qty": "quantity",
    "warehouse": "location",
    "updated_at": "counted_at",
}


class InventoryItem(NamedTuple):
    sku: str
    name: str
    quantity: int
    location: str
    counted_at: str


class QualityIssue(NamedTuple):
    sku: str
    field: str
    raw_value: str
    description: str


class ParsedSnapshot(NamedTuple):
    items_by_sku: dict[str, InventoryItem]
    quality_issues: list[QualityIssue]


def normalize_sku(raw_sku: str) -> str:
    stripped = raw_sku.strip()
    match = SKU_PATTERN.match(stripped)
    if not match:
        return stripped.upper()
    digits = match.group(2)
    return f"SKU-{digits}"


def parse_quantity(raw_value: str, sku: str) -> tuple[int, list[QualityIssue]]:
    issues: list[QualityIssue] = []
    stripped = raw_value.strip()

    try:
        as_float = float(stripped)
    except ValueError:
        raise ValueError(f"Non-numeric quantity '{stripped}' for {sku}")

    as_int = int(as_float)

    if stripped != str(as_int):
        issues.append(QualityIssue(sku, "quantity", stripped, "Non-integer quantity representation"))

    if as_int < 0:
        issues.append(QualityIssue(sku, "quantity", stripped, "Negative quantity"))

    return as_int, issues


def normalize_date(raw_value: str, sku: str) -> tuple[str, list[QualityIssue]]:
    issues: list[QualityIssue] = []
    stripped = raw_value.strip()

    us_match = US_DATE_PATTERN.match(stripped)
    if us_match:
        month, day, year = us_match.groups()
        issues.append(QualityIssue(sku, "counted_at", stripped, "Non-ISO date format (MM/DD/YYYY)"))
        return f"{year}-{month}-{day}", issues

    return stripped, issues


def _flag_whitespace(raw_value: str, sku: str, field: str) -> list[QualityIssue]:
    if raw_value != raw_value.strip():
        return [QualityIssue(sku, field, repr(raw_value), "Leading/trailing whitespace")]
    return []


def _map_row(
    raw_row: dict[str, str],
    column_mapping: dict[str, str],
) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for file_col, canonical_col in column_mapping.items():
        if file_col not in raw_row:
            raise KeyError(f"Expected column '{file_col}' not found. Got: {list(raw_row.keys())}")
        mapped[canonical_col] = raw_row[file_col]
    return mapped


def parse_snapshot(
    csv_path: Path,
    column_mapping: dict[str, str],
) -> ParsedSnapshot:
    if not csv_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {csv_path}")

    items_by_sku: dict[str, InventoryItem] = {}
    quality_issues: list[QualityIssue] = []

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        for line_number, raw_row in enumerate(reader, start=2):
            mapped = _map_row(raw_row, column_mapping)

            raw_sku = mapped["sku"]
            normalized_sku = normalize_sku(raw_sku)

            if raw_sku.strip() != normalized_sku:
                quality_issues.append(
                    QualityIssue(normalized_sku, "sku", raw_sku.strip(), "Non-standard SKU format")
                )

            raw_name = mapped["name"]
            quality_issues.extend(_flag_whitespace(raw_name, normalized_sku, "name"))
            name = raw_name.strip()

            quantity, qty_issues = parse_quantity(mapped["quantity"], normalized_sku)
            quality_issues.extend(qty_issues)

            raw_location = mapped["location"]
            quality_issues.extend(_flag_whitespace(raw_location, normalized_sku, "location"))
            location = raw_location.strip()

            counted_at, date_issues = normalize_date(mapped["counted_at"], normalized_sku)
            quality_issues.extend(date_issues)

            if normalized_sku in items_by_sku:
                quality_issues.append(
                    QualityIssue(
                        normalized_sku,
                        "sku",
                        f"line {line_number}",
                        f"Duplicate SKU (keeping first occurrence, discarding: {name}, qty={quantity})",
                    )
                )
                logger.warning("Duplicate SKU %s at line %d -- skipping", normalized_sku, line_number)
                continue

            items_by_sku[normalized_sku] = InventoryItem(
                sku=normalized_sku,
                name=name,
                quantity=quantity,
                location=location,
                counted_at=counted_at,
            )

    logger.debug("Parsed %d items from %s (%d quality issues)", len(items_by_sku), csv_path.name, len(quality_issues))
    return ParsedSnapshot(items_by_sku, quality_issues)
