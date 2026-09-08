# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Permanent data model

The project uses a reusable three-role scheme:

- **DEV** `2015-01-05 .. 2020-12-31` — full development and diagnosis;
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis;
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Repeated queries are not independent OOS samples. Exact BLACKBOX metrics, counts, dates, subperiods, events, probabilities, attribution and failure examples must never be released.

## Certified statistical mechanisms

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

- reusable detailed VALIDATION: PASS;
- BLACKBOX query #1: `PASS`;
- final parameter bundle: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

- reusable detailed VALIDATION: PASS on both co-primary cells;
- BLACKBOX query #3: `PASS`;
- final parameter bundle: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.

R1 and R2 are complementary parent-normal-state mechanisms: an intact trend raises lower-scale recovery probability, while an intact range raises attempted-breakout re-entry probability. They are not interchangeable signals and are not automatically one common scalar axis.

### R5-C — closed

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 returned `FAIL`. No hidden-period detail was released and same-identity rescue is prohibited.

## Unified router result

`rmr_unified_parent_normal_state_router_v1` was tested on DEV/VALIDATION only and **closed at VALIDATION**.

After a pure scale-identity implementation bug was fixed without changing protocol, the router improved pooled metrics overall because R1 improved, but both R2 cells worsened. Therefore:

> R1 and R2 are conceptually complementary, but cannot be compressed into the tested common standardized state-consistency axis.

No BLACKBOX query occurred. There is still no query #4.

Current retained evidence:

- `docs/research/rmr_unified_parent_state_router_v1_validation_adjudication_20260908.md`
- `docs/research/rmr_unified_parent_state_router_v1_closeout_20260908.md`
- `docs/archive/rmr_unified_parent_state_router_v1_history_anchor_20260908.md`

## Mechanism → execution diagnostic

`rmr_mechanism_to_execution_diagnostic_v1` is complete on DEV+VALIDATION only.

The diagnostic explains why certified restoration probabilities did not translate into the tested index-level next-minute / structural-boundary / 10bp execution family:

- the dominant failure is payoff-geometry mismatch: eventwise binary structural expected net is negative in all four VALIDATION cells;
- next-minute confirmation delay consumes little structural reward and is not the primary cause;
- boundary overshoot is a secondary aggravator, not the root cause;
- frozen restoration probabilities are not monotonic realized-return scores;
- R2 markouts deteriorate with horizon under the current directional execution family;
- R1_B alone shows a broad delayed positive markout term structure, motivating a **new temporal execution theory review**, not horizon selection.

Evidence:

- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_adjudication_20260908.md`
- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json`
- `docs/archive/rmr_mechanism_to_execution_diagnostic_v1_history_anchor_20260908.md`

No BLACKBOX source was opened; the query ledger remains exactly **3**.

## Economic translation status

No trading implementation is certified.

- R1 economic v1/v2/v3 failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- the current index-level next-minute / structural-boundary / 10bp family is closed for R1_A and R2_A/R2_B;
- do not create automatic R1 economic v4, R2 economic v2, router v2, probability-threshold rescue or horizon/entry/stop/cost/scale tuning against VALIDATION.

## Exact next stage

Automatic broad R8/R9 indicator generation remains paused.

The next allowed task is a **results-blind R1_B temporal execution theory review**. It must first explain causally why the higher-scale trend-parent restoration mechanism should realize through a distributed time path. It may not select 120/240 bars from the completed diagnostic, tune any execution parameter, use a PnL threshold to formulate the theory, access BLACKBOX, or claim production authority.

Instrument mapping (ETF/futures/options) is not the current choice because the diagnostic contains no instrument-specific basis, spread, liquidity, carry or convexity evidence. It remains eligible only under a separate independently motivated theory.

## BLACKBOX ledger

Completed reusable BLACKBOX queries:

1. R1 parent integrity — `PASS`;
2. R5-C event density — `FAIL`;
3. R2 range integrity — `PASS`.

**No query #4 exists or is currently authorized.**

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Production authority remains `false`.
