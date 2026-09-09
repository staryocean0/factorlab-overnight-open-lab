# V21-RD1 — regime-conditioned gap-fill mechanism diagnostic handoff

## Status

Cloud has closed `gap_fill_cross_index_transport_v1` with a valid but negative
final Audit-B result. A new research identity is active:

`gap_fill_v2_1_regime_conditioned_successor`

RD1 is preregistered, statically tested and execution-frozen. This task is a
**mechanism diagnostic only**. Do not fit or select a V2.1 successor model.

Protocol:

`docs/governance/cloud_session_20260907_gap_fill_v21_regime_diagnostic_protocol_v1.json`

Execution freeze:

`docs/governance/cloud_session_20260907_gap_fill_v21_regime_diagnostic_execution_freeze_v1.json`

Runner:

`scripts/diagnose_gap_fill_v21_regime_consumed.py`

## Scientific question

Audit B failed only for CSI500 high gaps in the `abs_gap > 10bp` cohort at the
15m/60m horizons. RD1 asks whether that residual probability failure is
conditioned by a state available at or before 09:31.

The five frozen probes are:

1. `P1_common_gap_support` — stronger same-direction normalized gap in the other
   broad index should lower fill probability;
2. `P2_relative_gap_excess` — larger target-specific relative gap excess should
   raise fill probability;
3. `P3_trend20_alignment` — gap aligned with prior 20-session trend should lower
   fill probability;
4. `P4_prior_daytime_alignment` — gap aligned with the prior session daytime
   move should lower fill probability;
5. `P5_relative_momentum5_alignment` — gap aligned with recent target-vs-other
   relative momentum should lower fill probability.

Do not add a sixth probe or alter the expected sign after seeing results.

## Authorized outcome-bearing data

Only already-consumed history may be used for RD1:

- CSI300: `2011-01-01 .. 2014-10-16`;
- CSI500: `2011-01-01 .. 2014-10-16`.

The runner may load a small pre-2011 history tail only to construct lagged
`rvol20`, trend and momentum features.

Do **not** open:

- `2014-10-17 .. 2014-12-31` supporting crosscheck;
- any 2015+ CSI300/CSI500 OHLC, gap, fill target or model score;
- any CSI1000 post-2026-08-21 outcome.

## Future blocks are metadata-only in RD1

The runner is allowed to scan only `symbol`, `trading_day`, `timestamp` for
future CSI300/CSI500 coverage. Those date partitions are already frozen:

- `V21_DEV`: `2015-01-01 .. 2018-12-31`;
- `V21_AUDIT_A`: `2019-01-01 .. 2021-12-31`;
- `V21_AUDIT_B`: `2022-01-01 .. 2024-12-31`;
- `V21_EXTERNAL_RESERVE`: `2025-01-01 .. 2026-08-21`.

RD1 must not read OHLC from those future blocks.

## Diagnostic math

For each probe/horizon, the runner starts from the frozen external T2
probability and fits only the one-dimensional consumed-evidence diagnostic:

`logit(p_state) = logit(p_base) + beta * z(probe)`

Frozen beta bounds: `[-6, 6]`.

Minimum diagnostic cell rows: `20`.

This beta is diagnostic only. It is not a probability calibration layer and may
not be promoted directly into a successor.

## Source

Use the admitted raw canonical market-index parquet partition:

`/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index`

Dataset identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

## Commands

```bash
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE='/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index'

python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/diagnose_gap_fill_v21_regime_consumed.py
```

Do not run any V21_DEV selector after this command chain. Cloud must first
adjudicate RD1 and freeze the candidate family.

## Expected outputs

Commit only:

- `docs/research/local_gap_fill_v21_regime_diagnostic_receipt_v1.json`
- `docs/governance/local_gap_fill_v21_regime_diagnostic_data_usage_v1.json`

Do not commit raw historical rows, per-day predictions, or future metadata row
lists.

## Return to cloud

Report/commit:

1. execution commit SHA;
2. validator exit code;
3. pytest exit code and passed count;
4. RD1 runner exit code;
5. source path used;
6. consumed target counts for CSI300/CSI500 and primary CSI500-high >10bp counts
   in pooled / Audit-A / Audit-B;
7. for each P1-P5, 15m/60m beta and log-loss improvement in pooled, Audit-A and
   Audit-B primary cells;
8. CSI300-high >10bp contrast beta signs;
9. each probe's seven diagnostic gates and final
   `mechanism_supported_for_family_design`;
10. future metadata-only block counts / exact-240 counts for CSI300/CSI500;
11. confirmation `2014Q4_supporting_crosscheck_opened=false`;
12. confirmation all V21 future outcome-open flags remain false;
13. confirmation no successor model fit/selection, trading return use or
    production authority occurred.

Cloud will independently review the result and freeze the first bounded V2.1
candidate family before opening `V21_DEV`.
