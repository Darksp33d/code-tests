"""Tests for report generation and JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from engine import ItemDelta, ReconciliationResult
from parsing import InventoryItem, QualityIssue
from reporting import build_report, write_report


def _minimal_result() -> ReconciliationResult:
    changed = [
        ItemDelta("SKU-001", "Widget", "Widget", 100, 80, -20, "WH-A", "WH-A"),
    ]
    unchanged = [
        InventoryItem("SKU-002", "Gadget", 50, "WH-B", "2024-01-08"),
    ]
    removed = [
        InventoryItem("SKU-003", "Cable", 200, "WH-C", "2024-01-08"),
    ]
    added = [
        InventoryItem("SKU-099", "New Item", 10, "WH-A", "2024-01-15"),
    ]
    issues = [
        QualityIssue("SKU-001", "quantity", "80.0", "Non-integer quantity"),
    ]
    return ReconciliationResult(changed, unchanged, removed, added, issues)


def test_build_report_summary_counts():
    result = _minimal_result()
    report = build_report(result, "before.csv", "after.csv")

    summary = report["summary"]
    assert summary["snapshot_before"] == "before.csv"
    assert summary["snapshot_after"] == "after.csv"
    assert summary["total_before"] == 3
    assert summary["total_after"] == 3
    assert summary["changed"] == 1
    assert summary["unchanged"] == 1
    assert summary["removed"] == 1
    assert summary["added"] == 1
    assert summary["quality_issues"] == 1


def test_build_report_has_all_sections():
    report = build_report(_minimal_result(), "a.csv", "b.csv")

    assert set(report.keys()) == {"summary", "changed", "unchanged", "removed", "added", "quality_issues"}


def test_build_report_delta_omits_unchanged_fields():
    result = _minimal_result()
    report = build_report(result, "a.csv", "b.csv")

    delta = report["changed"][0]
    assert "name_before" not in delta
    assert "location_before" not in delta
    assert delta["quantity_delta"] == -20


def test_build_report_delta_includes_name_change():
    changed = [ItemDelta("SKU-001", "Old Name", "New Name", 100, 100, 0, "WH-A", "WH-A")]
    result = ReconciliationResult(changed, [], [], [], [])
    report = build_report(result, "a.csv", "b.csv")

    delta = report["changed"][0]
    assert delta["name_before"] == "Old Name"
    assert delta["name_after"] == "New Name"


def test_write_report_creates_file(tmp_path: Path):
    report = build_report(_minimal_result(), "a.csv", "b.csv")
    report_path = write_report(report, tmp_path)

    assert report_path.exists()
    assert report_path.name == "reconciliation_report.json"

    loaded = json.loads(report_path.read_text())
    assert loaded["summary"]["changed"] == 1


def test_write_report_creates_output_directory(tmp_path: Path):
    nested_dir = tmp_path / "deep" / "nested"
    report = build_report(_minimal_result(), "a.csv", "b.csv")

    report_path = write_report(report, nested_dir)

    assert report_path.exists()
    assert nested_dir.exists()


def test_report_json_is_deterministic(tmp_path: Path):
    report = build_report(_minimal_result(), "a.csv", "b.csv")

    path_a = write_report(report, tmp_path / "run_a")
    path_b = write_report(report, tmp_path / "run_b")

    assert path_a.read_text() == path_b.read_text()
