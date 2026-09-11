# Trend open-state cloud dev pack (2019–2020)

Text-only development slice for `overnight_trend_conditioned_open_state_v1`.
Cloud runners can reproduce the local parquet diagnostic without reading binary parquet.

## Files

- `base_panel_2019_2020.csv` — 487 rows; columns `trading_day`, `gap`, `r20`, `rvol20`, `r1`, `prev_daytime`, `holiday_reopen`
- `minute_clocks_2019_2020.csv` — 1948 rows; columns `trading_day`, `clock`, `close` for clocks `09:35`, `09:50`, `10:05`, `10:35`
- `manifest.json` — row counts, dev-pack hashes, and source parquet hashes for audit linkage

## Execute (cloud)

```bash
bash scripts/run_trend_conditioned_open_state_dev_cloud.sh
```

Expected receipt: `docs/research/cloud_trend_conditioned_open_state_dev_diagnostic_v1.json`

Diagnostic numerics should match the local parquet receipt; `source_hashes` bind to this dev pack instead of parquet paths.
