# OHR-05 — Offshore-China ETF source admission

Status: **waiting for local source-only execution**.

This task freezes the data provider and verifies source/calendar integrity **before any China target or predictive diagnostic is loaded**. OHR-03 remains unopened. `2026-01-05..2026-08-21` remains sealed and post-2026-08-21 remains unread true-fresh evidence.

## Goal

Prepare one development-only daily OHLCV export for the fixed symbols:

- ASHS
- ASHR
- FXI
- MCHI
- SPY

and prove that the source has a usable regular-session calendar and price history for 2015-2025. Do not inspect whether any ticker predicts the CSI1000 gap in this task.

## Scientific reason for this ordering

The next research identity asks whether US-session trading of China-focused ETFs after the A-share close provides a new rebound-versus-continuation state. Data vendors can differ in corrections, adjustment conventions and missing observations. The provider must therefore be frozen before any target diagnostic so we cannot choose the source that happens to backtest best.

Protocol:
`docs/governance/cloud_session_20260906_offshore_china_price_discovery_protocol_v1.json`

Preanalysis:
`docs/research/offshore_china_price_discovery_preanalysis_20260906.md`

Source-only runner:
`scripts/probe_offshore_china_source_quality.py`

## Source preparation

First search existing local market-data caches/DataHub products for a single provider that contains the five symbols with US regular-session daily open, close and volume.

If a suitable local source already exists, use it. Otherwise obtain all five symbols from **one** external provider. Do not mix providers across tickers.

Freeze that provider **before reading any CSI1000 target diagnostic**.

Create a local-only parquet or CSV containing exactly the development-era source data needed by the runner. Required columns:

- `date` — US exchange trading date;
- `symbol`;
- `open` — regular-session market open;
- `close` — regular-session market close;
- `volume` — regular-session volume.

The file must contain no row later than `2025-12-31`. It may contain extra symbols; the runner ignores them, but the five required symbols must all exist.

Do not commit the raw file.

### Price convention

Use one consistent OHLC convention for all symbols and record it in the provider identity / feedback. Same-session `close/open - 1` must represent the US regular-session return. Do not mix adjusted open with raw close or vice versa.

The source-only probe intentionally does not calculate cross-session close-to-close returns, so splits between different US sessions do not create a synthetic return. If the chosen provider supplies adjusted OHLC, state the adjustment convention; if it supplies raw OHLC, state that explicitly.

## Required environment variables

Set:

```bash
export OVERNIGHT_OFFSHORE_ETF_DAILY=/absolute/path/to/development_only_source.parquet
export OVERNIGHT_OFFSHORE_ETF_PROVIDER='provider-name-and-interface'
export OVERNIGHT_OFFSHORE_ETF_PROVIDER_ID='optional export/cache/version identity'
```

Only `OVERNIGHT_OFFSHORE_ETF_PROVIDER_ID` is optional.

## Execute

```bash
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/probe_offshore_china_source_quality.py
```

## Hard denylist during OHR-05

Do not read or use for source choice:

- any 2026 target/prediction material;
- `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json` result fields;
- post-2026-08-21 targets;
- any CSI1000 2015-2025 gap relationship with ASHS/ASHR/FXI/MCHI/SPY;
- any model performance produced from these new ETF fields.

Governance documents may be read only to preserve the evidence boundary.

Do not change the fixed symbol set after seeing source quality unless the cloud controller first records an infrastructure failure and opens a new source identity. In particular, do not replace an inconvenient/illiquid ticker because another ticker appears more predictive.

## Expected outputs

The runner writes only:

- `docs/research/cloud_session_20260906_local_offshore_china_source_freeze_v1.json`
- `docs/governance/local_session_20260906_offshore_china_source_data_usage.json`

The receipt must state `predictive_target_loaded=false`, `candidate_selection_performed=false`, `2026_rows_loaded=false`, and `2026_blackbox_opened=false`.

## Local feedback required

Append to `docs/ops/cloud_local_communication.md` or return to the cloud controller:

- execution commit SHA;
- provider and provider/export identity;
- whether OHLC is raw or adjusted;
- local source SHA256;
- three command exit codes and pytest count;
- per-symbol total coverage vs SPY, missing count, invalid-price/volume count, zero-volume and zero-return counts;
- notable yearly coverage gaps;
- extreme same-session return diagnostics;
- output file paths and hashes;
- any unresolved measurement issue.

Do not upload raw ETF rows.

## Cloud acceptance

The cloud controller will review source quality without reading a China-target predictive result. If the provider/calendar is accepted, it will freeze OHR-06 and only then permit the development diagnostic using the preregistered source representations. If source integrity is unresolved, status is `infrastructure_or_measurement_gap`; there is no predictive experiment and 2026 remains sealed.
