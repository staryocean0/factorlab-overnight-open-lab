# Volatility-conditioned opening state — preanalysis (2026-09-11)

## Research identity

`overnight_volatility_conditioned_open_state_v1`

Product family:

`OFP-C2_prior_volatility_context_x_OFP-A2_observed_open_geometry`

## Question

Does the same volatility-normalized CSI1000 opening gap have a different short-horizon meaning when it occurs in a different pre-open realized-volatility environment?

This is a context-factor information diagnostic, not a trading backtest.

## Frozen continuous coordinates

`observed_gap_rvol = observed_gap / rvol20`

`trend20_rvol = r20 / (sqrt(20) * rvol20)`

Validated C1 interaction carried as a baseline control:

`trend_gap_interaction = observed_gap_rvol * trend20_rvol`

C2 volatility coordinate:

`log_rvol20 = log(rvol20)`

C2 candidate increment:

`vol_gap_interaction = observed_gap_rvol * log_rvol20`

`rvol20` must be finite and strictly positive. No epsilon floor is allowed.

Because the baseline already contains `observed_gap_rvol`, adding a constant to `log_rvol20` only adds a multiple of an existing baseline column. Therefore the incremental interaction test is invariant to expressing volatility in decimal versus percentage units.

## Why this is distinct from C1

C1 established that prior trend changes the 15-minute meaning of the observed opening gap. C2 must not receive credit for rediscovering that relation.

The C2 baseline therefore includes:

- `observed_gap_rvol`
- `log_rvol20`
- `trend20_rvol`
- `trend_gap_interaction`
- `r1`
- `prev_daytime`
- `holiday_reopen`

The candidate adds exactly one term:

- `vol_gap_interaction`

## Development evidence boundary

Detailed evidence is restricted to the already-opened text development pack:

`data/development/trend_open_state_dev_pack_2019_2020/`

Window:

`2019-01-01 .. 2020-12-31`

No detailed 2021-2025 outcome is authorized for this identity. No 2026 outcome is authorized.

## Frozen short-horizon targets

Reference clock: `09:35`.

Targets:

- `09:35 -> 09:50`
- `09:35 -> 10:05`
- `09:35 -> 10:35`

These are inherited mechanism horizons. They are not a search over trading exits.

## Diagnostics

For pooled 2019-2020 and separately for 2019 and 2020:

- partial correlation of `vol_gap_interaction` with the target after baseline controls;
- baseline R²;
- candidate R²;
- delta R²;
- standardized interaction coefficient;
- complete-case count.

No automatic promotion threshold is encoded. Main-agent adjudication will require directional stability across the two development years and economically interpretable incremental information before any later reusable BLACKBOX identity is frozen.

## Explicit prohibitions

This identity does not authorize:

- high-vol / low-vol buckets;
- volatility quantile or threshold search;
- alternate volatility lookbacks;
- alternate gap normalizations;
- alternate target horizons;
- trend-threshold rescue;
- Opening Surprise terms;
- downstream strategy PnL, cost, sizing, or execution optimization;
- detailed 2021-2025 inspection;
- 2026 outcome inspection.

`production_authority=false`.
