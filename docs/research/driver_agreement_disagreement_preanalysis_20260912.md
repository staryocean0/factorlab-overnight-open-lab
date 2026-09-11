# OFP-B4 Driver Agreement / Disagreement — preanalysis

Date: 2026-09-12

## Research identity

`overnight_driver_coherence_v1`

Product family:

`OFP-B4_driver_agreement_disagreement`

## Scientific question

Does a low-capacity measure of agreement among the global-risk, China-specific offshore, and FX overnight channels add information about the normalized CSI1000 opening gap beyond the three channel main effects and already-causal domestic context?

This is a pre-open driver product. It is not an Opening Surprise rescue, not a strategy backtest, and not a decomposition of hidden 2021-2025 V6A BLACKBOX behavior.

## Evidence boundary

Detailed development material is limited to `2015-01-05..2020-12-31`.

Inputs are restricted to the already-admitted connector-readable development carriers:

- `data/runtime_text_2015_2025/factor_panel_2015.csv` through `factor_panel_2020.csv`;
- `data/driver_runtime_text_2015_2020/driver_external_2015.csv` through `driver_external_2020.csv`.

The A50/HKMA text carrier is data engineering only and inherits the frozen V6A source semantics. Its carrier receipt must show A50 clock integrity PASS, HKMA causal timing PASS, no post-2020 rows loaded, and no 2021-2025 text shards generated.

2021-2025 detailed rows remain reusable BLACKBOX-governed and are not opened by this identity. 2026+ outcomes are not used.

## Result-free channel normalization

Every raw channel input is normalized by a causal trailing RMS scale computed on China trading-day rows:

`rms60_prev(x)_t = sqrt(mean(x^2 over up to the previous 60 valid China trading-day observations))`

The current observation is excluded with `shift(1)`. At least 20 prior valid observations are required. No mean subtraction, winsorization, clipping, quantile transform, or outcome-derived scale is allowed.

Signed channel coordinates are frozen as:

- `nasdaq_risk_z = us_nasdaq / rms60_prev(us_nasdaq)`
- `vix_risk_z = -us_vix_chg / rms60_prev(us_vix_chg)`
- `global_risk_z = 0.5 * (nasdaq_risk_z + vix_risk_z)`
- `china_offshore_z = a50_channel_return / rms60_prev(a50_channel_return)`
- `fx_cny_z = -hkma_usdcny_closure_return / rms60_prev(hkma_usdcny_closure_return)`

The minus signs on VIX change and USD/CNY return put all three channel families on the same semantic axis: positive means risk-on / CNY-strength-compatible; negative means risk-off / CNY-weakness-compatible.

## Candidate coordinate

Only one nonlinear candidate is admitted:

`driver_coherence = (global_risk_z + china_offshore_z + fx_cny_z) / (abs(global_risk_z) + abs(china_offshore_z) + abs(fx_cny_z))`

If the denominator is zero or any required channel is unavailable, the candidate is missing for that row.

Interpretation:

- near `+1`: channels coherently point risk-on;
- near `-1`: channels coherently point risk-off;
- near `0`: mixed/opposing channels.

No separate thresholded agreement label is authorized.

## Target

Exactly one target is admitted:

`opening_gap_rvol = gap / rvol20`

No absolute-gap target, high/low-open classifier, post-open horizon, Opening Surprise term, or PnL target is admitted.

## Baseline controls

The candidate is tested incrementally beyond exactly these main effects and causal domestic controls:

- `r1`
- `r20`
- `abs_r1`
- `prev_gap`
- `overnight_trend_5`
- `prev_daytime`
- `prev_last_hour`
- `prev_afternoon`
- `log_rvol20 = log(rvol20)`
- `weekend`
- `holiday_reopen`
- `global_risk_z`
- `china_offshore_z`
- `fx_cny_z`

This tests the nonlinear agreement/disagreement pattern, not whether the three raw channels have main-effect predictive value.

## Diagnostics

For pooled 2015-2020 and each natural year 2015..2020:

- partial correlation of `driver_coherence` with `opening_gap_rvol` after residualizing the baseline;
- baseline R2, candidate R2, and delta R2;
- standardized driver-coherence coefficient;
- complete-case count.

Every annual diagnostic requires at least 150 complete cases. Pooled diagnostic requires at least 900 complete cases. Failure of a count gate is `evidence_insufficient`, not a negative scientific result.

## Development progression rule

No automatic product promotion is granted.

If count sufficiency holds, B4 may be retained as development progression material only when all of the following are true:

- pooled partial correlation and pooled standardized coefficient have the same non-zero sign;
- at least 4 of 6 annual standardized coefficients share the pooled sign;
- the median annual standardized coefficient shares the pooled sign;
- pooled delta R2 is positive;
- at least 4 of 6 annual delta R2 values are positive.

Passing this rule does not validate the product and does not authorize production. Any later reusable BLACKBOX query requires a separately frozen successor identity and result-free protocol.

## Prohibitions

No alternate RMS window, expanding normalization, standard deviation normalization, winsorization, driver weighting search, channel drop/add search, pairwise-only agreement search, thresholds, sign buckets, absolute-gap target rescue, post-open horizon search, strategy return optimization, cost model, position sizing, or downstream adapter tuning.

Do not use C2 or C3 hidden/future validation behavior as B4 design input. Do not inspect or materialize 2021-2025 row-level text. `production_authority=false`.
