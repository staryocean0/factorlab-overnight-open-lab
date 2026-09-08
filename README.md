# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Permanent data model

- **DEV** `2015-01-05 .. 2020-12-31` — reusable full development and diagnosis.
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis.
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Repeated queries are not independent OOS samples. Exact hidden metrics, counts, dates, subperiods, events, probabilities, attribution and failure examples must never be released.

## Certified statistical mechanisms

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

- detailed VALIDATION: PASS;
- BLACKBOX query #1: `PASS`;
- final bundle: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

- detailed VALIDATION: PASS on both co-primary cells;
- BLACKBOX query #3: `PASS`;
- final bundle: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.

R1 and R2 are complementary parent-normal-state mechanisms, not interchangeable scalar signals.

### R5-C — closed

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 returned `FAIL`. No hidden-period detail was released and same-identity rescue is prohibited.

## Closed synthesis and economic work

### Unified parent-state router v1

`rmr_unified_parent_normal_state_router_v1` closed at VALIDATION. After a pure scale-identity implementation fix, both R2 cells worsened; the tested common standardized state-consistency axis is not supported. No BLACKBOX query occurred.

### Mechanism → execution diagnostic

`rmr_mechanism_to_execution_diagnostic_v1` completed on DEV+VALIDATION only. It showed:

- payoff geometry is the primary bridge failure;
- next-minute delay and boundary overshoot are secondary;
- restoration probability is not a monotonic realized-return score;
- R2 directional markouts deteriorate with horizon;
- R1_B alone showed a delayed positive markout term structure, motivating one separate temporal theory test.

No BLACKBOX source was opened; the ledger remained at 3 queries.

### R1_B temporal impulse completion v1 — closed on DEV

`rmr_R1B_temporal_impulse_completion_v1` was the single results-blind temporal identity authorized after the diagnostic.

Theory: after a certified R1_B `S2-inside-S3` pullback confirmation, treat the next complete parent-aligned S2 impulse as the temporal economic object. Entry remained the next observed 1m close. Exit was the **causal confirmation close** of the first subsequent parent-aligned S2 wave, unless the original S3 structural failure boundary was crossed first. S2/S3 thresholds, 10bp cost and the inherited 1200-bar safety horizon were unchanged.

DEV-only result on `682` tradeable events:

- candidate mean net: **+10.59bp**;
- candidate minus structural baseline mean net: **+11.87bp**;
- positive candidate mean-net years: **5 / 6**;
- candidate median net: **-32.11bp**;
- candidate win rate: **37.10%**.

The preregistered DEV gate required positive median net. That gate failed, so the identity is **closed on DEV**. VALIDATION was never opened.

Interpretation: the temporal object captures a positive right-tail component, but not a broad typical-event translation. The result may not be rescued by removing the median gate, exiting at the unobservable S2 extreme, choosing a fixed horizon, adding a probability filter, or tuning entry/stop/target/cost/scale/year/regime.

Evidence:

- `docs/research/rmr_R1B_temporal_execution_theory_program_review_20260908.md`
- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_adjudication_20260908.md`
- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_decisive_receipt_20260908.json`
- `docs/archive/rmr_R1B_temporal_impulse_completion_v1_history_anchor_20260908.md`

## Current economic status

No trading implementation is certified.

Closed without BLACKBOX:

- R1 economic v1/v2/v3;
- R2 economic v1;
- unified router v1;
- R1_B temporal impulse completion v1.

No automatic R1 economic v4, R2 economic v2, router v2, temporal v2, probability-filter rescue, or horizon/entry/stop/cost/scale tuning is authorized.

## Exact next stage

There is currently **no empirical economic candidate authorized**.

If economic research continues, the next task must be a separate results-blind **payoff-object or instrument-theory program review**. A new identity must be materially independent of the closed timing rule and preregistered before any new empirical output is opened.

Instrument mapping remains only a theory-level possibility because the current repository does not contain instrument-specific spread, basis, carry, liquidity, convexity or option-premium evidence. Any ETF/futures/options study requires its own data-source and cost-model contract first.

Broad R8/R9 indicator discovery remains paused.

## BLACKBOX ledger

Completed reusable BLACKBOX queries remain exactly:

1. R1 parent integrity — `PASS`;
2. R5-C event density — `FAIL`;
3. R2 range integrity — `PASS`.

**No query #4 exists or is authorized.**

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Production authority remains `false`.
