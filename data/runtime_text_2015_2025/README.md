# Runtime text pack, 2015-2025 intended window

This directory is a **connector-readable runtime carrier**.

It is **not**:

- a new scientific dataset
- a new fresh OOS
- a new factor authority
- a production dataset

> Physical/textual accessibility does not by itself grant evidence authority.

Even after these files can be read by a cloud connector, every research identity must still obey its own protocol, state file, and reusable BLACKBOX policy. Reading this pack does not open 2021-2025 detailed evidence, does not authorize factor admission, and does not change production authority.

## What is committed here

The committed shards cover only the already-opened development window:

```text
2015-01-05 .. 2020-12-31
```

Each year has:

- `factor_panel_YYYY.csv` — one row per `trading_day`, sorted ascending, dates as `YYYY-MM-DD`
- `opening_clocks_YYYY.csv` — exact clocks `09:35`, `09:50`, `10:05`, `10:35` in wide form

`abs_r1`, `us_nasdaq`, and `us_vix_chg` are included because the frozen reconstruction contract already requires those existing causal fields. No new feature was computed.

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

Clock extraction is exact-clock only. A missing `09:35` stays missing. `09:34` is never substituted.

Original parquet files remain the provenance sources. This text pack does not replace them.

See `manifest.json` for SHA256 lineage and `docs/research/runtime_text_carrier_parity_receipt_v1.json` for the data-engineering parity receipt.
