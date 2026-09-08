# R2 preanalysis — Range-boundary / failed-breakout reversion

Date: 2026-09-08  
Identity: `R2_range_boundary_reversion_stage1_v1`  
Role: results-blind shallow screen, not strategy optimization.

## Question

When the parent state is range-like rather than trending, can a price excursion beyond the established range be classified **before the outcome** as:

- a temporary overshoot / failed breakout that re-enters the range;
- a genuine breakout that establishes a new same-scale state?

This is not “sell resistance / buy support” by visual judgment. Range and boundary must be mechanical and causal.

## Coordinate definition

- **parent scale:** last two completed parent waves before the excursion;
- **parent state:** low net drift, meaningful overlap, and contained path relative to the two-wave envelope;
- **deviation object:** excursion outside the causal parent range envelope;
- **candidate mean:** the parent range / center region, not a fixed moving average;
- **recovery:** re-entry into the old range before sufficient continuation establishes a new state.

## Range measurements

Stage 1 keeps the range definition low-capacity:

1. `absolute_drift_ratio` across the last two completed parent waves;
2. `overlap_ratio` of the two wave intervals;
3. parent range width;
4. range age / number of completed oscillations as descriptive only;
5. short-to-parent volatility ratio.

Do not search many support/resistance construction methods in the first pass.

## Breakout-event measurements

For the first completed lower-scale move outside the parent envelope, report:

- outside distance / parent range width;
- breakout-wave size / pre-event volatility;
- breakout-wave path efficiency;
- breakout speed;
- volatility expansion relative to the parent range state.

These are measurements, not independently optimized trading filters.

## Primary outcome logic

After a causally detected excursion:

- **reversion boundary:** price re-enters the prior parent range through the breached edge;
- **continuation boundary:** price extends sufficiently to confirm a new same-direction parent-scale wave / state transition under the same causal wave rule;
- if neither boundary occurs within the predeclared horizon, the event is censored.

Primary outcome:

`range_reentry_first` vs `new_state_continuation_first`.

Time to reentry/continuation is mandatory reporting.

## Stage-1 hypotheses

H1. Stronger pre-event range character (lower drift, higher overlap) should increase reentry probability after a boundary excursion.

H2. Excursions accompanied by a large change in path efficiency / volatility structure should be less likely to re-enter than equally large excursions without such state change.

H3. Parent-range information should add beyond breakout size alone.

## Minimal comparisons

Only three first-pass comparisons are authorized:

1. **excursion-size baseline**;
2. **parent-range-state only**;
3. **parent-range-state + excursion-state-change measures**.

No named chart-pattern zoo and no search across many support/resistance algorithms in this identity.

## What would count as promising

R2 is progression-worthy if:

- a mechanical causal range definition yields sufficient events;
- reentry and continuation have materially different pre-outcome state measurements;
- parent-range conditioning adds beyond outside distance alone;
- effect direction is stable in more than one period or scale pairing;
- a low-capacity rule is enough to expose the separation.

## What would close or downgrade R2

- “range” labels are too unstable to reproduce causally;
- almost all apparent alpha comes from one optimized boundary definition;
- breakout size alone explains the effect and range state adds nothing;
- reentry/continuation distinction is not stable across periods/scales;
- event overlap or censoring makes the effective sample trivial.

## Data needed

Minimum:

- clean OHLC bars and exact session timestamps;
- enough history to form completed parent waves and lower-scale excursions;
- no fundamentals, cross-asset data, or execution data needed for Stage 1.

Broad liquid indices are preferred for first-pass mechanism screening.

## Explicit non-goals

- no optimized breakout threshold;
- no support/resistance visual labels;
- no transaction-cost/PnL optimization;
- no deep classifier;
- no attempt to rescue failed breakouts with many filters.

The first-round question is simply whether **a causal parent-range state contains information about reentry versus true state transition**.
