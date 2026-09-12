# C3 joint 30m+60m reusable BLACKBOX — minimal raw 14:00 handoff

Date: 2026-09-12

Repository: `staryocean0/factorlab-overnight-open-lab`

## Cloud-owned scientific state

The cloud main agent has already frozen the C3 successor identity and result-free reusable BLACKBOX protocol:

- identity: `overnight_previous_session_last_hour_conditioned_open_state_joint_30m_60m_v1`
- protocol: `docs/governance/previous_session_last_hour_conditioned_open_state_joint_30m_60m_blackbox_protocol_v1.json`
- state: `docs/governance/previous_session_last_hour_conditioned_open_state_joint_30m_60m_blackbox_state_v1.json`
- cloud controller: `scripts/run_previous_session_last_hour_conditioned_open_state_joint_blackbox_cloud_raw.py`

Local work is **raw data upload only**. Do not run the controller, regressions, bootstrap, yearly diagnostics, horizon selection or BLACKBOX adjudication.

## Why only one raw clock is missing

The previously accepted D1 raw carrier already supplies CSI1000 exact raw clocks for 2020-11-01..2025-12-31:

- 09:31 open
- 09:35 close
- 10:05 close
- 10:35 close
- 15:00 close

C3 additionally requires only the previous session's last-hour return, so the sole missing source field is **CSI1000 exact 14:00 bar close**.

## Admitted source

Use only the canonical Unified DataHub dataset:

`bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`

Frozen source SHA256:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

Instrument:

`000852.SH` / `CSI1000`

Read window:

`2020-11-01..2025-12-31`

Do not read 2026.

## Required output

Create:

`data/c3_blackbox_raw_1400_2020_2025/csi1000_close_1400_2020_2025.csv`

with exactly these columns:

```csv
trading_day,index_name,symbol,close_1400
```

One row per observed CSI1000 trading day. `close_1400` must be the **exact 14:00 bar close**.

No nearest-clock substitution, forward fill, backward fill, interpolation or resampling. Missing exact 14:00 remains missing.

Also create:

- `data/c3_blackbox_raw_1400_2020_2025/manifest.json`
- `data/c3_blackbox_raw_1400_2020_2025/README.md`
- `docs/research/c3_blackbox_raw_1400_upload_receipt_v1.json`

The manifest must contain:

- schema id `overnight_c3_blackbox_raw_1400_carrier@1.0`
- research identity
- source dataset version and SHA256
- read window start/end
- symbol `000852.SH`
- exact clock `14:00`
- exact columns
- output path/SHA256/bytes/rows/min_day/max_day
- transform flags proving no feature engineering, target engineering, scientific analysis, fill, nearest-clock substitution or resampling

The upload receipt may contain only data-engineering provenance. It must explicitly state:

- `scientific_diagnostic_performed: false`
- `BLACKBOX_controller_run: false`
- `BLACKBOX_decision_generated: false`
- `query_5_created: false`
- `2026_rows_loaded: false`

## Hard prohibitions

Do not compute or persist `prev_last_hour`, candidate interaction, returns, coefficients, correlations, R2, bootstrap support, annual results, PASS/FAIL/INSUFFICIENT, or any failure attribution.

Do not modify protocol, state, current authority, registry or BLACKBOX ledger.

## Commit

Commit only the supplemental raw carrier directory and upload receipt:

```bash
git add data/c3_blackbox_raw_1400_2020_2025 \
  docs/research/c3_blackbox_raw_1400_upload_receipt_v1.json
git commit -m "Upload C3 frozen BLACKBOX 14:00 raw carrier [skip ci]"
git push
```

Then stop. The cloud main agent owns technical parity, reusable BLACKBOX query #5, ledger registration and final C3 adjudication.
