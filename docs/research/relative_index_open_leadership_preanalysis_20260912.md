# OFP-D1 Relative-Index Opening Leadership — preanalysis

Date: 2026-09-12

## Research identity

`overnight_relative_size_open_leadership_v1`

Product family:

`OFP-D1_relative_index_open`

## Scientific question

Does the observed opening leadership of CSI1000 versus CSI300 contain stable short-horizon relative-return information after controlling for the common opening component and simple pre-open relative state?

This is a new independent identity. It is not a rescue, descendant, threshold variant, or rename of the closed Gap-Fill V2.1 P2 relative-gap-excess family.

## Frozen continuous representation

For index `i`:

- `gap_i = open_0931_i / previous_close_1500_i - 1`
- `r1_i = previous_close_1500_i / close_1500_two_trading_days_ago_i - 1`
- `rvol20_i = std(daily_close_return_i.shift(1), 20 trading days, min_periods=20)`
- `gap_rvol_i = gap_i / rvol20_i`

The only candidate coordinate is:

`size_open_leadership = gap_rvol_CSI1000 - gap_rvol_CSI300`

Positive values mean CSI1000 opens stronger than CSI300 on its own trailing-volatility scale; negative values mean CSI300 opens stronger.

CSI500 is admitted to the carrier inventory for future independently preregistered work, but it is not part of this v1 candidate, comparator, target, threshold, or rescue path.

## Frozen targets

All targets are relative returns from the same 09:35 reference clock:

- `relative_ret_0935_0950 = ret_CSI1000_0935_0950 - ret_CSI300_0935_0950`
- `relative_ret_0935_1005 = ret_CSI1000_0935_1005 - ret_CSI300_0935_1005`
- `relative_ret_0935_1035 = ret_CSI1000_0935_1035 - ret_CSI300_0935_1035`

No Gap-Fill target, high-gap subset, EOD target, or strategy return is admitted.

## Frozen baseline

For each target, baseline controls are exactly:

- `common_open_component = 0.5 * (gap_rvol_CSI1000 + gap_rvol_CSI300)`
- `relative_r1 = r1_CSI1000 - r1_CSI300`
- `relative_log_rvol = log(rvol20_CSI1000) - log(rvol20_CSI300)`

Candidate adds only `size_open_leadership`.

This baseline deliberately contains the simpler parents of the candidate so D1 receives incremental credit only for the cross-index opening spread itself.

## Evidence boundary

Detailed development material is limited to `2015-01-05..2020-12-31` from the newly admitted common three-index 1m source. The carrier may read earlier CSI1000 rows only as deterministic trailing-volatility warmup beginning `2014-10-17`.

No 2021-2025 row-level text may be generated or inspected for this identity. No reusable BLACKBOX is authorized at this phase. No 2026 outcome is used.

## Diagnostics

For pooled 2015-2020 and each natural year 2015..2020, report for each frozen horizon:

- partial correlation of `size_open_leadership` with the relative-return target after residualizing the baseline;
- baseline R2, candidate R2, and delta R2;
- standardized coefficient of `size_open_leadership`;
- complete-case count.

## Progression gate

A horizon may be retained as development progression material only if:

- pooled partial correlation and pooled standardized coefficient have the same sign;
- at least 4 of 6 annual standardized coefficients share the pooled sign;
- the median annual standardized coefficient shares the pooled sign;
- pooled delta R2 is positive;
- at least 4 of 6 annual delta R2 values are positive;
- every annual complete-case count is at least 150.

Passing grants development progression material only. If multiple horizons pass, retain them jointly; do not choose a unique winner post hoc. Any later reusable BLACKBOX requires a separately frozen successor identity and result-free protocol.

## Prohibitions

No CSI500 substitution or rescue, no P2 relative-gap-excess formula, no high-gap threshold, no gap-sign bucket, no quantile bucket, no alternate volatility window, no alternate opening clock, no alternate horizon search, no pairwise index search, no coefficient-sign conditioning, no PnL optimization, no cost/sizing optimization, no 2021-2025 detailed inspection, no auto-promotion, and no production authority.
