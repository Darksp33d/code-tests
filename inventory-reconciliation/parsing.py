"""CSV snapshot parsing, schema normalization, and data validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

SKU_PATTERN = re.compile(r"^(sku)-?(\d+)$", re.IGNORECASE)

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
