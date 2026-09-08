# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Current data rule

Historical data is **not a consumable resource**. The repository now uses the reusable three-role policy:

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis;
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; results may be opened and diagnosed;
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable certification only, with output restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

A blackbox query does **not** consume the blackbox and does not open its details. Repeated queries are allowed, but they are not independent new OOS samples. Each query must be logged and candidate changes after a query must be justified from DEV/VALIDATION, never from blackbox breakdowns.

## Current R1 position

Active mechanism:

`rmr_cross_scale_pullback_parent_integrity_v2`

Frozen representation:

`R1_PARENT_COMPOSITE_1D`

Under the new role map, R1 was re-evaluated as follows:

1. fit on DEV 2015–2020;
2. detailed validation on 2021–2025;
3. both pairings passed all gates and improved Brier in **5/5 validation years**;
4. one predeclared final refit used DEV+VALIDATION through 2025-12-31;
5. final parameter bundle SHA256: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`;
6. reusable 2026 blackbox query `a9ba75c39e675ae6be17` returned **PASS**;
7. no blackbox metric, count, subperiod, event or error detail was released.

Blackbox receipt:

`docs/research/rmr_R1_reusable_blackbox_certification_20260908.json`

Query ledger:

`docs/governance/reusable_blackbox_query_ledger_v1.json`

## Exact next action

Do **not** wait for unannounced future data.

The next research stage is a separate economic-translation identity for R1 using DEV and VALIDATION only. It may study implementable entry/exit, holding geometry, costs and PnL on the reusable detailed pools, but must keep the current blackbox closed.

Required progression:

1. create `rmr_R1_parent_integrity_economic_translation_v1` with a small preregistered strategy family;
2. develop on DEV and inspect VALIDATION in detail;
3. iterate using DEV/VALIDATION as needed;
4. before any next blackbox query, freeze the exact strategy candidate, fit recipe, cost model and certification gates;
5. only then submit the frozen candidate to the same reusable blackbox validator or a versioned successor;
6. the blackbox returns only `PASS / FAIL / INSUFFICIENT`; never request a failure breakdown.

Economic research on DEV/VALIDATION is now authorized. Production authority remains false.

## 2026Q4 protocol

The previously preregistered complete-2026Q4 challenge is retained as an **optional future extra fresh challenge**. It is no longer the repository-wide blocker and does not prevent current DEV/VALIDATION research. Do not inspect partial Q4 data unless a later authority explicitly changes that protocol.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
5. `docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
6. `docs/INDEX.md`

Old reserve/holdout/true-fresh `next_action` statements remain historical evidence only where they conflict with this authority.

Production authority remains `false`.
