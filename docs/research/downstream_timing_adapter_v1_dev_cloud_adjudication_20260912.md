# OFP-E1 timing adapter v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_c1_b4_timing_confidence_adapter_v1`

Phase: retrospective factor-utility diagnostic only

Development window: `2015-01-05..2020-12-31`

## Frozen identity

Comparator:

`c1_action = sign(-trend_gap_interaction)`

Candidate:

`c1_action if driver_coherence * sign(observed_gap_rvol) >= 0 else 0`

The candidate therefore does not create a new direction. Validated C1 is the only direction source. Validated B4 may only abstain at the result-free semantic zero alignment boundary.

Frozen target:

`ret_0935_0950 = close_0950 / close_0935 - 1`

This phase is not an account backtest, does not claim the cash index is directly tradable, uses no cost model, and grants no strategy or production authority.

## Execution integrity

The exact B4 development reconstruction implementation was reused for `driver_coherence`; C1 was reconstructed from its frozen continuous formula on the same connector-readable factor carrier. Opening target clocks came from the accepted 2015-2020 runtime text carrier.

The first workflow run failed before outcome computation because the mechanical runner incorrectly required the post-B4-warmup merged frame to begin exactly on the raw development start date. No receipt or scientific result was produced. The retry changed only that infrastructure check: all loaded rows must remain inside the frozen development boundary and annual complete-case sufficiency is adjudicated by the preregistered gate. The candidate, comparator, target and gates were unchanged.

The successful receipt records:

- no 2021-2025 detailed rows opened;
- no account or stock-selection backtest opened;
- no strategy-PnL optimization;
- no cost model;
- no threshold, weight, horizon or upstream add/drop search;
- one candidate attempt only;
- reusable BLACKBOX ledger unchanged.

## Development results

All six years pass the preregistered sufficiency gates.

Pooled complete cases: **1342**.

Pooled candidate active days: **858**.

Pooled candidate coverage: **0.639344**.

Pooled comparator active days: **1341**.

Pooled comparator hit rate: **0.493661**.

Pooled candidate active hit rate: **0.501166**.

Pooled mean comparator signed utility: **-0.0000986771**.

Pooled mean candidate signed utility: **-0.0000220145**.

Pooled delta mean signed utility: **+0.0000766626**.

Annual delta mean signed utility:

- 2015: `+0.0003013671`
- 2016: `+0.0003894145`
- 2017: `-0.0002599604`
- 2018: `+0.0000649667`
- 2019: `-0.0000765338`
- 2020: `+0.0000832934`

Preregistered dispersion result:

- positive annual delta count: **4 / 6** — PASS;
- median annual delta: **+0.0000741300** — PASS;
- pooled delta > 0 — PASS;
- all annual sufficiency gates — PASS.

## Decision

**`E1_DEV_PROGRESS_RETROSPECTIVE_FACTOR_UTILITY_ADAPTER_CANDIDATE`**

This decision is deliberately narrow.

The evidence supports retaining the exact zero-boundary B4 abstention overlay as retrospective factor-utility progression material relative to the C1-only comparator. It does **not** establish a profitable executable strategy. In particular, the pooled candidate signed utility remains slightly negative even though it improves materially relative to the more-negative comparator. That tradeoff is retained rather than hidden or reinterpreted.

No alternate B4 threshold, magnitude bucket, weight, horizon, upstream product, or sign convention may be searched under this identity after observing these results.

## Authority consequence

Maximum authority now granted:

`retrospective_factor_utility_adapter_candidate_only`

Not granted:

- validated E1 product authority;
- executable timing strategy authority;
- instrument mapping;
- costs or fill semantics;
- position sizing;
- stock-selection authority;
- Strategy Slice Rebuild completion;
- SSA or A0-A7 post-training account-audit completion;
- fresh OOS authority;
- production/live authority.

A future reusable 2021-2025 aggregate BLACKBOX may only be opened under a separately frozen, result-free validation identity/protocol. Reuse of that physical period is not independent OOS. A future executable consumer strategy requires a separate consumer-side identity satisfying the applicable Strategy Slice Rebuild / SSA / account-audit contracts; this development receipt cannot substitute for them.

`production_authority=false`.
