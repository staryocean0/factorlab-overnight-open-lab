# Trend-conditioned opening state — cloud adjudication (2026-09-11)

## Identity

`overnight_trend_conditioned_open_state_v1`

Receipt:

`docs/research/local_trend_conditioned_open_state_dev_diagnostic_v1.json`

Local execution commit:

`00279965699e418bc8d7d49662b3cdeebbfe9a0e`

## Execution / boundary review

Cloud review accepts the local execution as procedurally valid:

- the local commit added only the frozen diagnostic receipt;
- the commit message used `[skip ci]`;
- `development_window == 2019-01-01..2020-12-31`;
- `target_rows_after_2020_loaded == false`;
- `reusable_blackbox_2021_2025_opened == false`;
- `candidate_family_search == false`;
- `trend_bucket_search == false`;
- `threshold_search == false`;
- `horizon_search == false`;
- `volatility_bucket_search == false`;
- `trading_return_optimization == false`;
- `opening_surprise_rescue_performed == false`;
- production authority remains false.

The frozen base-panel and minute-bar hashes match the repository manifests, and the protocol identity matches the preregistered C1 continuous interaction experiment.

## Scientific result

Decision:

**`C1_DEV_PROGRESS_15M_CONTINUOUS_COORDINATE_ONLY`**

The continuous interaction

`trend_gap_interaction = trend20_rvol * observed_gap_rvol`

shows real development progression, but only the shortest frozen horizon is directionally stable across the two development years.

At `09:35 -> 09:50`:

- 2019 partial correlation is negative and the standardized interaction coefficient is negative;
- 2020 partial correlation is also negative and the standardized interaction coefficient is also negative;
- pooled partial correlation and pooled standardized coefficient are negative;
- adding the interaction raises in-sample explanatory power in both years and pooled.

At the longer `09:35 -> 10:05` and `09:35 -> 10:35` horizons, the interaction sign reverses between 2019 and 2020. Those horizons therefore do not support one stable general C1 product.

This review does **not** authorize choosing arbitrary best horizons after the fact. Instead it freezes a new, separately named 15-minute successor identity before any 2021-2025 query. The original multi-horizon mechanism diagnostic is closed as development evidence.

## Interpretation boundary

The supported statement is narrow:

> prior trend changes the short-horizon meaning of the observed opening gap, with the only cross-year stable development evidence appearing in the first 15 minutes after the 09:35 reference clock.

Do not infer a six-cell `up/range/down × high/low open` table from this result. The current evidence supports a continuous interaction coordinate, not categorical trend thresholds.

Do not over-interpret the negative interaction coefficient as one universal "mean reversion" rule for every quadrant. It is a conditional slope effect after the baseline main effects are controlled.

## Authority consequences

- retain C1 as valid progression material;
- do not promote the original multi-horizon identity as a finished factor product;
- freeze a separate 15-minute continuous candidate: `overnight_trend_conditioned_open_state_15m_v1`;
- keep `categorical_up_range_down_authority=false`;
- do not search trend thresholds, quantiles, gap thresholds, alternate lookbacks, volatility regimes, or strategy PnL before the 15-minute candidate is independently adjudicated;
- the 2021-2025 reusable BLACKBOX remains unopened for C1 at the time of this adjudication.

## Next step

A separate low-bandwidth reusable-BLACKBOX protocol is now permitted for the fully frozen 15-minute identity. It may release only `PASS / FAIL / INSUFFICIENT` and may not expose year/quarter/event/subgroup details.

`production_authority=false`.
