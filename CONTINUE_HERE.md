# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Permanent data rule

Historical data is reusable, not one-shot consumable:

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis.
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; year/event/regime diagnostics are allowed for frozen low-capacity identities.
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable low-bandwidth certification only; public output is restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy: `docs/governance/reusable_three_role_data_policy_v1.json`.

Never use hidden BLACKBOX behavior to choose a feature, threshold, scale, rule, instrument or model. Every completed query is append-only in `docs/governance/reusable_blackbox_query_ledger_v1.json`.

## Certified mechanisms

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

- detailed VALIDATION PASS;
- BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`;
- final bundle `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

- detailed VALIDATION PASS on both co-primary cells;
- BLACKBOX query #3 `a7e7f0208512aa7c1f31`: `PASS`;
- final bundle `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.

R1 and R2 are complementary parent-normal-state mechanisms, but they are not interchangeable signals and cannot be assumed to share one scalar router.

## Closed evidence

### R5-C

`rmr_event_density_state_reversal_v2` passed VALIDATION and then BLACKBOX query #2 returned `FAIL`. No hidden detail was released. Same-identity rescue is prohibited.

### Unified parent-state router v1

`rmr_unified_parent_normal_state_router_v1` is closed at VALIDATION. After the scale-alignment implementation bug was fixed without changing the scientific protocol, both R2 cells worsened. Router v2 rescue is not authorized.

### Existing economic families

No tested trading implementation is certified.

- R1 economic v1/v2/v3 failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- R1_A and R2_A/R2_B current simple index-level execution families were closed by the mechanism-to-execution diagnostic.
- probability-filter rescue is closed because certified probability is not a monotonic realized-return score.

## Mechanism → execution diagnostic — complete

`rmr_mechanism_to_execution_diagnostic_v1` completed on DEV+VALIDATION only and opened no BLACKBOX data.

It established:

1. payoff geometry is the primary bridge failure;
2. next-minute confirmation delay is too small to justify tuning entry delay;
3. boundary overshoot aggravates losses but is not the root cause;
4. restoration probability is not a monotonic realized-return score;
5. R2 directional markouts become increasingly adverse with horizon;
6. R1_B alone showed a broad delayed positive markout term structure and slow resolution.

That sixth observation authorized one results-blind temporal theory identity, not a horizon choice.

## R1_B temporal impulse completion v1 — CLOSED ON DEV

Identity: `rmr_R1B_temporal_impulse_completion_v1`.

Frozen theory:

> After a certified R1_B S2 pullback is confirmed, the temporal restoration object is one complete subsequent S2 impulse in the S3 parent direction. Because the impulse extreme is not causal, economic completion is the first subsequent parent-aligned S2 wave **confirmation close**, unless the original S3 failure boundary is crossed first.

The implementation changed no S2/S3 thresholds, entry delay, cost, parent failure boundary or safety horizon and used no probability filter.

DEV-only Actions run `34229441615` passed all 7 governance/boundary tests and matched the certified R1_B event population exactly.

On `682` tradeable DEV events:

- mean net: `+10.59bp`;
- improvement over original structural baseline mean net: `+11.87bp`;
- positive mean-net years: `5/6`;
- **median net: `-32.11bp`**;
- win rate: `37.10%`.

Predeclared DEV gates:

- pooled mean net > 0: PASS;
- pooled mean net > baseline: PASS;
- pooled median net > 0: **FAIL**;
- positive mean-net years >= 4/6: PASS.

Overall: **DEV_CLOSE**.

VALIDATION was never opened and is permanently unauthorized for this identity. The failed median gate may not be removed after seeing the result.

Interpretation: the candidate captures a positive right-tail component but not a broad typical-event translation. The result does not authorize exiting at the unobservable S2 extreme, adding probability filters, choosing 30/60/120/240 bars, or tuning entry/stop/target/cost/scale/year/regime.

Evidence:

- `docs/research/rmr_R1B_temporal_execution_theory_program_review_20260908.md`
- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_adjudication_20260908.md`
- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_decisive_receipt_20260908.json`
- `docs/archive/rmr_R1B_temporal_impulse_completion_v1_history_anchor_20260908.md`

## Exact next action

There is currently **no empirical economic candidate authorized**.

Do not automatically create R1_B temporal v2, R1 economic v4, R2 economic v2, router v2, or a probability/horizon/entry/stop/target/cost/scale rescue.

If economic research is to continue, the next allowed step is a separate results-blind **payoff-object or instrument-theory program review**. It must state an independent economic theory before opening any new empirical candidate.

A new review may consider whether the observed right-tail payoff suggests a materially different payoff object or instrument, but it must not simply repair the closed impulse-confirmation rule. Any instrument mapping must first establish an instrument-specific data-source and cost-model contract covering the relevant spread, basis, carry, liquidity, convexity/premium and execution conventions.

No current instrument study is empirically authorized because this repository contains index-level paths, not instrument-specific execution evidence.

Broad R8/R9 indicator discovery remains paused.

## BLACKBOX state

The append-only ledger remains exactly **3** completed queries:

1. R1 — PASS;
2. R5-C — FAIL;
3. R2 — PASS.

There is **no query #4**, and none is scheduled or authorized.

## Optional future data

Do not wait for future data. Continue only work authorized above. If newer data is supplied later, version the three-role map forward rather than declaring existing history consumed.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. active certified-mechanism states/protocols listed in `docs/INDEX.md`
5. `docs/INDEX.md`

Production authority remains `false`.
