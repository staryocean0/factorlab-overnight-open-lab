# Trend-conditioned opening state — preanalysis (2026-09-11)

## Research identity

`overnight_trend_conditioned_open_state_v1`

## Motivation

The Overnight/Open factor program needs context products that tell downstream timing and stock-selection systems whether the same observed opening state has different short-horizon meaning under different causal pre-open market states.

The user-motivated intuition includes ideas such as high-open during an uptrend versus high-open during a downtrend. This experiment deliberately does **not** start with categorical `up / range / down` labels because any such thresholds would introduce avoidable degrees of freedom.

Instead, the first test uses one continuous trend coordinate and one continuous opening-gap coordinate.

## Frozen coordinates

`observed_gap_rvol = observed_gap / rvol20`

`trend20_rvol = r20 / (sqrt(20) * rvol20)`

Candidate interaction:

`trend_gap_interaction = observed_gap_rvol * trend20_rvol`

The baseline contains both main effects. Therefore the interaction receives credit only if prior trend changes the relationship between the opening gap and the later short-horizon path.

This is the continuous analogue of asking whether a high/low open means something different in different prior trend states, without inventing regime thresholds.

## Evidence boundary

Detailed development evidence is restricted to:

`2019-01-01 .. 2020-12-31`

No detailed 2021-2025 outcomes may be opened for this identity. No 2026 outcome may be read.

The completed Opening Surprise diagnostic is negative evidence for that separate identity. Its observed coefficient signs, magnitude, or year split may not be used to tune this interaction. The C1 trend-context experiment was already the next preregistered shelf item before the Opening Surprise result was observed.

## Fixed information targets

Reference clock: `09:35`.

Targets:

- `09:35 -> 09:50`
- `09:35 -> 10:05`
- `09:35 -> 10:35`

These horizons are inherited as fixed short-horizon information diagnostics, not searched for a best trading interval.

## Baseline comparison

Baseline controls:

- `observed_gap_rvol`
- `trend20_rvol`
- `r1`
- `prev_daytime`
- `holiday_reopen`

Candidate adds exactly one term:

- `trend_gap_interaction`

Diagnostics are descriptive/incremental-information diagnostics only:

- partial correlation of the interaction with the target after baseline controls;
- baseline vs candidate R²;
- delta R²;
- standardized interaction coefficient;
- pooled and separate 2019/2020 results;
- complete-case count.

## Adjudication principle

A useful context product should show more than a pooled in-sample numerical improvement. Main-agent review will require economically interpretable incremental information and directional stability across the two independent development years before any later BLACKBOX protocol or categorical adapter view can be considered.

A sign reversal across 2019 and 2020 is strong negative evidence against a single stable interaction product.

No automatic pass threshold is encoded in the runner; scientific adjudication remains with the cloud main agent to avoid turning a two-year mechanism diagnostic into a mechanically optimized selection exercise.

## Explicitly forbidden

This phase does not authorize:

- up/range/down threshold search;
- quantile or bucket search on trend;
- high/low gap threshold search;
- volatility conditioning;
- Opening Surprise rescue interactions;
- alternate lookback search;
- alternate horizon search;
- strategy PnL or cost optimization;
- position sizing;
- 2021-2025 detailed outcome inspection;
- 2026 outcome inspection.

`production_authority=false`.
