# OFP-B1 global-risk driver v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_global_risk_driver_v1`

Product family: `OFP-B1_global_risk_driver`

## Question

Does the already-causal U.S. overnight global-risk channel carry incremental information about the normalized CSI1000 opening gap beyond simpler domestic pre-open context?

This identity is independently motivated by the factor-product shelf. It does not use hidden behavior from any reusable BLACKBOX query and does not use downstream E1/E2/E3 outcomes as design input.

## Frozen coordinate

Reuse the already result-free normalization introduced before B4 outcomes:

- `nasdaq_risk_z = us_nasdaq / RMS60_prev(us_nasdaq)`
- `vix_risk_z = -us_vix_chg / RMS60_prev(us_vix_chg)`
- `global_risk_z = 0.5 * (nasdaq_risk_z + vix_risk_z)`

where `RMS60_prev(x) = sqrt(mean(x^2))` over the prior 60 China trading days, current observation excluded with `shift(1)`, minimum 20 observations.

Positive `global_risk_z` means global risk-on; negative means global risk-off.

No alternate weighting, lookback, clipping, winsorization, threshold or nonlinear transform may be searched under this identity.

## Target

`opening_gap_rvol = gap / rvol20`

This is the observed CSI1000 opening gap normalized by the causal 20-day close-to-close volatility scale.

## Baseline

The simpler parent contains only domestic causal context:

- `r1`
- `r20`
- `abs_r1`
- `prev_gap`
- `overnight_trend_5`
- `prev_daytime`
- `prev_last_hour`
- `prev_afternoon`
- `log_rvol20`
- `weekend`
- `holiday_reopen`

Candidate adds exactly `global_risk_z`.

A50 and FX channels are deliberately excluded from the B1 parent because they belong to separate B2/B3 product identities. B4 coherence is also excluded.

## Directional hypothesis

Because the coordinate is signed risk-on, the preregistered expected incremental direction is positive:

- pooled partial correlation > 0;
- pooled standardized candidate coefficient > 0.

## Evidence boundary

Development only: `2015-01-05..2020-12-31`.

Report pooled and separately for 2015, 2016, 2017, 2018, 2019, 2020.

2021–2025 is not opened by this identity. A reusable validation successor, if justified, must be frozen separately after Development adjudication. Reuse of that period would not constitute independent OOS.

## Diagnostics

For pooled and each natural year:

- complete-case count;
- partial correlation candidate vs target after residualizing the frozen baseline;
- baseline R²;
- candidate R²;
- delta R²;
- standardized `global_risk_z` coefficient.

## Sufficiency and progression

Sufficiency:

- pooled complete cases >= 900;
- each natural year complete cases >= 150.

Progression requires all of:

1. pooled partial correlation > 0;
2. pooled standardized candidate coefficient > 0;
3. at least 4 of 6 annual standardized coefficients > 0;
4. median annual standardized coefficient > 0;
5. pooled delta R² > 0;
6. at least 4 of 6 annual delta R² > 0.

Passing only creates Development progression material. It does not auto-promote a product or authorize strategy use. Failure closes v1 without threshold, weight, lookback, target, channel-combination or nonlinear rescue.

`production_authority=false`.
