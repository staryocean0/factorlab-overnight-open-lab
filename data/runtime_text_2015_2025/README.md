# Runtime text pack (connector-readable carrier)

This directory is a **connector-readable runtime carrier**.

It is **not**:

- a new scientific dataset
- a new fresh OOS sample
- a new factor authority
- a production dataset

> Physical/textual accessibility does not by itself grant evidence authority.

Even after these files can be read by a cloud connector, every research identity must still obey its own protocol, state, and BLACKBOX policy. Being able to open a CSV does not reopen 2021-2025 detailed evidence, does not authorize feature changes, and does not grant production authority.

## Why this pack exists

Cloud GitHub connectors cannot stably hand complete bytes of the large binary parquet files to the compute environment. This pack is the smallest necessary **text** projection of already-frozen development material:

- row filter by calendar year
- column filter of already-materialized causal fields
- exact-clock pivot of already-stored one-minute closes
- CSV serialization

No values are recomputed. No clocks are nearest-matched. No forward/back fill is applied. Missing exact clocks stay missing.

The original parquet files remain the provenance sources and must not be deleted.

## Published window

Committed text shards cover **2015-01-05 .. 2020-12-31** only.

`2021-2025` row-level factor/clock CSVs are **not** generated or committed here. That interval remains a reusable BLACKBOX. Current authority forbids converting those detailed rows into a public text pack, and `annotated_panel.parquet` does not already contain the reconstructed 2021-2025 feature columns. Reconstructing them would be feature engineering, which this carrier must not do.

The conversion script defaults to a 2015-2025 *supported* window so later cloud adjudication can decide whether BLACKBOX text shards may ever be emitted. Until that decision, the script withholds 2021-2025.

## Files

Year-split factor panels:

- `factor_panel_2015.csv` ... `factor_panel_2020.csv`

One row = one `trading_day`, sorted ascending, dates `YYYY-MM-DD`.

Columns:

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

The last three columns are included only because the frozen V6A reconstruction contract already materializes them on the 2015-2020 development panel. They are copied, not recalculated.

Year-split opening-clock carriers:

- `opening_clocks_2015.csv` ... `opening_clocks_2020.csv`

Wide schema:

```text
trading_day,close_0935,close_0950,close_1005,close_1035
```

Exact clocks only: `09:35`, `09:50`, `10:05`, `10:35`. Instrument: `000852.SH`.

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

`--end-year 2025` does **not** publish 2021-2025 text shards.

Parity receipt:

`docs/research/runtime_text_carrier_parity_receipt_v1.json`

That receipt records only data-engineering hashes, inventories, and PASS/FAIL. It contains no alpha, return, or strategy results.

`production_authority=false`.
