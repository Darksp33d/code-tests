"""Tests for CSV parsing, SKU normalization, and data validation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from parsing import (
    InventoryItem,
    QualityIssue,
    SNAPSHOT_1_COLUMNS,
    normalize_date,
    normalize_sku,
    parse_quantity,
    parse_snapshot,
)


# -- SKU normalization --


def test_normalize_sku_already_canonical():
    assert normalize_sku("SKU-001") == "SKU-001"


def test_normalize_sku_missing_hyphen():
    assert normalize_sku("SKU005") == "SKU-005"


def test_normalize_sku_lowercase():
    assert normalize_sku("sku-008") == "SKU-008"


def test_normalize_sku_lowercase_no_hyphen():
    assert normalize_sku("sku042") == "SKU-042"


def test_normalize_sku_with_whitespace():
    assert normalize_sku("  SKU-010 ") == "SKU-010"


# -- Quantity parsing --


def test_parse_quantity_clean_integer():
    value, issues = parse_quantity("150", "SKU-001")
    assert value == 150
    assert issues == []


def test_parse_quantity_float_representation():
    value, issues = parse_quantity("70.0", "SKU-002")
    assert value == 70
    assert len(issues) == 1
    assert issues[0].description == "Non-integer quantity representation"


def test_parse_quantity_float_with_trailing_zeros():
    value, issues = parse_quantity("80.00", "SKU-007")
    assert value == 80
    assert len(issues) == 1
    assert "Non-integer" in issues[0].description


def test_parse_quantity_negative():
    value, issues = parse_quantity("-5", "SKU-045")
    assert value == -5
    assert any(i.description == "Negative quantity" for i in issues)


def test_parse_quantity_non_numeric_raises():
    with pytest.raises(ValueError, match="Non-numeric quantity"):
        parse_quantity("abc", "SKU-099")


# -- Date normalization --


def test_normalize_date_iso_format_unchanged():
    date, issues = normalize_date("2024-01-15", "SKU-001")
    assert date == "2024-01-15"
    assert issues == []


def test_normalize_date_us_format_converted():
    date, issues = normalize_date("01/15/2024", "SKU-035")
    assert date == "2024-01-15"
    assert len(issues) == 1
    assert "Non-ISO date format" in issues[0].description


# -- Full snapshot parsing --


def _write_csv(tmp_path: Path, content: str) -> Path:
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(textwrap.dedent(content).lstrip())
    return csv_file


def test_parse_snapshot_basic(tmp_path: Path):
    csv_file = _write_csv(tmp_path, """\
        sku,name,quantity,location,last_counted
        SKU-001,Widget A,100,Warehouse A,2024-01-08
        SKU-002,Widget B,50,Warehouse B,2024-01-08
    """)

    snapshot = parse_snapshot(csv_file, SNAPSHOT_1_COLUMNS)

    assert len(snapshot.items_by_sku) == 2
    assert snapshot.items_by_sku["SKU-001"].name == "Widget A"
    assert snapshot.items_by_sku["SKU-002"].quantity == 50
    assert snapshot.quality_issues == []


def test_parse_snapshot_strips_whitespace(tmp_path: Path):
    csv_file = _write_csv(tmp_path, """\
        sku,name,quantity,location,last_counted
        SKU-001, Widget A ,100,Warehouse A,2024-01-08
    """)

    snapshot = parse_snapshot(csv_file, SNAPSHOT_1_COLUMNS)
    item = snapshot.items_by_sku["SKU-001"]

    assert item.name == "Widget A"
    assert any(i.field == "name" for i in snapshot.quality_issues)


def test_parse_snapshot_normalizes_sku(tmp_path: Path):
    csv_file = _write_csv(tmp_path, """\
        sku,name,quantity,location,last_counted
        SKU005,Widget,100,Warehouse A,2024-01-08
    """)

    snapshot = parse_snapshot(csv_file, SNAPSHOT_1_COLUMNS)

    assert "SKU-005" in snapshot.items_by_sku
    assert any(i.description == "Non-standard SKU format" for i in snapshot.quality_issues)


def test_parse_snapshot_duplicate_keeps_first(tmp_path: Path):
    csv_file = _write_csv(tmp_path, """\
        sku,name,quantity,location,last_counted
        SKU-001,Widget A,100,Warehouse A,2024-01-08
        SKU-001,Widget A Updated,999,Warehouse B,2024-01-09
    """)

    snapshot = parse_snapshot(csv_file, SNAPSHOT_1_COLUMNS)

    assert len(snapshot.items_by_sku) == 1
    assert snapshot.items_by_sku["SKU-001"].quantity == 100
    assert snapshot.items_by_sku["SKU-001"].name == "Widget A"
    assert any("Duplicate SKU" in i.description for i in snapshot.quality_issues)


def test_parse_snapshot_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_snapshot(Path("/nonexistent/file.csv"), SNAPSHOT_1_COLUMNS)


def test_parse_snapshot_missing_column(tmp_path: Path):
    csv_file = _write_csv(tmp_path, """\
        sku,wrong_col,quantity,location,last_counted
        SKU-001,Widget A,100,Warehouse A,2024-01-08
    """)

    with pytest.raises(KeyError, match="Expected column"):
        parse_snapshot(csv_file, SNAPSHOT_1_COLUMNS)
