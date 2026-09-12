# OFP-E2 v2 C2 stock-selection risk abstention adapter — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_c2_stock_selection_risk_abstention_adapter_v1`

Phase: retrospective selection-quality diagnostic only.

Development window: `2015-01-05..2020-12-31`.

## Frozen identity

Consumer is pinned to `staryocean0/factorlab-multifactor-stock-lab@af2e478aaff5c8ef7f753424b57fd2d19019f248`, strategy `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`, model `d8-h8-K1-r0_fit_prefix_successor_incumbent`, policy `N30_equal_backfill_unconstrained`, with 14:30 and 14:45 evaluated jointly.

Validated C2 coordinate:

`vol_gap_interaction = (gap / rvol20) * log(rvol20)`

Frozen direction score:

`c2_direction_score = -vol_gap_interaction`

Candidate keeps a frozen consumer decision iff `c2_direction_score >= 0`; otherwise it abstains. Rankings, Top30, weights, consumer model, clocks and costs are unchanged.

## Execution integrity

The consumer decision carrier is pinned by commit and blob SHA. Only 2015–2020 rows were admitted for science; the first post-2020 row was used only as a stream-stop sentinel. C2 was reconstructed from the already-published 2015–2020 factor runtime carrier. No 2021–2025 scientific rows, account-PnL backtest or strategy execution were opened.

No threshold, magnitude bucket, clock choice, ranking mutation, TopN mutation or upstream add/drop search occurred.

## Sufficiency result

The frozen rule requires each clock-year to have at least 20 complete decisions and at least 8 C2-active decisions.

For both 14:30 and 14:45, calendar year 2017 has only **6 active decisions**, below the frozen minimum of 8. Other years meet the active-count threshold.

Therefore annual sufficiency fails for both consumer clocks.

## Decision

**`E2V2_DEV_INSUFFICIENT`**

This is an evidence-sufficiency outcome, not a scientific FAIL of C2 or the frozen REAKA consumer. Because sufficiency fails before progression adjudication, the observed incomplete-surface utility statistics do not authorize selection, rejection, threshold changes, alternate sign rules, clock selection or a successor under this identity.

No reusable validation successor is authorized and no BLACKBOX query is created.

`production_authority=false`.
