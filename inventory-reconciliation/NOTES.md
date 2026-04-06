# Notes

## Approach

The solution is a three-stage pipeline: **parse → reconcile → report**, each in its own module. Quality issues discovered during parsing are accumulated as structured data and carried through to the final report, so the consumer gets reconciliation results and data quality findings in one place.

All dependencies are stdlib. The only external dependency is `pytest` for testing.

## Assumptions

- **SKU is the primary key.** Items are matched across snapshots by normalized SKU, not by name or location.
- **First occurrence wins.** When a SKU appears more than once in a file, I keep the first row and flag the duplicate. The second `SKU-045` entry (qty=-5) looks like a data error, not a correction.
- **Quantity is always integral.** Values like `70.0` and `80.00` are coerced to `int`. If fractional quantities were meaningful, this assumption would need revisiting.
- **Whitespace is never intentional.** Leading/trailing whitespace in names and SKUs is stripped and flagged, not preserved.

## Key Decisions

**SKU normalization.** The snapshots have inconsistent SKU formatting: `SKU005` (missing hyphen), `sku-008` (lowercase), `SKU018` (missing hyphen). I normalize all to the canonical `SKU-NNN` pattern and flag the originals as quality issues.

**Column mapping.** The two files use different schemas (`name` vs `product_name`, `quantity` vs `qty`, etc.). Each file gets a mapping dict that translates its headers to canonical names. The CLI auto-detects which mapping to use from the CSV header.

**JSON output.** The README permits CSV or JSON. JSON maps naturally to the hierarchical report structure (summary, categorized items, quality issues). A flat CSV would lose structure or require multiple files.

**Negative quantities.** Flagged as a quality issue but still included in reconciliation. The downstream consumer is better positioned to decide whether `-5` is a data error or a legitimate adjustment. The tool reports; it does not censor.

## Data Quality Issues Found

**Snapshot 1** (2 issues):
- `SKU-035`: trailing whitespace in name (`"Cable Ties 100pk "`)
- `SKU-052`: leading whitespace in name (`" Compressed Air Can"`)

**Snapshot 2** (11 issues):
- `SKU-002`: leading whitespace in name (`" Widget B"`), float quantity (`70.0`)
- `SKU-005`: malformed SKU (`SKU005`, missing hyphen)
- `SKU-007`: float quantity (`80.00`)
- `SKU-008`: malformed SKU (`sku-008`, lowercase)
- `SKU-010`: trailing whitespace in name (`"Mounting Bracket Large "`)
- `SKU-018`: malformed SKU (`SKU018`, missing hyphen)
- `SKU-021`: leading and trailing whitespace in name (`" HDMI Cable 3ft "`)
- `SKU-035`: non-ISO date format (`01/15/2024` instead of `2024-01-15`)
- `SKU-045`: duplicate SKU (line 54), negative quantity (`-5`)

**Cross-snapshot:** `SKU-045` name changed from "Multimeter Pro" to "Multimeter Professional".

## Usage

```
cd inventory-reconciliation
python reconcile.py                          # uses default data/ paths
python reconcile.py before.csv after.csv     # custom paths
python reconcile.py -o results/ -v           # custom output dir, verbose
```

Output is written to `output/reconciliation_report.json`. Tests run with `python -m pytest tests/ -v`.
