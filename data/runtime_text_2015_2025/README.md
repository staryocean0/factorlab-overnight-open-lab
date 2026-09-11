# Runtime text pack, 2015-2025 intended window

This directory is a **connector-readable runtime carrier**.

It is **not**:

- a new scientific dataset
- a new fresh OOS
- a new factor authority
- a production dataset

> Physical/textual accessibility does not by itself grant evidence authority.

Even after these files can be read by a cloud connector, every research identity must still obey its own protocol, state file, and reusable BLACKBOX policy. Reading this pack does not open 2021-2025 detailed evidence, does not authorize factor admission, and does not change production authority.

## Why this pack exists

Cloud GitHub connectors cannot stably hand complete bytes of the large binary parquet files to the compute environment. This pack is the smallest necessary **text** projection of already-frozen development material:

- row filter by calendar year
- column filter of already-materialized causal fields
- exact-clock pivot of already-stored one-minute closes
- CSV serialization

No values are recomputed. No clocks are nearest-matched. No forward/back fill is applied. Missing exact clocks stay missing.

The original parquet files remain the provenance sources and must not be deleted.

## What is committed here

The committed shards cover only the already-opened development window:

```text
2015-01-05 .. 2020-12-31
```

Each year has:

- `factor_panel_YYYY.csv` — one row per `trading_day`, sorted ascending, dates as `YYYY-MM-DD`
- `opening_clocks_YYYY.csv` — exact clocks `09:35`, `09:50`, `10:05`, `10:35` in wide form

Factor-panel columns:

```text
trading_day
gap
r1
r20
rvol20
prev_daytime
prev_last_hour
prev_afternoon
holiday_reopen
weekend
prev_gap
overnight_trend_5
abs_r1
us_nasdaq
us_vix_chg
```

`abs_r1`, `us_nasdaq`, and `us_vix_chg` are included because the frozen reconstruction contract already requires those existing causal fields. They are copied, not recalculated. No new feature was computed.

Opening-clock wide schema:

```text
trading_day,close_0935,close_0950,close_1005,close_1035
```

Exact clocks only. Instrument: `000852.SH`. A missing `09:35` stays missing. `09:34` is never substituted.

## What this pack is not allowed to contain

2021-2025 row-level CSV shards are **not** generated or committed. Existing governance already forbids converting that reusable BLACKBOX window into a public text pack:

- `docs/governance/overnight_reusable_blackbox_policy_v1.json`
- `docs/governance/v6a_base_panel_reconstruction_contract_20260910.json`
- `docs/governance/current_authority_v1.json`

Do not infer BLACKBOX sample counts, dates, targets, or scores from the absence of those files.

## Lineage

- Raw provenance source: `data/high_open_dev_2015_2025/annotated_panel.parquet`
- 2015-2020 factor-value authority: `data/development/csi1000_open_pit_panel.parquet`
- Exact-clock source: `data/high_open_dev_2015_2025/1m_official.parquet`

`annotated_panel.parquet` does not contain reconstructed columns such as `r1` / `r20` / `rvol20`. This carrier therefore slices the already-frozen development panel. It does not rerun rolling formulas.

See `manifest.json` for SHA256 lineage and `docs/research/runtime_text_carrier_parity_receipt_v1.json` for the data-engineering parity receipt.

## Rebuild

```bash
python3 scripts/build_runtime_text_carrier.py \
  --annotated-panel data/high_open_dev_2015_2025/annotated_panel.parquet \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --out-dir data/runtime_text_2015_2025
```

Optional bounds:

```text
--start-year 2015
--end-year 2025
```

`--end-year 2025` does **not** publish 2021-2025 text shards. The script withholds that window by default.

`production_authority=false`.
