# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Permanent data model

The project uses a reusable three-role scheme:

- **DEV** `2015-01-05 .. 2020-12-31` — full development access;
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis;
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Details remain closed after every query. Reusing the same BLACKBOX is allowed, but repeated queries are not independent new OOS samples.

## Current evidence

### R1 parent integrity — certified mechanism

`rmr_cross_scale_pullback_parent_integrity_v2`

The low-capacity parent-integrity representation passed detailed 2021–2025 VALIDATION and reusable BLACKBOX query #1:

**PASS**

Final mechanism bundle:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

The first bounded R1 economic-translation family is separately closed: v1/v2/v3 all failed detailed VALIDATION before any economic BLACKBOX query. This does not invalidate the statistical mechanism, but it means no currently tested execution family has established trading viability.

### R5-C event density — validation survived, certification failed

`rmr_event_density_state_reversal_v2`

A stricter dedicated test compared event density against a baseline containing severity, completed-wave duration and time since previous confirmation.

Detailed VALIDATION passed on both S1 and S2, but reusable BLACKBOX query #2 returned:

**FAIL**

No BLACKBOX detail was released. R5-C v2 is closed and is not eligible for hidden-period rescue.

## Current next stage

The only broad Stage-1 direction that remained on HOLD rather than CLOSED was R2 range-boundary reversion. A program review has approved exactly one dedicated successor:

`rmr_range_boundary_parent_integrity_v2`

Its question is whether parent-range integrity adds re-entry probability information after controlling for breakout geometry, break speed and local volatility.

Dedicated representation:

`range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff)) / 3`

This identity must first pass both co-primary scales on reusable DEV/VALIDATION. Only then may BLACKBOX query #3 occur.

Review:

`docs/research/rmr_R2_dedicated_program_review_20260908.md`

## Query ledger

The reusable BLACKBOX ledger currently contains two completed queries:

1. R1 parent integrity — `PASS`;
2. R5-C event density — `FAIL`.

Neither query exposes exact recent-period metrics or failure breakdowns.

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Production authority remains false.
