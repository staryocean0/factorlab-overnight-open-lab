# Documentation index

This index describes the current worktree only. Historical experiments removed during consolidation remain available in Git history; see `docs/archive/README.md`.

## Current authority

1. `../CONTINUE_HERE.md`
2. `governance/reusable_three_role_data_policy_v1.json`
3. `governance/reversal_mean_reversion_program_state_v1.json`
4. `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
5. `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`

## Data governance

- `governance/reusable_three_role_data_policy_v1.json` — DEV 2015–2020, VALIDATION 2021–2025, reusable BLACKBOX 2026-01-05..2026-08-21.
- `governance/reusable_blackbox_query_ledger_v1.json` — append-only low-bandwidth blackbox query ledger.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Exact metrics, counts, subperiods and failure examples must never be copied into the current research surface.

## Current R1 reusable certification assets

- `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json` — DEV/VALIDATION/final-refit/blackbox contract.
- `../scripts/run_rmr_R1_reusable_dev_validation.py` — detailed DEV/VALIDATION runner; physically excludes 2026.
- `../scripts/certify_rmr_R1_reusable_blackbox.py` — low-bandwidth blackbox certifier.
- `../tests/test_reusable_three_role_blackbox.py` — role, leakage and three-state output tests.
- `research/rmr_R1_reusable_validation_adjudication_20260908.md` — detailed 2021–2025 validation evidence.
- `governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json` — final 2015–2025 fit frozen before blackbox; SHA256 `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.
- `research/rmr_R1_reusable_blackbox_certification_20260908.json` — query 1 low-bandwidth result: `PASS`.

## R1 mechanism history retained in current tree

- `governance/reversal_mean_reversion_stage1_scale_contract_v1.json`
- `governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json`
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_protocol_v1.json`
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_protocol_v1.json`
- `research/rmr_R1_parent_integrity_v2_preanalysis_20260908.md`
- `research/reversal_mean_reversion_R1_parent_integrity_v2_selection_adjudication_20260908.md`
- `research/reversal_mean_reversion_R1_parent_integrity_v2_holdout_adjudication_20260908.md`

The old 2023–2025 `holdout` label is historical. Under current repository-wide governance those years belong to reusable VALIDATION.

## Next research stage

Next identity:

`rmr_R1_parent_integrity_economic_translation_v1`

Use DEV/VALIDATION for strategy economics and implementation research. Freeze a strategy candidate before another blackbox query.

R5-C remains the secondary Priority-B mechanism:

`ops/rmr_R5C_event_density_promotion_handoff_20260908.md`

## Optional future Q4 experiment

The previously frozen complete-2026Q4 source-admission/evaluator protocols remain in `governance/` and `scripts/` as an optional future fresh challenge. They are not current next-action authority.

## Data paths

- `../data/high_open_dev_2015_2025/` — current detailed historical pool for DEV/VALIDATION.
- `../archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet` — current reusable BLACKBOX physical source; direct research inspection is prohibited by policy.

Production authority remains false.
