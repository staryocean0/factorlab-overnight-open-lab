# OFP-E2 v3 B2 stock-selection offshore-risk abstention — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1`

## Independent motivation

B2 `china_offshore_z` is a separately validated, China-specific same-contract A50 pre-open coordinate (reusable BLACKBOX query `608e037b0d24724b097b`). Its program-level consumer role includes style rotation. This makes B2 a direct candidate for an A-share stock-selection risk/participation overlay independent of the outcomes of earlier B4/C2 downstream adapters.

This identity is frozen without using hidden behavior from E1/E2/E3 validation queries. It is not a threshold rescue of any prior adapter.

## Frozen consumer

Repository: `staryocean0/factorlab-multifactor-stock-lab`

Pinned commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`

Strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`

Model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`

Selection/account policy: `N30_equal_backfill_unconstrained`

Decision clocks: 14:30 and 14:45 jointly.

Decision-level carrier: `output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/selection_opportunity_decision_summary.csv`, pinned blob SHA `8ad23f84d6664cb6e870e1667cbd4d06682a3626`.

The adapter may only abstain an entire frozen consumer decision; it cannot rerank stocks, alter Top30, weights, clock, model or cost policy.

## Frozen B2 coordinate

`china_offshore_z = a50_channel_return / sqrt(mean(prev 60 China trading-day a50_channel_return^2, min 20, current excluded))`

B2 validated sign is positive.

Comparator: all complete frozen consumer decisions.

Candidate active rule: `china_offshore_z >= 0`.

Candidate inactive rule: abstain when `china_offshore_z < 0`.

Zero is the only boundary. No magnitude threshold/bucket search is allowed.

## Development surface

Development window: `2015-01-05..2020-12-31`.

Primary utility: `selected_mean_h20_return`.

Selection-quality safeguard: `selection_gap_mean_h20_return = selected_mean_h20_return - oracle_mean_h20_return`, higher is better.

This is retrospective selection-quality research only. It is not fresh OOS and does not run or mutate account PnL.

## Sufficiency and progression

Per clock-year:
- at least 20 complete decisions;
- at least 8 candidate-active decisions.

Per clock progression requires:
- pooled selected-return delta > 0;
- at least 4 of 6 annual selected-return deltas > 0;
- median annual selected-return delta >= 0;
- pooled selection-gap delta >= -0.002;
- at least 4 of 6 annual selection-gap deltas >= -0.002.

Both 14:30 and 14:45 must pass. No post-result clock selection.

Passing grants only `retrospective_E2_selection_quality_adapter_candidate_only`; reusable validation would require a separate compact protocol.

## Forbidden post-result actions

No nonzero B2 threshold, magnitude bucket, ordinary/holiday split, cutoff change, alternate RMS window, clock selection, ranking/TopN/weight mutation, added upstream product, account-PnL optimization or hidden-BLACKBOX rescue.

`production_authority=false`.
