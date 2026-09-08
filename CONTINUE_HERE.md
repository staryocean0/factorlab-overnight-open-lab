# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Current research identity

Repository-wide priority is the frozen R1 specialist:

`rmr_cross_scale_pullback_parent_integrity_v2`

Current R1 status:

`composite_1D_selected_holdout_confirmed_not_fresh_true_fresh_2026Q4_preregistered_source_admission_and_evaluator_frozen_waiting_complete_2026_extension`

Broad Stage-1 direction discovery is closed. Automatic R8/R9-style lane generation is paused. R5-C event density remains a secondary Priority-B handoff only.

## Exact next action

Do **not** write or run another empirical R1 model now. The future execution path is already frozen end-to-end.

The fresh challenge is `2026-10-01 .. 2026-12-31`, while causal state reconstruction uses the complete `2026-01-05 .. 2026-12-31` CSI1000 1m extension so October events are not initialized from an artificial quarter boundary.

Not before `2027-01-01` China time:

1. obtain the complete 2026 CSI1000 1m extension and an authoritative A-share trading calendar;
2. run the frozen metadata-only source gate: `scripts/admit_rmr_R1_true_fresh_2026Q4_source.py`;
3. the source gate may read only `symbol / trading_day / timestamp` and requires exact named 240-clock sessions (`09:31..11:30` + `13:01..15:00`); the legacy V21 239-clock exception does not apply;
4. cloud-review the compact admission receipt;
5. only if admission passes, create a **new concrete** execution authorization from the frozen template, binding source SHA, calendar SHA, receipt SHA and evaluator blob SHA;
6. source-admission PASS alone does not authorize outcome access;
7. after concrete authorization, run the already-frozen evaluator exactly once: `scripts/evaluate_rmr_R1_true_fresh_2026Q4.py`;
8. do not refit, change candidate, change scale/threshold, calibrate, or read post-2026-12-31 prices;
9. PAIR_A and PAIR_B must each meet their sample minimum and beat the frozen severity baseline on both Brier and log-loss.

Frozen files:

- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_execution_freeze_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_execution_freeze_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_execution_authorization_template_v1.json`

## Explicitly forbidden before that gate

- score October alone or October–November partial Q4;
- inspect partial Q4 outcome metrics;
- read OHLC during metadata-only source admission;
- truncate causal state at 2026-10-01;
- treat source-admission PASS as outcome-execution authorization;
- modify the frozen Q4 evaluator after source inspection;
- use 2027Q1 prices to resolve late-Q4 events;
- refit or alter the frozen R1 parameters;
- change the parent-integrity formula, severity definition, scale pairings or first-passage boundaries;
- optimize entry, stop, holding period, trading return or PnL;
- reopen closed R2/R3/R4/R5-A/R5-B/R6/R7 identities to rescue them;
- create new broad indicator lanes merely because no work is currently executable.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_state_v1.json`
3. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json`
5. frozen R1 source/evaluator/parameter/evidence files listed in `docs/INDEX.md`

Everything else is background, reproducibility material or historical evidence. Old `next_action` fields in Git history have no repository-wide authority.

Production authority remains `false`.
