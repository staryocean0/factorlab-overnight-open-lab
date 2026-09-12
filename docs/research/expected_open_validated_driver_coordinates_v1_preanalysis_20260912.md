# OFP-A1 expected-open validated-driver coordinate adapter v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_expected_open_validated_driver_coordinates_v1`

Product family: `OFP-A1_expected_open_state`

## Question

Can the already validated continuous B1 global-risk and B2 China-offshore coordinates add predictive value to the frozen V6A signed-gap model without changing its estimator, clocks, target, domestic inputs or source semantics?

This identity is a downstream model adapter over validated upstream products. It does not redefine B1/B2 and does not use hidden BLACKBOX behavior. B3 is not imported because it has no validated product authority. B4 coherence is not imported to keep v1 low-dimensional and avoid a second interaction-like degree of freedom.

## Comparator

Frozen V6A model family:

`StandardScaler + Ridge(alpha=1.0)`

Comparator features are exactly the V6A feature set used by `scripts/run_v6a_reusable_blackbox_local.py`:

- domestic/base: `r1, r20, abs_r1, prev_gap, overnight_trend_5, prev_daytime, prev_last_hour, prev_afternoon, rvol20, weekend, holiday_reopen, us_nasdaq, us_vix_chg`
- closure extras: `us_nasdaq_closure_extra, us_vix_closure_extra, hkma_usdcny_closure_return, a50_holiday_closure_return`
- ordinary A50: `a50_ordinary_preauction_closure_return`

The comparator is refit on exactly the candidate-complete common sample; this prevents missingness differences from being credited to the candidate.

## Candidate

Candidate uses the same estimator and comparator features plus exactly two already validated continuous coordinates:

- B1 `global_risk_z`
- B2 `china_offshore_z`

Frozen formulas:

- `global_risk_z = 0.5 * (us_nasdaq / RMS60_prev(us_nasdaq) + (-us_vix_chg / RMS60_prev(us_vix_chg)))`
- `china_offshore_z = a50_channel_return / RMS60_prev(a50_channel_return)`

RMS normalization is trailing 60 China trading days, current observation excluded by `shift(1)`, minimum 20 observations. `a50_channel_return` uses the already governed holiday/ordinary same-contract channel selection.

No coefficient, Ridge alpha, lookback, upstream add/drop, interaction, threshold, bucket or clock is searched.

## Target and windows

Target: signed CSI1000 opening gap `gap` exactly as in V6A.

Training: `2015-01-05..2018-12-31`.

Open Development evaluation: `2019-01-01..2020-12-31`.

2019–2020 is retrospective Development material, not fresh OOS. 2021–2025 remains reusable BLACKBOX and is not opened by this parent identity.

## Diagnostics

For pooled 2019–2020 and separately 2019/2020:

- complete common-sample count;
- comparator/candidate SSE;
- comparator/candidate R²;
- comparator/candidate IC;
- comparator/candidate sign accuracy.

## Sufficiency

- training common complete cases >= 800;
- each evaluation year common complete cases >= 200.

## Progression

All must pass:

1. pooled candidate SSE < comparator SSE;
2. pooled candidate R² > comparator R²;
3. pooled candidate IC >= comparator IC;
4. pooled candidate sign accuracy >= comparator sign accuracy - 0.01;
5. candidate SSE lower in both 2019 and 2020;
6. candidate IC >= comparator IC in at least one of two evaluation years;
7. candidate sign accuracy >= comparator sign accuracy - 0.02 in both evaluation years.

Passing only creates an A1 Development successor candidate. A reusable validation requires a separately frozen compact identity. Same-period reuse is not independent OOS.

`production_authority=false`.
