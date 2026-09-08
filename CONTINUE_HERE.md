# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Permanent data rule

Historical data is a reusable research asset, not a one-shot consumable.

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis.
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; year/event/regime diagnostics are allowed.
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable low-bandwidth certification only; public output is restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

BLACKBOX may be queried repeatedly by separately frozen candidates, but queries are not independent new OOS samples. Never release exact blackbox metrics, counts, dates, subperiods, events, probabilities or failure examples. Every completed blackbox query must be appended to `docs/governance/reusable_blackbox_query_ledger_v1.json`.

## R1 status

Mechanism:

`rmr_cross_scale_pullback_parent_integrity_v2`

R1 passed detailed 2021–2025 VALIDATION on both scale pairings and then passed reusable BLACKBOX query `a9ba75c39e675ae6be17` with no detail release. Its final mechanism bundle is:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

R1 therefore remains a **certified mechanism**.

However, the first bounded economic-translation round is closed:

- v1 probability-edge trading: VALIDATION fail;
- v2 binary-boundary structural expectancy: VALIDATION fail;
- v3 direct realized-return Ridge model: VALIDATION fail;
- all three failed **before BLACKBOX**, so no economic blackbox query occurred.

Controlling closeout:

`docs/research/rmr_R1_economic_translation_round_closeout_20260908.md`

Do not create R1 economic v4/v5 by tweaking the same next-minute / original-boundary / 10bp family against VALIDATION. A future R1 economic identity requires genuinely new execution or instrument theory.

## Exact next action

Move the active research budget to the queued Priority-B mechanism:

`rmr_event_density_state_reversal_v2`  (R5-C)

Use the same three-role data policy:

1. freeze one small dedicated R5-C representation/model family before running it;
2. develop on DEV and inspect VALIDATION in detail;
3. require stable incremental value beyond a nearby event-geometry baseline on both S1 and S2;
4. only after VALIDATION PASS may one final DEV+VALIDATION refit be frozen;
5. only then may the reusable BLACKBOX be queried, with three-state output only;
6. a BLACKBOX FAIL/INSUFFICIENT reveals no breakdown and must return research to DEV/VALIDATION.

The existing scientific handoff is:

`docs/ops/rmr_R5C_event_density_promotion_handoff_20260908.md`

## Optional future data

The previously preregistered complete-2026Q4 R1 challenge remains an optional future extra experiment. It is not a current blocker. When the user supplies newer data, version the three-role map forward rather than declaring the existing history consumed.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. active specialist state/protocol listed in `docs/INDEX.md`
5. `docs/INDEX.md`

Production authority remains `false`.
