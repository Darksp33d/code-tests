"""Tests for the inventory reconciliation engine."""

from __future__ import annotations

from engine import reconcile, ItemDelta
from parsing import InventoryItem, ParsedSnapshot, QualityIssue


def _item(sku: str, name: str = "Widget", quantity: int = 100, location: str = "WH-A") -> InventoryItem:
    return InventoryItem(sku=sku, name=name, quantity=quantity, location=location, counted_at="2024-01-08")


def _snapshot(
    items: list[InventoryItem] | None = None,
    issues: list[QualityIssue] | None = None,
) -> ParsedSnapshot:
    items = items or []
    return ParsedSnapshot(
        items_by_sku={item.sku: item for item in items},
        quality_issues=issues or [],
    )


# -- Matched items --


def test_reconcile_quantity_change():
    before = _snapshot([_item("SKU-001", quantity=100)])
    after = _snapshot([_item("SKU-001", quantity=80)])

    result = reconcile(before, after)

    assert len(result.changed) == 1
    assert result.changed[0].quantity_delta == -20
    assert result.unchanged == []


def test_reconcile_unchanged():
    item = _item("SKU-001", name="Widget", quantity=100, location="WH-A")
    before = _snapshot([item])
    after = _snapshot([item])

    result = reconcile(before, after)

    assert result.changed == []
    assert len(result.unchanged) == 1
    assert result.unchanged[0].sku == "SKU-001"


def test_reconcile_name_change():
    before = _snapshot([_item("SKU-001", name="Multimeter Pro")])
    after = _snapshot([_item("SKU-001", name="Multimeter Professional")])

    result = reconcile(before, after)

    assert len(result.changed) == 1
    delta = result.changed[0]
    assert delta.name_before == "Multimeter Pro"
    assert delta.name_after == "Multimeter Professional"
    assert delta.quantity_delta == 0


def test_reconcile_location_change():
    before = _snapshot([_item("SKU-001", location="WH-A")])
    after = _snapshot([_item("SKU-001", location="WH-B")])

    result = reconcile(before, after)

    assert len(result.changed) == 1
    assert result.changed[0].location_before == "WH-A"
    assert result.changed[0].location_after == "WH-B"


# -- Removed and added --


def test_reconcile_removed_item():
    before = _snapshot([_item("SKU-001"), _item("SKU-002")])
    after = _snapshot([_item("SKU-001")])

    result = reconcile(before, after)

    assert len(result.removed) == 1
    assert result.removed[0].sku == "SKU-002"


def test_reconcile_added_item():
    before = _snapshot([_item("SKU-001")])
    after = _snapshot([_item("SKU-001"), _item("SKU-099")])

    result = reconcile(before, after)

    assert len(result.added) == 1
    assert result.added[0].sku == "SKU-099"


# -- Edge cases --


def test_reconcile_both_empty():
    result = reconcile(_snapshot(), _snapshot())

    assert result.changed == []
    assert result.unchanged == []
    assert result.removed == []
    assert result.added == []
    assert result.quality_issues == []


def test_reconcile_no_overlap():
    before = _snapshot([_item("SKU-001")])
    after = _snapshot([_item("SKU-099")])

    result = reconcile(before, after)

    assert len(result.removed) == 1
    assert len(result.added) == 1
    assert result.changed == []
    assert result.unchanged == []


def test_reconcile_quality_issues_merged():
    issue_before = QualityIssue("SKU-001", "name", "' Widget '", "Whitespace")
    issue_after = QualityIssue("SKU-002", "quantity", "-5", "Negative")

    before = _snapshot([_item("SKU-001")], issues=[issue_before])
    after = _snapshot([_item("SKU-001")], issues=[issue_after])

    result = reconcile(before, after)

    assert len(result.quality_issues) == 2
    assert issue_before in result.quality_issues
    assert issue_after in result.quality_issues


def test_reconcile_output_sorted_by_sku():
    before = _snapshot([_item("SKU-003"), _item("SKU-001")])
    after = _snapshot([_item("SKU-003", quantity=50), _item("SKU-001", quantity=50)])

    result = reconcile(before, after)

    skus = [d.sku for d in result.changed]
    assert skus == sorted(skus)
