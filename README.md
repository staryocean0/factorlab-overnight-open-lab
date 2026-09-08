# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Permanent data model

The project uses a reusable three-role scheme:

- **DEV** `2015-01-05 .. 2020-12-31` — full development access;
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis;
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Repeated queries are allowed for separately frozen candidates, but they are not independent new OOS samples and never release blackbox detail.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

## Strongest established mechanism

`rmr_cross_scale_pullback_parent_integrity_v2`

Frozen representation:

`parent_integrity = (z(abs_drift) - z(overlap) + z(parent_eff)) / 3`

R1 was fit on DEV 2015–2020 and validated in detail on 2021–2025:

- PAIR_A: 1,283 validation events; Brier improvement `0.0097436681`; positive annual Brier improvement 5/5 years;
- PAIR_B: 517 validation events; Brier improvement `0.0094935894`; positive annual Brier improvement 5/5 years.

After the predeclared DEV+VALIDATION final refit, parameter bundle:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

Reusable BLACKBOX query `a9ba75c39e675ae6be17` returned:

**PASS**

No blackbox metric, count, subperiod, event or failure detail was released.

R1 is therefore a **certified mechanism**, not a certified trading strategy.

## R1 economic translation result

Three bounded implementations were tested on DEV / VALIDATION only:

1. probability-edge filter;
2. binary-boundary structural expectancy filter;
3. direct realized-return Ridge model.

All three failed the detailed VALIDATION gates before BLACKBOX. No economic blackbox query occurred. The economic round is closed rather than continuing to fit VALIDATION with v4/v5 tweaks.

Closeout:

`docs/research/rmr_R1_economic_translation_round_closeout_20260908.md`

## Current active research

The next specialist is the previously promoted Priority-B mechanism:

`rmr_event_density_state_reversal_v2`  (R5-C)

Its dedicated work must use the same DEV / VALIDATION / reusable BLACKBOX policy. BLACKBOX is only available after a frozen R5-C candidate passes detailed VALIDATION.

Scientific handoff:

`docs/ops/rmr_R5C_event_density_promotion_handoff_20260908.md`

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

The optional complete-2026Q4 R1 experiment remains preregistered but is not a current blocker. When newer data is supplied, version the three-role map forward rather than declaring old history consumed.

Production authority remains false.
