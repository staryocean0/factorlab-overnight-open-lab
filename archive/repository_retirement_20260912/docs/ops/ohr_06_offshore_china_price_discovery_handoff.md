# OHR-06 — Offshore-China price-discovery mechanism diagnostic

Status: **waiting for local development-only execution**.

OHR-05 Yahoo source admission has been accepted by cloud review. OHR-06 is now authorized to load 2015-2025 development targets, but it is **not** a candidate-model selection task and must not open 2026.

## Frozen identities

- Source review: `docs/research/offshore_china_ohr05_cloud_source_review_20260906.md`
- Protocol: `docs/governance/cloud_session_20260906_offshore_china_ohr06_diagnostic_protocol_v1.json`
- Execution freeze: `docs/governance/cloud_session_20260906_offshore_china_ohr06_execution_freeze_v1.json`
- Runner: `scripts/diagnose_offshore_china_price_discovery_dev.py`
- Incumbent: `median_quantile_sign`, SHA256 `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`
- Frozen offshore source SHA256: `045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd`

## Required local source

Use the exact Yahoo chart-v8 development parquet already frozen by OHR-05:

`/home/starryocean/.cache/overnight-open-lab/ohr05_offshore_etf_daily_yahoo_chart_v8_2015_2025.parquet`

If the local path differs, the file bytes must still have the exact SHA256 above. Do not regenerate from Yahoo unless the cloud controller first opens a new source identity; OHR-06 is bound to the frozen bytes, not merely the provider name.

Set:

```bash
export OVERNIGHT_OFFSHORE_ETF_DAILY=/absolute/path/to/ohr05_offshore_etf_daily_yahoo_chart_v8_2015_2025.parquet
```

Existing FactorLab/DataHub path overrides may remain unset. The current repository contains the 2015-2025 cloud development pack; local paths may also be used if they preserve the already-audited source identity.

## Execute exactly

```bash
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/diagnose_offshore_china_price_discovery_dev.py
```

## What this run is allowed to do

It replays the accepted Median direction head in 2016-2025 expanding OOF and evaluates only the seven preregistered offshore states:

- `ashs_session`
- `ashr_session`
- `ashs_minus_ashr`
- `a_share_consensus`
- `a_share_specific_vs_spy`
- `broad_china_specific_vs_spy`
- `china_etf_positive_breadth`

Primary slice:

`incumbent predicts low` AND `prev_last_hour < 0`.

The diagnostic asks whether each offshore state is higher on actual-high-open days than actual-low-open days in that unresolved slice.

Zero-volume required ETF sessions are treated as non-informative and excluded via the common diagnostic inventory. They must not be silently filled as zero.

## Mechanism gate

A representation passes its diagnostic mechanism gate only if all are true:

1. pooled actual-up minus actual-down mean difference > 0;
2. positive annual difference in at least 6 of 10 OOF years;
3. median annual difference > 0;
4. Q4 actual-high-open share > Q1 actual-high-open share.

A later bounded candidate family is authorized only if at least one **China-specific** representation passes all gates:

- `ashs_minus_ashr`
- `a_share_specific_vs_spy`
- `broad_china_specific_vs_spy`

Raw ASHS/ASHR/consensus/breadth cannot alone authorize a family because they may simply mirror the US common factor.

OHR-06 itself does not select or fit a new successor.

## Hard denylist

Do not:

- change source/provider/source SHA;
- add/remove tickers;
- change representation formulas or weights;
- add thresholds/interactions after seeing the target;
- search quantile/alpha/threshold/class weights;
- optimize trading return;
- load 2026-01-05..2026-08-21;
- read post-2026-08-21 targets;
- open OHR-03.

## Expected outputs

Only small aggregate artifacts:

- `docs/research/cloud_session_20260906_local_offshore_china_ohr06_diagnostic_receipt_v1.json`
- `docs/governance/local_session_20260906_offshore_china_ohr06_data_usage.json`

Do not commit raw Yahoo ETF rows or row-level OOF predictions.

## Local feedback required

Return / append:

- execution commit SHA;
- three command exit codes and pytest count;
- exact offshore source SHA verification;
- `n_incumbent_oof`, `n_common_offshore_oof`, `n_primary_slice`;
- zero-session / zero-volume exclusion audit;
- for all seven representations: pooled mean/median/standardized difference, positive-year count, median annual difference, Q1/Q4 actual-up shares, mechanism-gate result;
- `china_specific_passers`, `decision`;
- output paths and hashes;
- confirmation that 2026/OHR-03 remained unopened.

Cloud review will decide whether the evidence is strong enough to preregister a later bounded candidate family. If no China-specific representation passes, retain the incumbent and close this source identity without opening 2026.
