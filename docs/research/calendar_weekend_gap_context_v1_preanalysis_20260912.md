# OFP-C4 weekend-closure gap context v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_weekend_gap_conditioned_open_state_15m_v1`

Product family: `OFP-C4_calendar_closure_context_x_OFP-A2_observed_open_geometry`

## Question

Does an ordinary weekend closure change the immediate 15-minute post-open meaning of the same normalized CSI1000 opening gap after controlling simpler causal parents and the already validated C1 trend-conditioned coordinate?

This identity is independently motivated by the pre-existing C4 calendar-closure shelf. It is not a rescue of E1/E2/E3, C3, D1 or B3 and does not use hidden reusable-BLACKBOX behavior.

## Frozen coordinate

- `observed_gap_rvol = gap / rvol20`
- `weekend_gap_interaction = weekend * observed_gap_rvol`

`weekend` is the already-materialized causal calendar flag in the frozen CSI1000 factor panel. No alternate weekday coding, closure-length reconstruction, holiday merge, threshold or calendar search is allowed.

## Target

Exactly one target is preregistered:

`ret_0935_0950 = close_0950 / close_0935 - 1`

The 15-minute horizon is chosen before outcomes because regular weekend-closure information should be absorbed, if relevant, in the immediate post-open interval. No 30m/60m horizon search is allowed under v1.

## Baseline controls

- `observed_gap_rvol`
- `weekend`
- `holiday_reopen`
- `trend20_rvol = r20 / (sqrt(20) * rvol20)`
- validated C1 `trend_gap_interaction = observed_gap_rvol * trend20_rvol`
- `log_rvol20 = log(rvol20)`
- `r1`
- `prev_daytime`

C2's validated 60-minute interaction is not imported because this identity has a 15-minute target. B1/B2/B4 driver coordinates are also not imported; this is a calendar-context mechanism diagnostic, not a multi-factor strategy.

## Direction

No ex-ante sign is imposed. The Development question is whether a single continuous interaction has a stable nonzero sign. Any successor validation, if justified, must freeze the pooled Development sign before opening 2021–2025.

## Evidence boundary

Development only: `2015-01-05..2020-12-31`.

Report pooled plus 2015, 2016, 2017, 2018, 2019, 2020 separately.

2021–2025 remains unopened until a separately frozen compact successor protocol.

## Sufficiency

Each calendar year must have:

- at least 150 complete cases overall;
- at least 30 complete weekend-flagged observations.

## Diagnostics

For pooled and each natural year:

- complete-case count;
- weekend complete-case count;
- partial correlation of `weekend_gap_interaction` with target after residualizing the baseline;
- baseline/candidate R² and delta R²;
- standardized interaction coefficient.

## Progression

Progression requires all of:

1. pooled partial correlation and pooled standardized coefficient are finite, nonzero and have the same sign;
2. at least 4 of 6 annual standardized coefficients share the pooled coefficient sign;
3. median annual standardized coefficient shares the pooled coefficient sign;
4. pooled delta R² > 0;
5. at least 4 of 6 annual delta R² > 0.

Passing creates Development progression material only. No auto-promotion, threshold, bucket, weekday search, holiday substitution or strategy authority follows.

`production_authority=false`.
