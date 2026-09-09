# Gap-Fill V2 2026 repeat data pack

User-authorized public copy of the frozen repeat-only inputs for
`scripts/evaluate_local_gap_fill_v2_2026_repeat.py`.

This pack is **repeat-only** material for `2026-01-05` through `2026-08-21`.
It is not fresh OOS and has no production authority. Post-2026-08-21 remains
excluded.

## Files

- `annotated_panel_2025Q4_to_20260821.parquet`
- `csi1000_1m_20260105_to_20260821.parquet`
- `manifest.json`

The annotated panel starts at the first session on or after `2025-10-01` so
the frozen `rvol20` can be computed. The one-minute file is strictly the
frozen 2026 window; the evaluator rejects any minute row outside
`2026-01-05`..`2026-08-21`.

## Cloud commands

From the overnight-open-lab repository root, after this pack is present:

```bash
export OVERNIGHT_ANNOTATED_PANEL="$PWD/data/gap_fill_repeat_2026/annotated_panel_2025Q4_to_20260821.parquet"
export OVERNIGHT_DATAHUB_1M="$PWD/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/evaluate_local_gap_fill_v2_2026_repeat.py
```

No FRED, Yahoo ETF, or V1 files are included. Do not load any row after
2026-08-21. Do not refit the sealed scaler or Logistic coefficients.
