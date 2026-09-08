# AGENTS.md — repository operating rules

## 1. One canonical repository

`staryocean0/factorlab-overnight-open-lab` is the only active repository for this research project.

## 2. Current authority

Read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Historical `next_action` fields never override these files.

## 3. Reusable three-role data governance

Market history is reusable, not a one-shot consumable.

### DEV

`2015-01-05 .. 2020-12-31`

Full access for fitting, diagnosis, feature work and iteration.

### VALIDATION

`2021-01-01 .. 2025-12-31`

Reusable detailed validation. Year/event/regime diagnostics are allowed and may motivate later DEV/VALIDATION iterations.

### BLACKBOX

`2026-01-05 .. 2026-08-21`

Reusable certification only. Public output is limited to:

`PASS / FAIL / INSUFFICIENT`

Never release exact BLACKBOX metrics, counts, dates, months, regimes, event examples, probabilities, feature attribution or failure analysis.

Repeated BLACKBOX queries are allowed for separately frozen candidates, but they are not independent new OOS samples. Append every completed query to `docs/governance/reusable_blackbox_query_ledger_v1.json`.

A BLACKBOX FAIL/INSUFFICIENT returns research to DEV/VALIDATION without a breakdown.

## 4. Final-fit rule

A candidate may receive one preregistered DEV+VALIDATION final refit only after detailed VALIDATION passes. BLACKBOX may never participate in fitting, candidate selection, thresholds or feature choice.

## 5. R1 status

`rmr_cross_scale_pullback_parent_integrity_v2` is a certified mechanism.

Final mechanism bundle:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

Reusable BLACKBOX query `a9ba75c39e675ae6be17` returned `PASS`; no detail was released.

The first R1 economic-translation round is closed after three materially different low-capacity implementations all failed detailed VALIDATION before BLACKBOX. Do not create automatic v4/v5 tweaks against the same execution family. A new R1 economic identity requires genuinely new execution or instrument theory.

## 6. Current active specialist

The active research identity is:

`rmr_event_density_state_reversal_v2`  (R5-C)

Use the existing R5-C handoff and freeze a small family before empirical work. The family must test event-density information beyond nearby event geometry on both S1 and S2. Only a detailed VALIDATION PASS may authorize final refit and a low-bandwidth BLACKBOX query.

## 7. Optional future Q4 challenge

The previously preregistered complete-2026Q4 R1 challenge remains optional and is not the current blocker. Do not inspect partial Q4 under that protocol unless later authority explicitly changes it.

## 8. Repository hygiene

- Keep authority concise and non-duplicative.
- Keep BLACKBOX receipts low-bandwidth.
- Do not copy BLACKBOX detail into docs, logs, charts or issues.
- Remove completed Actions workflows after their bounded execution.
- Completed implementation details may be recovered from Git history instead of remaining as active clutter.
- Do not create a second active repository for this project.

Production authority remains false.
