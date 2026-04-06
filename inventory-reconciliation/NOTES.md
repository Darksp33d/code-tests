# Notes

## Approach

The solution is a three-stage pipeline: **parse → reconcile → report**.

Each stage is a separate module with pure functions and no shared mutable state. Data flows forward through NamedTuples. Quality issues are accumulated as structured data alongside parsed items rather than logged and forgotten, so the final report gives consumers the full picture without requiring them to read logs.

All dependencies are stdlib (`csv`, `json`, `re`, `pathlib`, `argparse`, `logging`). The only external dependency is `pytest` for testing.

## Key Decisions

**SKU normalization.** The two snapshots have inconsistent SKU formatting: `SKU005` (missing hyphen), `sku-008` (lowercase), `SKU018` (missing hyphen). I normalize all SKUs to the canonical `SKU-NNN` pattern using a regex, and flag the original value as a quality issue.

**Column mapping.** The snapshots use different schemas (`name` vs `product_name`, `quantity` vs `qty`, etc.). Rather than hardcoding column indices, each snapshot gets a column mapping dict that translates file-specific headers to canonical names. The CLI auto-detects which mapping to use based on the CSV header.

**Duplicate handling.** `SKU-045` appears twice in snapshot 2 — once with valid data (qty=23) and once with a negative quantity (qty=-5). I keep the first occurrence and discard the duplicate, flagging it as a quality issue with full context.

**JSON output.** The README permits CSV or JSON. I chose JSON because the report has a naturally hierarchical structure: summary counts, categorized item lists, and quality issues. A flat CSV would either lose structure or require multiple files.

**Negative quantities.** Flagged as a quality issue but still included in reconciliation. The downstream consumer is better positioned to decide whether a negative quantity is a data error or a legitimate adjustment (e.g., a return). The tool reports; it does not censor.

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
