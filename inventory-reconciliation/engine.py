"""Inventory reconciliation engine -- compares two parsed snapshots."""

from __future__ import annotations

from typing import NamedTuple

from parsing import InventoryItem, ParsedSnapshot, QualityIssue


class ItemDelta(NamedTuple):
    sku: str
    name_before: str
    name_after: str
    quantity_before: int
    quantity_after: int
    quantity_delta: int
    location_before: str
    location_after: str


class ReconciliationResult(NamedTuple):
    changed: list[ItemDelta]
    unchanged: list[InventoryItem]
    removed: list[InventoryItem]
    added: list[InventoryItem]
    quality_issues: list[QualityIssue]
