# OFP-E2 v2 C2 stock-selection risk abstention adapter — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_c2_stock_selection_risk_abstention_adapter_v1`

## Motivation

This is a new downstream E2 identity enabled by the later reusable validation of C2 (`overnight_volatility_conditioned_open_state_60m_v1`, query `a1068de9321c04632aad`). C2 did not have validated product authority when the prior B4-based E2 identity was frozen.

The economic question is narrow: for an already frozen long-only stock-selection consumer, does the validated C2 morning risk direction provide a useful zero-boundary abstention gate without changing stock rankings, TopN, weights, execution clocks or the consumer model?

This is not a rescue of the earlier B4-based E2 identity. B4 is excluded and no hidden behavior from any failed downstream query is used.

## Frozen consumer

Repository: `staryocean0/factorlab-multifactor-stock-lab`

Pinned commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`

Strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`

Model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`

Selection/account policy: `N30_equal_backfill_unconstrained`

Decision clocks: `14:30` and `14:45`, evaluated jointly with no post-result clock selection.

Consumer decision carrier: `output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/selection_opportunity_decision_summary.csv`, frozen blob SHA `8ad23f84d6664cb6e870e1667cbd4d06682a3626`.

The adapter may only abstain entire consumer decisions. It may not rerank stocks, change Top30 membership, weights, costs, clocks or account policy.

## Frozen upstream coordinate

Validated C2 coordinate:

`vol_gap_interaction = (gap / rvol20) * log(rvol20)`

The validated C2 scientific direction is negative, therefore:

`c2_direction_score = -vol_gap_interaction`

Candidate active rule:

`active iff c2_direction_score >= 0`

Inactive rule:

`abstain iff c2_direction_score < 0`

Zero is the only boundary. No threshold or magnitude search is allowed.

## Development evidence

Development window: `2015-01-05..2020-12-31`.

Consumer outcomes are the already-consumed decision-level H20 selection-quality fields. This phase is retrospective and not fresh OOS.

Primary utility: `selected_mean_h20_return`.

Comparator: mean over all complete consumer decisions for the same clock.

Candidate: mean over C2-active complete consumer decisions for the same clock.

Selection-quality safeguard: `selection_gap_mean_h20_return = selected_mean_h20_return - oracle_mean_h20_return`; the adapter may not materially worsen this gap.

## Sufficiency and progression

For each clock-year: at least 20 complete decisions and at least 8 active decisions.

For each clock separately, progression requires:

- pooled selected-return delta > 0;
- at least 4 of 6 annual selected-return deltas > 0;
- median annual selected-return delta >= 0;
- pooled selection-gap delta >= -0.002;
- at least 4 of 6 annual selection-gap deltas >= -0.002.

Both `14:30` and `14:45` must pass all gates. No winner clock may be selected after results.

Passing grants only `retrospective_E2_selection_quality_adapter_candidate_only`. No account-PnL, strategy-execution or production authority is granted.

## Forbidden post-result actions

No nonzero C2 threshold, magnitude bucket, alternate horizon, clock selection, ranking mutation, TopN mutation, weight change, extra upstream factor, cost/fill optimization or hidden-BLACKBOX rescue.

`production_authority=false`.
