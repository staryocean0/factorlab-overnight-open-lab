# Trend-conditioned opening-state DEV handoff — 2026-09-11

## Goal

Execute the next factor-product research task:

`overnight_trend_conditioned_open_state_v1`

This is a **factor information diagnostic**, not a trading backtest.

The question is whether continuous prior-trend context changes the short-horizon meaning of the observed CSI1000 opening gap.

Frozen candidate increment:

`trend_gap_interaction = observed_gap_rvol * trend20_rvol`

where:

- `observed_gap_rvol = observed_gap / rvol20`
- `trend20_rvol = r20 / (sqrt(20) * rvol20)`

The baseline already includes both main effects, so the interaction receives credit only for conditional information beyond them.

## Evidence boundary

Detailed target/price outcomes may be read only for:

`2019-01-01 .. 2020-12-31`

Do not inspect or report detailed 2021-2025 rows, years, quarters, events, factor-return relationships, or strategy outcomes for this identity. Do not read 2026 outcomes.

This is an independent C1 context-product experiment. Do not use the completed Opening Surprise result as a design input or rescue target.

## Frozen inputs

- protocol: `docs/governance/trend_conditioned_open_state_v1_protocol.json`
- preanalysis: `docs/research/trend_conditioned_open_state_preanalysis_20260911.md`
- runner: `scripts/diagnose_trend_conditioned_open_state_dev.py`
- one-command runner: `scripts/run_trend_conditioned_open_state_dev.sh`

The runner uses:

- frozen 2015-2020 Overnight panel: `data/development/csi1000_open_pit_panel.parquet`
- minute carrier: `data/high_open_dev_2015_2025/1m_official.parquet`, filtered by the runner to 2019-2020 and exact required clocks.

Do not change the trend lookback, normalization, interaction formula, controls, or horizons.

## Execute

From repository root:

```bash
git pull --ff-only
bash scripts/run_trend_conditioned_open_state_dev.sh
```

Expected stdout:

`TREND_CONDITIONED_OPEN_STATE_DEV_DIAGNOSTIC_COMPLETE`

Expected output:

`docs/research/local_trend_conditioned_open_state_dev_diagnostic_v1.json`

## What may be returned

Because 2019-2020 is development material for this identity, the diagnostic receipt may contain the preregistered aggregate and per-year diagnostics for 2019 and 2020.

Do not add:

- `up / range / down` thresholds;
- trend quantile buckets;
- gap-size thresholds;
- volatility conditioning;
- alternate lookbacks;
- alternate horizons;
- Opening Surprise terms;
- trading rules, costs, position sizing, or strategy PnL.

Commit only the diagnostic receipt (and a minimal execution note only if strictly needed) with `[skip ci]`.

Do not update the factor registry, state, current authority, or any BLACKBOX ledger locally. Cloud review will adjudicate the evidence.

## Failure handling

If execution fails, return the traceback/error text without modifying the research formula to make it run. Do not substitute data files, loosen evidence boundaries, forward-fill missing values, or search another definition.

`production_authority=false`.
