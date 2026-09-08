# AGENTS.md — repository operating rules

## 1. One canonical repository

`staryocean0/factorlab-overnight-open-lab` is the only active repository for this project.

## 2. Current authority

Read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Historical `next_action` fields never override these files.

## 3. Reusable three-role data governance

### DEV

`2015-01-05 .. 2020-12-31`

Full development/diagnostic access.

### VALIDATION

`2021-01-01 .. 2025-12-31`

Reusable detailed validation. Year/event/regime diagnostics are allowed and may motivate later DEV/VALIDATION iterations.

### BLACKBOX

`2026-01-05 .. 2026-08-21`

Reusable certification only. Public output is limited to:

`PASS / FAIL / INSUFFICIENT`

Never release exact BLACKBOX metrics, counts, dates, subperiods, regimes, event examples, probabilities, feature attribution or failure analysis.

Repeated BLACKBOX queries are allowed for separately frozen candidates but are not independent new OOS samples. Append every completed query to `docs/governance/reusable_blackbox_query_ledger_v1.json`.

A BLACKBOX FAIL/INSUFFICIENT returns research to DEV/VALIDATION without a breakdown. Hidden BLACKBOX behavior may never justify a feature, threshold, scale, rule or model change.

## 4. Final-fit rule

A candidate may receive one preregistered DEV+VALIDATION final refit only after detailed VALIDATION passes. BLACKBOX may never participate in fitting, candidate selection, thresholds or feature choice.

## 5. Certified mechanisms

### R1

`rmr_cross_scale_pullback_parent_integrity_v2`

Trend-like intact-parent pullback recovery. BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`.

### R2

`rmr_range_boundary_parent_integrity_v2`

Range-like intact-parent boundary re-entry. BLACKBOX query #3 `a7e7f0208512aa7c1f31`: `PASS`.

R1 and R2 are complementary state-restoration mechanisms, not independent generic signals.

### R5-C

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 `4fa9bfa2ec38f16cd65f` returned `FAIL`. The identity is closed and may not be rescued using hidden recent-period behavior.

## 6. Economic translation boundary

No tested economic implementation is certified.

- R1 economic v1/v2/v3 all failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- no economic BLACKBOX query has occurred; the ledger count remains three mechanism queries.

Do not create automatic follow-on economic versions by changing probability thresholds, expected-return thresholds, entry delays, stops, costs, scales, time filters or portfolio weights against VALIDATION.

A future economic identity requires materially new execution or instrument theory, not tuning of the closed index-level next-minute / structural-boundary family.

## 7. Current next research

Automatic broad indicator generation remains paused.

The next allowed task is a results-blind unified parent-state router review using only already-certified R1/R2 features and event geometries.

The review may approve at most one low-capacity router identity. It must:

- use no new indicator family;
- introduce no scale or threshold search;
- remain a non-PnL scientific test;
- fit on DEV and require cross-lane / cross-year detailed VALIDATION stability;
- access BLACKBOX only after full VALIDATION PASS, as query #4;
- close on BLACKBOX FAIL/INSUFFICIENT without breakdown.

The router is a synthesis layer, not a new broad R8/R9 lane and not an economic rescue.

## 8. Optional future Q4 challenge

The preregistered complete-2026Q4 R1 challenge remains optional and is not the current blocker. Do not inspect partial Q4 under that protocol unless later authority explicitly changes it.

## 9. Repository hygiene

- Keep current authority concise and non-duplicative.
- Keep BLACKBOX receipts low-bandwidth.
- Do not copy BLACKBOX detail into docs, logs, charts or issues.
- Remove completed Actions workflows after bounded execution.
- Completed implementation details belong in Git history plus compact history anchors, not the active surface.
- Do not create a second active repository for this project.

Production authority remains false.
