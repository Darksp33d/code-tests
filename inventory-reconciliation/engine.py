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


def _compare_matched_item(before: InventoryItem, after: InventoryItem) -> ItemDelta | None:
    quantity_changed = before.quantity != after.quantity
    name_changed = before.name != after.name
    location_changed = before.location != after.location

    if not (quantity_changed or name_changed or location_changed):
        return None

    return ItemDelta(
        sku=before.sku,
        name_before=before.name,
        name_after=after.name,
        quantity_before=before.quantity,
        quantity_after=after.quantity,
        quantity_delta=after.quantity - before.quantity,
        location_before=before.location,
        location_after=after.location,
    )


def reconcile(before: ParsedSnapshot, after: ParsedSnapshot) -> ReconciliationResult:
    before_skus = before.items_by_sku.keys()
    after_skus = after.items_by_sku.keys()

    removed_skus = sorted(before_skus - after_skus)
    added_skus = sorted(after_skus - before_skus)
    matched_skus = sorted(before_skus & after_skus)

    changed: list[ItemDelta] = []
    unchanged: list[InventoryItem] = []

    for sku in matched_skus:
        delta = _compare_matched_item(before.items_by_sku[sku], after.items_by_sku[sku])
        if delta is not None:
            changed.append(delta)
        else:
            unchanged.append(before.items_by_sku[sku])

    removed = [before.items_by_sku[sku] for sku in removed_skus]
    added = [after.items_by_sku[sku] for sku in added_skus]
    merged_issues = before.quality_issues + after.quality_issues

    return ReconciliationResult(
        changed=changed,
        unchanged=unchanged,
        removed=removed,
        added=added,
        quality_issues=merged_issues,
    )
