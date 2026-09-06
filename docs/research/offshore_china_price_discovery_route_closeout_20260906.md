# Offshore-China price-discovery successor route closeout — 2026-09-06

## Final decision

Research identity: `offshore_china_price_discovery_successor_v1`.

Final decision: **close this route and retain the incumbent `median_quantile_sign` direction head**.

No offshore-China successor passed the preregistered development gates. Do not open the 2026 repeat blackbox for this route. `2026-01-05..2026-08-21` remains sealed for this identity and post-2026-08-21 remains unread true-fresh evidence.

This closeout does not revoke the OHR-06 mechanism finding. It separates two claims:

1. `broad_china_specific_vs_spy` contains a stable development-era China-specific state signal in the preregistered unresolved slice;
2. the tested low-capacity ways of using that signal do **not** qualify as a high-open-recall successor.

The first claim is supported. The second failed.

## Evidence chain

### OHR-05 — source admission

The single accepted source is the exact Yahoo chart-v8 development artifact:

`data/offshore_etf_dev_2015_2025/offshore_etf_daily.parquet`

SHA256:

`045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd`

The source covers ASHS / ASHR / FXI / MCHI / SPY from 2015-01-02 through 2025-12-31 and contains no 2026 rows.

### OHR-06 — mechanism diagnostic

Cloud run `34025772456` passed source identity, package validation and tests. OHR-06 used 2,424 common offshore-valid OOF rows and a preregistered primary slice of 815 rows:

`incumbent predicts low` AND `prev_last_hour < 0`.

Only one preregistered China-specific representation passed every mechanism gate:

`broad_china_specific_vs_spy = 0.5*(FXI_post_cn + MCHI_post_cn) - SPY_post_cn`.

On the primary slice:

- pooled actual-up minus actual-down mean: about +15.5 bp;
- standardized mean difference: about +0.222;
- positive annual differences: 8/10 years;
- median annual difference: about +12.4 bp;
- Q1 actual-high-open share: about 20.1%;
- Q4 actual-high-open share: about 28.9%.

Interpretation: completed-US-session broad-China repricing relative to the US market contains genuine information about rebound versus continuation after a weak Chinese tail. It did **not** support a CSI1000-small-cap relative-pricing story: `ashs_minus_ashr` and A-share-consensus-minus-SPY failed.

### OHR-07 — one-feature joint refit

Candidate:

`broad_china_specific_tail_weak = broad_china_specific_vs_spy * 1(prev_last_hour < 0)`

added as a 14th feature to the incumbent Median pipeline.

Cloud run `34026047565`; 24 tests passed; 2026 remained sealed.

The candidate slightly improved pooled high-open recall but failed hit, balanced-accuracy, material >30bp recall and 6/10-year robustness gates. Jointly refitting all 14 coefficients also changed predictions outside the state where the new feature was nonzero, revealing coefficient-refit spillover.

OHR-07 was rejected.

### OHR-08 — final frozen-base one-parameter overlay

To isolate the new information from coefficient-refit spillover, OHR-08 froze the exact incumbent in each expanding OOF fold and fitted exactly one no-intercept median-regression coefficient `beta` on the residual using the same gated offshore state.

Candidate score:

`incumbent_score + beta * broad_china_specific_vs_spy * 1(prev_last_hour < 0)`.

No beta grid, intercept, standardization, clipping, sign constraint, alternative quantile, threshold, ticker, representation or trading-return search was allowed.

Cloud run `34026483074`:

- exact offshore SHA passed;
- package validator passed;
- pytest: 28 passed;
- Stage-1 exact-incumbent replay max absolute score difference: `2.168404344971009e-18`;
- outside `prev_last_hour < 0`, candidate versus incumbent score max absolute difference: exactly `0.0`;
- 2026 rows loaded: false;
- 2026 blackbox opened: false.

Therefore the OHR-08 result is a clean test of the one-dimensional offshore overlay rather than a refit artifact.

Common 2,424-row OOF metrics:

| metric | incumbent | OHR-08 | delta |
|---|---:|---:|---:|
| direction hit | 0.717822 | 0.720297 | +0.002475 |
| balanced accuracy | 0.701275 | 0.703493 | +0.002218 |
| recall_up | 0.626723 | 0.627784 | +0.001060 |
| recall_down | 0.775827 | 0.779203 | +0.003376 |
| >10bp high-open recall | 0.660033 | 0.658375 | -0.001658 |
| >30bp high-open recall | 0.711921 | 0.705298 | -0.006623 |
| correct count | 1740 | 1746 | +6 |

The overlay improved pooled hit and balanced accuracy, but it failed the frozen high-open-successor objective:

- >10bp high-open recall declined;
- >30bp high-open recall declined;
- recall_up strictly improved in only 2/10 OOF years;
- the frozen gate required at least 6/10 years.

Prediction-flip morphology shows why pooled accuracy improved:

- incumbent-down -> overlay-up: 5;
- rescued actual highs: 3;
- new false highs: 2;
- incumbent-up -> overlay-down: 9;
- lost actual highs: 2;
- repaired false highs: 7.

The net accuracy gain came mainly from **removing false high calls**, not from robustly repairing missed high opens. This is useful information, but it is not the stated successor objective.

The fitted fold betas also show that the effect is not a strong threshold-crossing direction channel. Betas were negative in 2016 and 2022, zero in 2021, and positive in the other seven folds; despite predominantly positive later betas, high-open recall improved strictly in only two years.

## Scientific conclusion

The development evidence supports this narrower statement:

> When the Chinese session ends weak, broad China ETFs trading in the completed US session contain China-specific information beyond SPY about next-open state. However, that information is too weak and/or too continuous to serve as a robust high-open false-negative repair rule under the current Median direction objective.

The signal appears more useful for **reallocating confidence / reducing some false-high calls** than for a stable high-open-recall successor. That alternative objective was not preregistered for this identity and must not be adopted post hoc to rescue the candidate.

Accordingly:

- `median_quantile_sign` remains the direction incumbent;
- `broad_china_specific_vs_spy` is retained only as documented progression/mechanism material;
- no OHR-03 / 2026 repeat-blackbox is opened for this route;
- no threshold, beta, ticker, interaction or utility retuning is allowed on the consumed 2015-2025 evidence under this identity;
- any future use of the offshore signal for confidence, abstention, probability calibration or false-positive control requires a **new preregistered research objective and identity**;
- post-2026-08-21 remains unread true-fresh evidence;
- production authority remains false.

## Current incumbent state

Direction: `median_quantile_sign`.

Magnitude: existing accepted `abs_frozen_clock_signed_prediction` component.

The incumbent research architecture remains component-wise fresh confirmed from prior cycles; no new integrated successor was admitted by the high-open or offshore-China branches.
