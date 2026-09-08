# R5 statistical-state-extremes Stage-1 execution handoff — 2026-09-08

Task ID: `R5-STAGE1-EXEC-01`

Research identity: `R5_statistical_state_extremes_stage1_v1`

## Purpose

Execute exactly the frozen first-pass R5 screen. This is a mechanism screen, not a strategy backtest.

The candidate budget is fixed at three statistical-state properties across two already-frozen directional-change scales:

- `R5_A_path_efficiency`
- `R5_B_volatility_state_displacement`
- `R5_C_event_density`
- scales: `S1`, `S2`

No new property, scale, normalization window, interaction, threshold or model class may be added during execution.

## Frozen identity

Read before execution:

- `docs/research/rmr_R5_statistical_state_extremes_preanalysis_20260908.md`
- `docs/governance/reversal_mean_reversion_stage1_common_data_roles_v1.json`
- `docs/governance/reversal_mean_reversion_stage1_scale_contract_v1.json`
- `docs/governance/reversal_mean_reversion_R5_stage1_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R5_stage1_execution_freeze_v1.json`

Runner:

- `scripts/run_rmr_R5_stage1.py`

Tests:

- `tests/test_rmr_R5_stage1.py`

Common source:

- `data/high_open_dev_2015_2025/1m_official.parquet`
- SHA256 `11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce`

## Evidence boundary

The runner is hard-limited to:

- DEV: `2015-01-05 .. 2019-12-31`
- chronological stability: `2020-01-01 .. 2022-12-31`, explicitly not fresh

It must not open:

- `2023-01-01 .. 2025-12-31` internal broad-program reserve
- any 2026 row
- any legacy sealed/fresh R4 outcome

The full parquet contains 2015-2025 history, but the runner reads with a hard `trading_day <= 2022-12-31` filter and records `rows_2023_or_later = 0`.

## Frozen measurement semantics

Normalization for every property:

- past-only reference window: preceding 100 completed same-scale observations
- center: median
- scale: MAD
- current observation excluded from its own reference
- zero/nonfinite MAD observations excluded
- `abs(z) >= 2` is descriptive only, never a selected threshold

Price-path outcome:

- after a completed same-scale event, reverse by one frozen scale before extending by one frozen scale, versus extend first
- same-bar tie is censored
- max horizon 1200 observed 1m bars
- unresolved events are censored

Primary model comparison per property/scale:

1. severity-only baseline
2. the same baseline plus exactly one frozen property z-score

No PnL is used.

## Local commands

Run from repository root on the execution-frozen commit or an exact descendant that has not modified the protocol/runner/tests:

```bash
python3 -m pytest -q tests/test_rmr_R5_stage1.py
python3 scripts/run_rmr_R5_stage1.py \
  --parquet data/high_open_dev_2015_2025/1m_official.parquet \
  --output docs/research/local_rmr_R5_stage1_receipt_v1.json \
  --usage-output docs/governance/local_rmr_R5_stage1_data_usage_v1.json
```

Do not edit protocol/runner/tests after seeing output.

## Expected outputs

Commit only compact aggregate artifacts:

- `docs/research/local_rmr_R5_stage1_receipt_v1.json`
- `docs/governance/local_rmr_R5_stage1_data_usage_v1.json`

No raw event rows or row-level scores.

## Mandatory acceptance checks

The receipt must show:

- exact properties `[R5_A_path_efficiency, R5_B_volatility_state_displacement, R5_C_event_density]`
- exact scales `[S1, S2]`
- reference window `100`
- source max day `<= 2022-12-31`
- `rows_2023_or_later == 0`
- `reserve_2023_2025_opened == false`
- `2026_rows_loaded == false`
- no scale search
- no z-threshold search
- no volatility-window search
- no event-density-window search
- no interaction/ensemble search
- no probability calibration
- no binary threshold selection
- no deep/frequency model
- no trading-return use
- no raw event rows written
- `scientifically_fresh == false`
- `production_authority == false`

If any check fails, do not interpret R5 results and do not open the reserve.

## After execution

Cloud adjudication will compare all six property×scale cells. A property may progress only if it adds stable held-forward information beyond the frozen severity baseline and does not rely merely on mechanical reversion of the statistic itself. If none survives, R5 Stage-1 v1 closes; no indicator expansion is allowed as rescue.
