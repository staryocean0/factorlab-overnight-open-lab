# AGENTS.md — repository operating rules

## 1. One project, one canonical repository

`staryocean0/factorlab-overnight-open-lab` is the only active repository for this research project.

## 2. Current authority

Read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
5. `docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
6. `docs/INDEX.md`

Old reserve/holdout/fresh `next_action` statements are historical evidence only when they conflict with this authority.

## 3. Reusable three-role data governance

Market history is a reusable research asset, not a one-shot consumable.

### DEV

`2015-01-05 .. 2020-12-31`

Full access. Fit, diagnose, engineer, ablate and iterate here.

### VALIDATION

`2021-01-01 .. 2025-12-31`

Reusable detailed validation. It may be inspected by year/event/regime and may support later development iterations. A validation use does not consume these rows forever.

### BLACKBOX

`2026-01-05 .. 2026-08-21`

Reusable final certification. Current research must access it only through a frozen blackbox validator. Public scientific output is restricted to:

`PASS / FAIL / INSUFFICIENT`

Do not release exact blackbox metrics, counts, dates, months, regimes, event examples, probabilities, feature attribution or error analysis.

A blackbox query does not consume the data. However repeated queries are **not independent new OOS samples**. Log every query in `docs/governance/reusable_blackbox_query_ledger_v1.json`.

After a blackbox FAIL, return to DEV/VALIDATION. Any changed feature, threshold, rule or model must be justified from DEV/VALIDATION, never from blackbox details.

## 4. Final-fit rule

A candidate may be refit once on DEV+VALIDATION before blackbox only when its structure and exact fit recipe were frozen beforehand. The blackbox may never participate in fitting.

## 5. Current R1 status

`rmr_cross_scale_pullback_parent_integrity_v2` / `R1_PARENT_COMPOSITE_1D` passed reusable validation and the first reusable blackbox certification.

Current final parameter bundle SHA256:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

Blackbox query `a9ba75c39e675ae6be17` returned `PASS`; no blackbox details were released.

The next research identity is `rmr_R1_parent_integrity_economic_translation_v1`. Economic/PnL research is allowed on DEV/VALIDATION only. A second blackbox query requires a newly frozen strategy candidate and gates.

## 6. Optional future Q4 challenge

The old complete-2026Q4 true-fresh protocol remains a valid optional future experiment. It is not the repository-wide blocker. Do not inspect partial Q4 under that protocol unless later authority explicitly changes it.

## 7. Repository hygiene

- Keep current authority concise and non-duplicative.
- Keep blackbox receipts low-bandwidth.
- Do not copy blackbox details into docs, logs, charts or issue comments.
- Completed workflows should be removed after their bounded execution; immutable evidence remains in Git history.
- Do not create a second active repository for this project.

Production authority remains false.
