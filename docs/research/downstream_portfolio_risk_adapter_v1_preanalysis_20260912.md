# OFP-E3 portfolio-risk adapter v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_c1_intraday_portfolio_risk_abstention_v1`

Consumer portfolio is frozen to the immutable current REAKA strategy/account snapshot:

- repository: `staryocean0/factorlab-multifactor-stock-lab`
- source commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`
- strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`
- model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`
- account policy: `N30_equal_backfill_unconstrained`
- decision-clock accounts: 14:30 and 14:45
- account contract: `docs/ops/reaka_current_k1_account_ledgers@1.5.json`
- immutable account snapshot: `output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/account_snapshot/`

This identity is independent of E1 and E2 outcomes. It is motivated by C1's already-validated **15-minute** open-state information horizon and therefore uses exactly the same 09:35→09:50 window. It does not use B4, E1 or E2 behavior as design input.

## Frozen mechanism

Validated C1:

`trend_gap_interaction = observed_gap_rvol * trend20_rvol`

with negative validated direction for `09:35 -> 09:50`.

Define:

`c1_direction_score = -trend_gap_interaction`

`c1_action = sign(c1_direction_score)`

For a long-only frozen consumer portfolio, the result-free risk rule is:

- comparator exposure over 09:35→09:50 = 1;
- candidate exposure = 0 if `c1_action < 0`;
- candidate exposure = 1 if `c1_action >= 0`.

The boundary is the semantic zero sign boundary. There are no fitted weights, thresholds, buckets, clock choices or stock-level ranking changes.

This phase is a **portfolio-utility/risk diagnostic only**. It does not execute hypothetical sells/rebuys, charge costs, alter the frozen account path, or claim an executable strategy.

## Portfolio interval return reconstruction

For each account and China trading day `t`, use the previous China trading day's immutable account snapshot:

- previous-day holdings market values;
- previous-day NAV and cash;
- no mutation of quantities or account policy.

Use a QFQ signal-price view only (per project contract, QFQ is allowed for signal/diagnostic views; no fill claim is made) for each carried holding:

- previous official close QFQ;
- exact 09:35 QFQ close on day `t`;
- exact 09:50 QFQ close on day `t`.

Let previous-day holding weight be `w_i = market_value_i / nav_prev` and previous-day cash weight `w_cash = cash_prev / nav_prev`.

Revalue to 09:35:

`g_i = close_0935_qfq / prev_close_qfq`

`denom_0935 = w_cash + sum_i(w_i * g_i)`

Frozen portfolio 09:35→09:50 diagnostic return:

`portfolio_ret_0935_0950 = sum_i[w_i * g_i * (close_0950_qfq / close_0935_qfq - 1)] / denom_0935`

No nearest-clock substitution, forward/back fill or resampling is allowed. Missing exact prices make that account-day incomplete.

## Evidence boundary

Development material: 2015-01-05..2020-12-31 only.

Report separately for the 14:30 and 14:45 frozen consumer accounts and by natural year 2015..2020. Both account variants must pass jointly. Do not select a clock after outcomes.

2021-2025 is not opened under this identity. Any later reusable validation requires a separately frozen compact protocol and is not independent OOS.

## Diagnostics and gates

For each account clock/year and pooled:

- complete account-day count;
- candidate exposed-day count and coverage;
- comparator mean 15m portfolio return;
- candidate mean utility where de-risked days contribute zero;
- delta mean utility;
- comparator 5th-percentile 15m return;
- candidate 5th-percentile utility.

Sufficiency per clock/year:

- >=150 complete account-days;
- >=40 candidate exposed days;
- >=40 candidate de-risked days.

Progression requires for each clock:

1. pooled candidate-minus-comparator mean utility > 0;
2. at least 4 of 6 annual mean-utility deltas > 0;
3. median annual mean-utility delta >= 0;
4. pooled candidate 5th percentile >= comparator 5th percentile;
5. at least 4 of 6 annual candidate 5th percentiles >= comparator 5th percentiles.

Both clocks must pass jointly.

Passing grants only `retrospective_E3_intraday_portfolio_risk_utility_candidate`. It does not grant account execution, transaction-cost authority, strategy mutation, fresh OOS or production authority. Any executable overlay must be frozen under a new consumer-side strategy identity with applicable Strategy Slice Rebuild / SSA / account-audit requirements.

`production_authority=false`.
