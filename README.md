# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Current data model

The project now uses a permanent reusable three-role scheme instead of treating historical periods as consumable holdouts:

- **DEV** `2015-01-05 .. 2020-12-31` — full development access;
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis;
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

A blackbox query returns only `PASS / FAIL / INSUFFICIENT`. Its details remain closed after every query. Reusing the same blackbox is allowed, but repeated queries are not independent new OOS samples.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

## Current scientific result

The strongest mechanism remains:

`rmr_cross_scale_pullback_parent_integrity_v2`

with frozen representation:

`parent_integrity = (z(abs_drift) - z(overlap) + z(parent_eff)) / 3`

and severity:

`abs(counter_move) / DEV_median_rvol20`.

Under the new role map, the R1 candidate was fit on DEV 2015–2020 and checked in detail on VALIDATION 2021–2025.

- PAIR_A: 1,283 validation events; pooled Brier improvement `0.0097436681`; log-loss improvement `0.0214322349`; positive annual Brier improvement in 5/5 years.
- PAIR_B: 517 validation events; pooled Brier improvement `0.0094935894`; log-loss improvement `0.0217072277`; positive annual Brier improvement in 5/5 years.

After validation passed, the predeclared recipe performed one final refit on DEV+VALIDATION through 2025-12-31. Final parameter bundle SHA256:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

The first reusable blackbox query then returned:

**PASS**

No blackbox exact metric, count, month, event, subgroup, error example or probability was released.

Receipt:

`docs/research/rmr_R1_reusable_blackbox_certification_20260908.json`

## Current next stage

The repository should **not wait for future data**. The next identity is:

`rmr_R1_parent_integrity_economic_translation_v1`

It may research entry/exit geometry, holding rules, transaction costs and PnL using DEV and VALIDATION only. Before another blackbox query, the exact strategy candidate, cost assumptions, fit recipe and certification gates must be frozen.

Production authority remains false.

## Optional future data

The previously preregistered complete-2026Q4 true-fresh challenge remains available as a future extra experiment, but it no longer blocks present research. When the user explicitly supplies newer data, the three-role map will be versioned forward rather than treating old data as used up.

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
5. `docs/INDEX.md`

Historical material removed during repository consolidation remains recoverable through Git history and does not override current authority.
