# Documentation index

This index describes the current worktree only. Historical implementation details remain recoverable from Git history.

## Current authority

1. `../CONTINUE_HERE.md`
2. `governance/reusable_three_role_data_policy_v1.json`
3. `governance/reversal_mean_reversion_program_state_v1.json`
4. this index

## Reusable data governance

- `governance/reusable_three_role_data_policy_v1.json` — DEV 2015–2020, VALIDATION 2021–2025, reusable BLACKBOX 2026-01-05..2026-08-21.
- `governance/reusable_blackbox_query_ledger_v1.json` — append-only BLACKBOX query ledger; current count = 2.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Exact metrics, counts, subperiods and failure examples must never be copied into the current research surface.

## R1 certified mechanism

- `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json` — current R1 mechanism state.
- `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json` — reusable R1 certification contract.
- `governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json` — final 2015–2025 fit; bundle SHA256 `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.
- `research/rmr_R1_reusable_validation_adjudication_20260908.md` — detailed VALIDATION PASS.
- `research/rmr_R1_reusable_blackbox_certification_20260908.json` — BLACKBOX query #1: `PASS`.
- `research/rmr_R1_economic_translation_round_closeout_20260908.md` — v1/v2/v3 economic implementations failed VALIDATION before BLACKBOX.
- `archive/rmr_R1_economic_translation_round_history_anchor_20260908.md` — full economic implementation history anchor.

## R5-C closed specialist

- `governance/reversal_mean_reversion_R5C_state_v1.json` — dedicated VALIDATION PASS / BLACKBOX FAIL / identity closed.
- `research/rmr_R5C_reusable_validation_adjudication_20260908.md` — detailed 2021–2025 evidence.
- `research/rmr_R5C_reusable_blackbox_certification_20260908.json` — BLACKBOX query #2: `FAIL`, no detail released.
- `research/rmr_R5C_reusable_closeout_20260908.md` — controlling closeout.
- `archive/rmr_R5C_v2_history_anchor_20260908.md` — full protocol/runner/tests/freeze/workflow history anchor.

## Next active research

Program review:

`research/rmr_R2_dedicated_program_review_20260908.md`

Approved identity:

`rmr_range_boundary_parent_integrity_v2`

Frozen scientific direction before execution:

- original broad R2 re-entry-vs-continuation event geometry;
- baseline `outside_ratio + break_speed + local_vol_ratio`;
- only added feature `range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff))/3`;
- S1-outside-S2 and S2-outside-S3 co-primary;
- DEV/VALIDATION first; BLACKBOX only after both-scale VALIDATION PASS.

## Core reusable code/data

- `../scripts/run_rmr_stage1_common_probe.py` — causal directional-change engine and original R1/R2 event geometry.
- `../scripts/run_rmr_R1_reusable_dev_validation.py` and `../scripts/certify_rmr_R1_reusable_blackbox.py` — retained because R1 remains the certified active mechanism.
- `../tests/test_reusable_three_role_blackbox.py` — permanent role/leakage/ledger boundary tests.
- `../data/high_open_dev_2015_2025/` — detailed DEV/VALIDATION historical source.
- `../archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet` — reusable BLACKBOX physical source; direct research inspection prohibited.

Production authority remains false.
