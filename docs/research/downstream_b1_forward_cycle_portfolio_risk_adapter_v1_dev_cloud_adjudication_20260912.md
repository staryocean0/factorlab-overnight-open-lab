# OFP-E3 v2 B1 forward-cycle portfolio-risk abstention — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_b1_forward_cycle_portfolio_risk_abstention_v1`

Phase: retrospective account-overlay utility/risk diagnostic only.

Development window: `2015-01-05..2020-12-31`.

## Frozen identity

Consumer is pinned to `staryocean0/factorlab-multifactor-stock-lab@af2e478aaff5c8ef7f753424b57fd2d19019f248`, strategy `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`, model `d8-h8-K1-r0_fit_prefix_successor_incumbent`, account policy `N30_equal_backfill_unconstrained`, with 14:30 and 14:45 evaluated jointly.

Validated B1 coordinate is reused exactly:

`global_risk_z = 0.5 * (nasdaq_risk_z + vix_risk_z)`

with the frozen lagged 60-China-trading-day RMS normalization and current observation excluded.

Comparator exposure is always 1. Candidate exposure is 1 iff `global_risk_z >= 0`, otherwise 0. Zero is the only boundary.

For each frozen consumer rebalance/decision date `t`, the target is the compounded account return over the five trading days strictly after `t`. The decision-day return is excluded. Decisions that cannot obtain all five future returns inside 2015–2020 are incomplete; no 2021 row is used to complete late-2020 targets.

No account path is rerun or mutated. No costs, fills, threshold search, B1 magnitude buckets, alternate target length, clock selection, consumer-policy mutation or extra upstream products are introduced.

## Development results

Both frozen consumer clocks pass every preregistered sufficiency and progression gate.

### 14:30

- pooled complete decisions: **288**;
- pooled active decisions: **165**;
- active coverage: **0.572917**;
- comparator mean utility: **+0.0003180622**;
- candidate mean utility: **+0.0033630208**;
- pooled mean-utility delta: **+0.0030449586**;
- comparator downside mean: **-0.0179661076**;
- candidate downside mean: **-0.0087170576**;
- pooled downside-mean delta: **+0.0092490501**;
- annual mean-utility delta positive in **5 / 6** years;
- median annual mean-utility delta: **+0.0026851463**;
- annual downside-mean delta nonnegative in **6 / 6** years.

Annual mean-utility deltas:

- 2015: `+0.0040888920`
- 2016: `+0.0005066695`
- 2017: `+0.0059756797`
- 2018: `+0.0068618224`
- 2019: `-0.0003175895`
- 2020: `+0.0012814006`

### 14:45

- pooled complete decisions: **288**;
- pooled active decisions: **165**;
- active coverage: **0.572917**;
- comparator mean utility: **+0.0003127092**;
- candidate mean utility: **+0.0033469525**;
- pooled mean-utility delta: **+0.0030342433**;
- comparator downside mean: **-0.0178191239**;
- candidate downside mean: **-0.0085917527**;
- pooled downside-mean delta: **+0.0092273713**;
- annual mean-utility delta positive in **5 / 6** years;
- median annual mean-utility delta: **+0.0024562505**;
- annual downside-mean delta nonnegative in **6 / 6** years.

Annual mean-utility deltas:

- 2015: `+0.0039320988`
- 2016: `+0.0006086546`
- 2017: `+0.0059999993`
- 2018: `+0.0069983045`
- 2019: `-0.0002017211`
- 2020: `+0.0009804021`

The single negative annual mean-utility delta is 2019 for both clocks; this is retained rather than optimized away. Downside mean improves in every year for both clocks.

## Decision

**`E3V2_DEV_PROGRESS_RETROSPECTIVE_PORTFOLIO_RISK_ADAPTER_CANDIDATE`**

This grants only retrospective E3 portfolio-risk adapter progression material. It does not establish executable account performance because the candidate is an analytical whole-portfolio exposure overlay on an immutable account return path, not a replay with frozen sell/re-entry fills and costs.

A reusable 2021–2025 validation may be opened only under a separately frozen compact identity/protocol. Reuse of that physical period is not independent OOS.

`production_authority=false`.
