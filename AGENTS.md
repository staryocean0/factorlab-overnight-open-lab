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

## 5. Current evidence

### R1

`rmr_cross_scale_pullback_parent_integrity_v2` is the only currently certified mechanism.

BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`.

The first R1 economic-translation round is closed after three materially different low-capacity implementations all failed detailed VALIDATION before BLACKBOX. Do not create automatic v4/v5 tweaks against the same execution family.

### R5-C

`rmr_event_density_state_reversal_v2` passed detailed dedicated VALIDATION but BLACKBOX query #2 `4fa9bfa2ec38f16cd65f` returned `FAIL`.

No BLACKBOX detail was released. R5-C v2 is closed; do not choose a scale, density window, z threshold, interaction or rescue feature from hidden recent behavior.

## 6. Current active specialist

One bounded dedicated R2 successor has been approved:

`rmr_range_boundary_parent_integrity_v2`

Scientific question:

> Does parent-range integrity add re-entry probability information beyond attempted-breakout geometry, speed and local volatility?

Dedicated baseline:

`outside_ratio + break_speed + local_vol_ratio`

Only added feature:

`range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff)) / 3`

S1-outside-S2 and S2-outside-S3 are co-primary. Use the original broad R2 event/outcome geometry. No threshold, scale, speed-window, vol-window, interaction or PnL search.

Both scales must pass detailed VALIDATION before any BLACKBOX query #3. A BLACKBOX FAIL/INSUFFICIENT closes R2 v2 and does not authorize automatic R2 v3.

## 7. Optional future Q4 challenge

The preregistered complete-2026Q4 R1 challenge remains optional and is not the current blocker. Do not inspect partial Q4 under that protocol unless later authority explicitly changes it.

## 8. Repository hygiene

- Keep current authority concise and non-duplicative.
- Keep BLACKBOX receipts low-bandwidth.
- Do not copy BLACKBOX detail into docs, logs, charts or issues.
- Remove completed Actions workflows after bounded execution.
- Completed implementation details belong in Git history plus compact history anchors, not the active surface.
- Do not create a second active repository for this project.

Production authority remains false.
