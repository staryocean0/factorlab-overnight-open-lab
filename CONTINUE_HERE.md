# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Current research identity

Repository-wide priority is the frozen R1 specialist:

`rmr_cross_scale_pullback_parent_integrity_v2`

Current R1 status:

`composite_1D_selected_holdout_confirmed_not_fresh_true_fresh_2026Q4_preregistered_source_admission_tooling_frozen_waiting_complete_2026_extension`

Broad Stage-1 direction discovery is closed. Automatic R8/R9-style lane generation is paused. R5-C event density remains a secondary Priority-B handoff only.

## Exact next action

Do **not** run another empirical R1 outcome test now.

The future source-admission path is already frozen. The challenge itself is `2026-10-01 .. 2026-12-31`, but the causal state must be reconstructed from a complete `2026-01-05 .. 2026-12-31` CSI1000 1m extension so October events are not initialized from an artificial quarter boundary.

Not before `2027-01-01` China time:

1. obtain the complete 2026 CSI1000 1m extension and an authoritative A-share trading calendar;
2. run `scripts/admit_rmr_R1_true_fresh_2026Q4_source.py`;
3. that runner may read only `symbol / trading_day / timestamp` and must require exact named 240-clock sessions (`09:31..11:30` + `13:01..15:00`); the legacy V21 239-clock exception does not apply;
4. cloud-review the compact admission receipt and freeze the exact source/calendar SHA values in a **new** authorization artifact;
5. source-admission PASS by itself does not authorize outcome access;
6. only after separate authorization, execute one frozen full-quarter R1 challenge without refit, candidate change, scale/threshold change or calibration;
7. require both PAIR_A and PAIR_B to meet the preregistered sample minimum and beat the frozen severity baseline on both Brier and log-loss.

Controlling files:

- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_execution_authorization_template_v1.json`

## Explicitly forbidden before that gate

- score October alone or October–November partial Q4;
- inspect partial Q4 outcome metrics;
- read OHLC during metadata-only source admission;
- truncate causal state at 2026-10-01 rather than use the frozen full-2026 context extension;
- treat source-admission PASS as outcome-execution authorization;
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
5. frozen R1 source-admission/parameter/evidence files listed in `docs/INDEX.md`

Everything else is background, reproducibility material or historical evidence. Old `next_action` fields in Git history have no repository-wide authority.

Production authority remains `false`.
