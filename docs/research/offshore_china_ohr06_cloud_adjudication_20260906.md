# OHR-06 cloud adjudication — 2026-09-06

## Decision

OHR-06 is accepted as a valid development-only mechanism diagnostic.

Decision: `mechanism_supported_freeze_one_bounded_candidate`.

The only preregistered **China-specific** representation that passed every mechanism gate is:

`broad_china_specific_vs_spy = 0.5 * (FXI_post_cn + MCHI_post_cn) - SPY_post_cn`

This authorizes one later bounded development candidate. It does **not** authorize 2026, production, trading-return optimization, threshold search, or a broad new feature search.

## Execution integrity

Cloud run: `34025772456`.

- exact OHR-05 Yahoo source located at `data/offshore_etf_dev_2015_2025/offshore_etf_daily.parquet`;
- SHA256: `045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd`;
- package validator: passed (`ok 3 research_architecture_accepted production_authority=false`);
- pytest: 21 passed;
- frozen OHR-06 diagnostic: passed;
- aggregate receipt / usage were committed by the cloud runner;
- `2026_rows_loaded=false`, `2026_blackbox_opened=false`, `ohr_03_opened=false`;
- no parameter / quantile / threshold search and no candidate selection occurred in OHR-06.

OOF inventory:

- incumbent OOF rows: 2,426;
- common offshore-valid OOF rows: 2,424;
- two rows excluded because a required ASHS US session had zero volume;
- primary unresolved slice (`incumbent predicts low` AND `prev_last_hour < 0`): 815 rows;
- actual-high-open share in that slice: 23.93%.

## Mechanism evidence

### Raw offshore China/A-share states

Several raw states were strong on the primary slice:

- `ashr_session`: positive in 10/10 years, standardized pooled difference about +0.619, Q1 actual-high-open share 9.80% versus Q4 43.14%;
- `ashs_session`: positive in 10/10 years, standardized pooled difference about +0.391, Q1 15.69% versus Q4 37.75%;
- `a_share_consensus`: positive in 10/10 years, standardized pooled difference about +0.545, Q1 11.76% versus Q4 38.73%;
- `china_etf_positive_breadth`: positive in 10/10 years, standardized pooled difference about +0.604, Q1 13.73% versus Q4 43.14%.

These are useful corroboration, but they cannot by themselves authorize a family because a US common-market factor may explain much of their movement.

### China-specific controls

`ashs_minus_ashr` failed: pooled actual-up minus actual-down mean was negative, only 3/10 annual differences were positive, and Q4 actual-high-open share was below Q1. Therefore there is no evidence that US trading specifically reprices smaller A-shares more positively than large A-shares before the unresolved CSI1000 high opens.

`a_share_specific_vs_spy` failed even more clearly: pooled difference was negative, only 1/10 years was positive, and Q4 actual-high-open share was below Q1. This rejects the simple story that A-share ETF excess performance over the US market is the missing signal.

`broad_china_specific_vs_spy` passed all gates:

- pooled actual-up minus actual-down mean: `+0.0015520` (~+15.5 bp);
- standardized pooled mean difference: `+0.2224`;
- positive annual differences: 8/10 years;
- median annual mean difference: `+0.0012422` (~+12.4 bp);
- Q1 actual-high-open share: `20.10%`;
- Q4 actual-high-open share: `28.92%`.

The effect is materially smaller than raw ASHR/consensus/breadth, but it survives the SPY common-factor control and is therefore the only representation with preregistered authority to enter a successor family.

## Financial interpretation

The surviving signal is not a CSI1000-small-cap relative price-discovery effect. It is better described as **broad China risk repricing relative to the US market during completed US regular sessions after the prior China close**.

When the prior Chinese session ends weak, a comparatively stronger FXI/MCHI session versus SPY is consistent with overseas investors revising China-specific risk upward before the next Chinese open. That state raises the probability that an incumbent low-open call is actually followed by a high open.

The small OHR-04 disagreement set does not show a positive rescue-minus-false-high difference for this representation. That 38-flip sample was preregistered as supporting evidence only and is too small to overturn the 815-row / 10-year primary-slice mechanism result. It does, however, argue against a hand-written threshold rule.

## Next mathematical form

Only one low-capacity candidate is admitted:

`broad_china_specific_tail_weak = broad_china_specific_vs_spy * 1(prev_last_hour < 0)`

The zero threshold on `prev_last_hour` is not tuned; it is the exact financial state used in the OHR-06 preregistered primary slice. The feature is zero outside that state.

The incumbent estimator, quantile, alpha, decision threshold and original 13 features remain unchanged. This creates exactly one additional piecewise slope: the Median head may respond to broad China-specific offshore repricing only after a weak prior last hour.

Raw ASHS, ASHR, A-share consensus, ETF breadth, `ashs_minus_ashr`, and `a_share_specific_vs_spy` are not admitted as candidate inputs. No alternative ticker, weight, sign threshold, nonlinear transform or interaction may be added after seeing the OHR-06 result.

## Evidence boundary

Development selection remains 2016-2025 expanding natural-year OOF using 2015-2025 material.

`2026-01-05..2026-08-21` remains sealed repeat-blackbox material and cannot participate in development. Post-2026-08-21 remains unread true-fresh evidence.

If the single bounded candidate fails the already-established non-sacrifice gates, retain `median_quantile_sign` and close this offshore source route without opening 2026.
