# OFP-C3 Previous China Session Shape — preanalysis

Date: 2026-09-12

## Research identity

`overnight_previous_session_last_hour_conditioned_open_state_v1`

Product family:

`OFP-C3_previous_china_session_shape_x_OFP-A2_observed_open_geometry`

## Question

Does the previous mainland session's final-hour return change the short-horizon meaning of the same normalized CSI1000 opening gap, after controlling for the already validated C1 trend-conditioned opening interaction and simpler causal parents?

## Result-free representation

Use one continuous, low-capacity coordinate only:

- `observed_gap_rvol = gap / rvol20`
- `last_hour_rvol = prev_last_hour / rvol20`
- `last_hour_gap_interaction = last_hour_rvol * observed_gap_rvol`

The final-hour coordinate is selected before outcome inspection because it is the most recent completed mainland-session return available before the overnight interval. This identity does not search `prev_afternoon`, alternative session windows, buckets, thresholds, or combinations after seeing results.

## Evidence boundary

Detailed development material is limited to `2015-01-05..2020-12-31`, using the parity-validated connector-readable carrier under `data/runtime_text_2015_2025/`.

2021-2025 detailed rows remain reusable BLACKBOX-governed and are not opened by this identity. 2026+ outcomes are not used.

## Targets

Pre-register three short horizons from the same 09:35 reference clock:

- 09:35 -> 09:50
- 09:35 -> 10:05
- 09:35 -> 10:35

No full-day or 15:00 target is admitted.

## Baseline

For each target, baseline controls are:

- `observed_gap_rvol`
- `last_hour_rvol`
- `prev_daytime`
- `trend20_rvol = r20 / (sqrt(20) * rvol20)`
- validated C1 `trend_gap_interaction = observed_gap_rvol * trend20_rvol`
- `log_rvol20 = log(rvol20)`
- `r1`
- `holiday_reopen`

Candidate adds only `last_hour_gap_interaction`.

C2's unvalidated 60m interaction is not imported as a control or design input.

## Diagnostics

For pooled 2015-2020 and each natural year 2015..2020:

- partial correlation of candidate interaction with the target after residualizing the baseline;
- baseline and candidate R2, plus delta R2;
- standardized interaction coefficient;
- complete-case count.

## Stability review

No automatic product promotion. A horizon may be retained as progression material only if, before any later BLACKBOX is considered:

- pooled partial correlation and pooled standardized coefficient have the same sign;
- at least 4 of 6 annual standardized coefficients share the pooled sign;
- the median annual standardized coefficient shares the pooled sign;
- pooled delta R2 is positive;
- at least 4 of 6 annual delta R2 values are positive.

Passing these development rules grants only progression material, not validation or production authority. A later reusable BLACKBOX requires a separately frozen successor identity and protocol.

## Prohibitions

No threshold search, no high/low session-shape buckets, no alternate final-hour clock, no `prev_afternoon` rescue, no alternate horizon search, no PnL optimization, no strategy costs/sizing, no 2021-2025 detailed inspection, and no production authority.
