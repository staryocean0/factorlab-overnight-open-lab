# FactorLab Reversal / Mean-Reversion Research

This is the single canonical repository for the project.

## Permanent data model

The project uses a reusable three-role scheme:

- **DEV** `2015-01-05 .. 2020-12-31` — full development access;
- **VALIDATION** `2021-01-01 .. 2025-12-31` — reusable detailed validation and diagnosis;
- **BLACKBOX** `2026-01-05 .. 2026-08-21` — reusable low-bandwidth certification only.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Details remain closed after every query. Reusing the same BLACKBOX is allowed, but repeated queries are not independent new OOS samples.

## Current certified mechanism set

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

Detailed VALIDATION passed and BLACKBOX query #1 returned **PASS**.

Final mechanism bundle:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

Detailed VALIDATION passed on both co-primary scales and BLACKBOX query #3 returned **PASS**.

Final mechanism bundle:

`08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`

R1 and R2 are complementary expressions of the same higher-level idea:

> first identify whether the parent normal state is intact and whether that normal state is trend-like or range-like; then ask whether the observed deviation restores toward that state or represents state failure.

### R5-C — closed

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 returned **FAIL**. No hidden-period detail was released and the v2 identity is closed.

## Economic translation status

No tested trading implementation is certified.

- R1 economic v1/v2/v3 all failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 also failed detailed VALIDATION before BLACKBOX.
- therefore no economic BLACKBOX query has occurred; the query ledger contains exactly three mechanism queries.

R2 economic-v1 closeout:

`docs/research/rmr_R2_economic_translation_v1_closeout_20260908.md`

The current evidence therefore separates mechanism from implementation:

> R1 and R2 contain certified state-transition probability information, but the tested index-level next-minute / structural-boundary / 10bp execution families do not establish trading viability.

Do not rescue these execution families by tuning thresholds, costs, entry delays, stops, scales or time filters against VALIDATION.

## Current next stage

Automatic broad indicator discovery remains paused.

The next allowed research task is a low-capacity **unified parent-state router review** built only from the two certified mechanisms. It asks whether one common signed parent-state axis can coherently route trend-like deviations to R1 and range-like deviations to R2 while adding restoration-probability information beyond each lane's local geometry baseline.

This is scientific synthesis, not a new R8/R9 indicator family and not an economic rescue. Any approved router must pass DEV/VALIDATION before a possible low-bandwidth BLACKBOX query #4.

## Query ledger

Completed reusable BLACKBOX queries:

1. R1 parent integrity — `PASS`;
2. R5-C event density — `FAIL`;
3. R2 range integrity — `PASS`.

No query exposes exact recent-period metrics, counts, dates, subperiods or failure breakdowns.

## Read first

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Production authority remains false.
