# OFP-E3 v2 B1 forward-cycle portfolio-risk abstention — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_b1_forward_cycle_portfolio_risk_abstention_v1`

## Motivation

B1 `global_risk_z` is a validated pre-open continuous global-risk coordinate (reusable BLACKBOX query `6b0b6899f94fd8353a34`). This identity asks a separate downstream question: can that already-validated market-level risk coordinate improve the next consumer decision-cycle utility/risk of a frozen long-only REAKA portfolio by scaling the whole portfolio to zero in risk-off states?

This identity is independent of the earlier C1 intraday E3 identity, which closed as evidence-insufficient. It does not relax exact intraday-clock rules, reuse incomplete intraday targets, or use hidden E3-v1 behavior. It uses the frozen account daily-return ledger directly and a new, causally later target.

## Frozen consumer

Repository: `staryocean0/factorlab-multifactor-stock-lab`

Pinned commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`

Strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`

Model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`

Account policy: `N30_equal_backfill_unconstrained`

Variants: `14:30` and `14:45`, evaluated jointly.

Frozen account snapshot daily carrier:

`output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/account_snapshot/portfolio_daily.parquet`

Scientific SHA256: `8f6be84836d7839642e3cf722639887be339fa3f660c274b16d7c0a2b56ae1a5`.

Only replay segment `2011_2020` and dates `2015-01-05..2020-12-31` may be materialized for Development.

## Frozen upstream signal

B1 normalization is reused exactly:

`nasdaq_risk_z = us_nasdaq / sqrt(mean(prev 60 trading-day us_nasdaq^2, min 20, current excluded))`

`vix_risk_z = -us_vix_chg / sqrt(mean(prev 60 trading-day us_vix_chg^2, min 20, current excluded))`

`global_risk_z = 0.5 * (nasdaq_risk_z + vix_risk_z)`

B1 validated sign is positive.

Candidate exposure:

`candidate_exposure = 1 if global_risk_z >= 0 else 0`

Comparator exposure:

`comparator_exposure = 1`

Zero is the only boundary. No nonzero threshold or magnitude bucket is searched.

## Frozen target and timing

The consumer is a D5 decision process. For each frozen rebalance/decision date `t`, define:

`forward_5_account_return = product(1 + daily_return[t+1:t+5]) - 1`

The decision-day return itself is excluded because B1 is available pre-open but this research does not model a same-day 14:30/14:45 liquidation fill. The five subsequent trading days form the next frozen decision-cycle utility surface.

A decision is complete only if five subsequent daily returns exist inside the admitted 2015–2020 development surface. Late-2020 decisions lacking five future development days are incomplete; no 2021 row may be used to complete them.

Comparator utility: `forward_5_account_return`.

Candidate utility: `candidate_exposure * forward_5_account_return`.

Portfolio downside utility: `min(utility, 0)`; higher (less negative) is better.

This is a retrospective account-overlay utility/risk diagnostic, not an executable re-simulation. No fills, transaction costs, cash-transfer mechanics or account mutation are claimed.

## Development and gates

Development: `2015-01-05..2020-12-31`, reported by decision year 2015..2020 and pooled, separately for 14:30 and 14:45.

Sufficiency per clock-year:

- at least 20 complete decisions;
- at least 8 active candidate decisions.

Progression per clock requires all:

- pooled mean utility delta > 0;
- at least 4 of 6 annual mean-utility deltas > 0;
- median annual mean-utility delta >= 0;
- pooled downside-mean delta >= 0;
- at least 4 of 6 annual downside-mean deltas >= 0.

Both clocks must pass. No post-result clock selection is allowed.

Passing grants only `retrospective_E3_portfolio_risk_adapter_candidate_only`. Reusable validation requires a separate compact protocol; 2021–2025 reuse is not independent OOS.

## Forbidden post-result actions

No B1 threshold search, magnitude buckets, alternate NASDAQ/VIX weights, alternate RMS window, alternate target length, same-day-return inclusion, consumer clock selection, consumer policy mutation, extra upstream factor, cost/fill optimization, or hidden-BLACKBOX rescue.

`production_authority=false`.
