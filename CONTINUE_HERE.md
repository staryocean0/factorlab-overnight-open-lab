# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Permanent data rule

Historical data is reusable, not a one-shot consumable:

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis.
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; year/event/regime diagnostics are allowed.
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable certification only; public output is restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

BLACKBOX may be reused by separately frozen candidates, but repeated queries are not independent new OOS samples. Never release exact BLACKBOX metrics, counts, dates, subperiods, events, probabilities or failure examples. Every completed query must be appended to `docs/governance/reusable_blackbox_query_ledger_v1.json`.

## Certified / closed evidence

### R1 parent integrity

`rmr_cross_scale_pullback_parent_integrity_v2`

- detailed VALIDATION PASS on both scale pairings;
- reusable BLACKBOX query #1 `a9ba75c39e675ae6be17`: **PASS**;
- final mechanism bundle: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`;
- no BLACKBOX detail released.

R1 remains the only currently BLACKBOX-certified mechanism.

Its first bounded economic-translation family is closed after v1/v2/v3 all failed detailed VALIDATION before BLACKBOX. Do not create v4/v5 by tweaking the same next-minute / original-boundary / 10bp execution family.

### R5-C event density

`rmr_event_density_state_reversal_v2`

- dedicated geometry-baseline VALIDATION: PASS on S1 and S2;
- reusable BLACKBOX query #2 `4fa9bfa2ec38f16cd65f`: **FAIL**;
- BLACKBOX details remain closed;
- v2 identity is closed and may not be rescued from hidden recent-period behavior.

Closeout:

`docs/research/rmr_R5C_reusable_closeout_20260908.md`

## Exact next action

A program review has approved one bounded dedicated successor for the only broad mechanism that remained on HOLD rather than CLOSED:

`rmr_range_boundary_parent_integrity_v2`  (R2 dedicated)

Review:

`docs/research/rmr_R2_dedicated_program_review_20260908.md`

The scientific question is:

> After controlling for attempted-breakout geometry, speed and local volatility, does an intact parent range increase first re-entry probability?

Frozen dedicated representation:

- baseline: `outside_ratio + break_speed + local_vol_ratio`;
- added feature only: `range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff)) / 3`;
- S1-outside-S2 and S2-outside-S3 are co-primary;
- same broad R2 event / re-entry-vs-continuation outcome geometry;
- DEV 2015–2020; detailed VALIDATION 2021–2025;
- no threshold, scale, speed-window, vol-window, interaction or PnL search.

Required progression:

1. freeze the exact R2 dedicated protocol/runner/tests before empirical execution;
2. run DEV/VALIDATION only;
3. both scales must beat the geometry baseline on pooled Brier and log-loss, show >=4/5 annual Brier improvement, meet sample gates, and have positive DEV range-integrity coefficient;
4. only after full VALIDATION PASS may one DEV+VALIDATION final refit be frozen;
5. only then may BLACKBOX query #3 occur, with three-state output only;
6. a BLACKBOX FAIL/INSUFFICIENT closes R2 v2 with no hidden breakdown and no automatic R2 v3.

## Optional future data

The preregistered complete-2026Q4 R1 challenge remains an optional future extra experiment, not a current blocker. When the user supplies newer data, version the three-role map forward rather than declaring existing history consumed.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. active specialist state/protocol listed in `docs/INDEX.md`
5. `docs/INDEX.md`

Production authority remains `false`.
