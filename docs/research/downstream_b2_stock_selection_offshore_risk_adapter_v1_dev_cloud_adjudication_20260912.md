# OFP-E2 v3 B2 stock-selection offshore-risk adapter — Development adjudication

Date: 2026-09-12

Research identity: `overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1`

## Frozen identity

- consumer: pinned `REAKA_D5_H20_R5_CURRENT_GENERATION_V1` at commit `af2e478aaff5c8ef7f753424b57fd2d19019f248`;
- clocks: 14:30 and 14:45 jointly;
- upstream: validated B2 `china_offshore_z`, reusable query `608e037b0d24724b097b`;
- adapter: whole decision active iff `china_offshore_z >= 0`, otherwise abstain;
- development window: `2015-01-05..2020-12-31`;
- primary utility: `selected_mean_h20_return`;
- selection-quality safeguard: selected return minus oracle return;
- no ranking, Top30, weights, consumer parameter, threshold, bucket, holiday split, clock selection, account-PnL, or upstream-product mutation.

## Development result

**`E2V3_DEV_NO_PROGRESS`**

Both clocks pass every preregistered annual sufficiency gate, so this is not an insufficient-data result.

For 14:30, pooled selected-return delta is positive, but only 3 of 6 annual selected-return deltas are positive and the pooled selection-gap delta is worse than the frozen -0.002 tolerance; the annual selection-gap count gate also fails.

For 14:45, pooled selected-return delta is positive, but only 3 of 6 annual selected-return deltas are positive and the pooled selection-gap delta is worse than the frozen -0.002 tolerance. The annual selection-gap count gate passes, but the full joint progression contract does not.

Therefore neither clock passes the frozen progression contract, and the joint-clock rule fails.

## Authority consequence

- no reusable 2021-2025 validation successor;
- no new reusable BLACKBOX query; ledger remains 12;
- no account-PnL backtest;
- no validated E2v3 product;
- no threshold/bucket/clock rescue;
- validated upstream B2 remains valid;
- `production_authority=false`.

The observed Development details are evidence for this exact frozen adapter only. They do not authorize changing the B2 zero boundary, selecting a clock, mutating the consumer, or constructing an outcome-tuned successor.
