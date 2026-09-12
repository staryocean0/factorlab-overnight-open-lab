# OFP-E2 stock-selection adapter v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_b4_stock_selection_abstention_adapter_v1`

Consumer strategy (frozen external identity):

- repository: `staryocean0/factorlab-multifactor-stock-lab`
- source commit: `af2e478aaff5c8ef7f753424b57fd2d19019f248`
- strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`
- model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`
- account/selection policy: `N30_equal_backfill_unconstrained`
- decision clocks: `14:30` and `14:45`, treated as separate frozen consumer variants
- consumer contract: `docs/ops/reaka_current_k1_account_ledgers@1.5.json`
- selection decision carrier: `output/factor-rotation/reaka_current_k1_account_ledgers_v1_2011_2026/formal/selection_opportunity_decision_summary.csv`

The external consumer is admitted here as an immutable historical selection identity only. This E2 phase does not mutate its ranking, Top30 membership, model, clock, costs, or account policy and does not claim production authority.

## Result-free mechanism

Validated OFP-B4 `driver_coherence` is a pre-open continuous coordinate describing agreement of global risk, China offshore and FX channels. A long-only stock-selection consumer may plausibly have lower opportunity quality when those channels are net risk-off. E2 v1 therefore tests only whether a semantic zero-boundary risk-on filter improves the quality of the consumer's already-frozen Top30 decisions.

B4 is the only Overnight input in E2 v1. E1 validation behavior is not used as a design input. C1, A1, A4, C2, C3 and D1 are excluded.

## Frozen adapter view

For each frozen consumer decision date and each frozen decision clock:

- `driver_coherence` is reconstructed exactly from the validated B4 definition using only information available before the China open;
- `active = 1` iff `driver_coherence >= 0`;
- `active = 0` iff `driver_coherence < 0`;
- stock rankings and Top30 membership are unchanged;
- an inactive decision is interpreted only as a downstream abstention candidate for later consumer research, not as an executed cash trade in this phase.

No nonzero threshold, quantile, magnitude bucket, weight, clock selection, or extra factor is searched.

## Evidence boundary

Development material is exactly `2015-01-05..2020-12-31`, reported by natural year and separately for both `14:30` and `14:45` consumer variants.

The consumer's older 2011-2014 decisions are structurally outside B4 availability and are not fabricated. The consumer's 2021-2025 rows are not opened in detail under this development identity. Any later reusable validation must use a separately frozen compact protocol; reuse of 2021-2025 is not independent OOS.

## Primary and safeguard diagnostics

Primary per-decision utility: `selected_mean_h20_return` from the frozen consumer selection ledger.

Safeguard: `selection_gap_mean_h20_return = selected_mean_h20_return - oracle_mean_h20_return`; closer to zero is better. The adapter is not allowed to improve market beta exposure while materially worsening selection quality relative to the same frozen oracle opportunity set.

For each clock and pooled across clocks, report:

- complete decision count;
- active decision count and coverage;
- comparator mean selected H20 return (all decisions);
- candidate mean selected H20 return (active decisions only);
- delta selected H20 return;
- comparator mean selection gap;
- candidate mean selection gap;
- delta selection gap;
- annual values for 2015..2020.

## Frozen progression rule

Sufficiency, separately for each clock/year:

- at least 20 complete decisions;
- at least 8 active decisions.

Progression requires all of the following for **both** clocks:

1. pooled active-minus-all mean selected H20 return > 0;
2. at least 4 of 6 annual selected-return deltas > 0;
3. median annual selected-return delta >= 0;
4. pooled candidate selection gap is not worse than comparator by more than 0.002 absolute return;
5. at least 4 of 6 annual selection-gap deltas >= -0.002.

Both clocks must pass jointly. There is no post-result clock winner selection.

Passing grants only `retrospective_E2_selection_quality_adapter_candidate`. It does not grant account-PnL, execution, capital allocation, strategy replacement, fresh OOS, or production authority. A later account overlay requires a separate result-free identity and applicable Strategy Slice Rebuild / SSA / post-training account audit.

`production_authority=false`.
