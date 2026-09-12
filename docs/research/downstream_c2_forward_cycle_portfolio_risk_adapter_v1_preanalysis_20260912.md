# OFP-E3 v3 C2 forward-cycle portfolio-risk abstention — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_c2_forward_cycle_portfolio_risk_abstention_v1`

## Independent motivation

C2 `vol_gap_interaction` is a separately validated prior-volatility/open-geometry risk coordinate (reusable BLACKBOX query `a1068de9321c04632aad`). Its product-level consumer role includes portfolio risk. This identity therefore asks a direct downstream question that is independent of the result of the earlier B1 portfolio-risk adapter: does the validated C2 risk direction improve the next frozen consumer decision-cycle utility/risk when it is allowed only to set whole-portfolio exposure to zero?

No hidden behavior from E3 v2 query 12 is used. The signal family, scientific mechanism and upstream authority are different from B1. This is not a threshold, target or clock rescue of E3 v2.

## Frozen consumer

Repository: `staryocean0/factorlab-multifactor-stock-lab`

Pinned commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`

Strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`

Model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`

Account policy: `N30_equal_backfill_unconstrained`

Consumer variants: 14:30 and 14:45, evaluated jointly with no post-result clock selection.

Frozen daily account carrier:

`output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/account_snapshot/portfolio_daily.parquet`

Scientific SHA256: `8f6be84836d7839642e3cf722639887be339fa3f660c274b16d7c0a2b56ae1a5`.

Development admits only replay segment `2011_2020` and dates `2015-01-05..2020-12-31`.

## Frozen upstream signal

Validated C2 coordinate:

`observed_gap_rvol = gap / rvol20`

`vol_gap_interaction = observed_gap_rvol * log(rvol20)`

C2 validated scientific direction is negative, so the downstream risk-on score is fixed as:

`c2_risk_on_score = -vol_gap_interaction`

Comparator exposure:

`comparator_exposure = 1`

Candidate exposure:

`candidate_exposure = 1 if c2_risk_on_score >= 0 else 0`

Zero is the only boundary. There are no fitted weights, magnitude thresholds, volatility buckets or alternate C2 transformations.

## Frozen target and timing

For each frozen consumer rebalance/decision date `t`:

`forward_5_account_return = product(1 + daily_return[t+1:t+5]) - 1`

The decision-day account return is excluded. The five subsequent trading days form the next frozen D5 decision-cycle utility surface and avoid claiming an executable same-day liquidation at 14:30/14:45.

A decision is complete only when five subsequent account daily returns exist inside the admitted 2015–2020 Development surface. No 2021 row may complete a late-2020 target.

Comparator utility: `forward_5_account_return`.

Candidate utility: `candidate_exposure * forward_5_account_return`.

Downside utility: `min(utility, 0)`, where higher / less negative is better.

This phase is an analytical whole-portfolio overlay on an immutable account-return path. It does not rerun account fills, costs, holdings or cash transfers.

## Development evidence and gates

Development window: `2015-01-05..2020-12-31`; report pooled and by decision year 2015..2020 for both 14:30 and 14:45.

Sufficiency per clock-year:

- at least 20 complete decisions;
- at least 8 candidate-active decisions.

Progression per clock requires all:

- pooled mean-utility delta > 0;
- at least 4 of 6 annual mean-utility deltas > 0;
- median annual mean-utility delta >= 0;
- pooled downside-mean delta >= 0;
- at least 4 of 6 annual downside-mean deltas >= 0.

Both consumer clocks must pass every gate. No post-result winner clock may be selected.

Passing grants only `retrospective_E3_portfolio_risk_adapter_candidate_only`. Reusable validation requires a separately frozen compact identity/protocol. Reuse of 2021–2025 is not independent OOS.

## Forbidden post-result actions

Do not search a nonzero C2 threshold, C2 magnitude/volatility buckets, alternate sign conventions, alternate C2 horizon, alternate target length, decision-day inclusion, consumer clock selection, consumer account/model/policy mutation, extra upstream products, costs/fills, or hidden-BLACKBOX rescue.

`production_authority=false`.
