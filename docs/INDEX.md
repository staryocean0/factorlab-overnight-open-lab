# Documentation index

This index describes the current worktree only. Historical implementation details remain recoverable from Git history.

## Current authority

1. `../CONTINUE_HERE.md`
2. `governance/reusable_three_role_data_policy_v1.json`
3. `governance/reversal_mean_reversion_program_state_v1.json`
4. this index

## Reusable data governance

- `governance/reusable_three_role_data_policy_v1.json` — DEV 2015–2020, VALIDATION 2021–2025, reusable BLACKBOX 2026-01-05..2026-08-21.
- `governance/reusable_blackbox_query_ledger_v1.json` — append-only BLACKBOX ledger; current count = **3**.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Exact metrics, counts, subperiods and failure examples must never be copied into the current research surface.

## Certified mechanism 1 — R1 trend-parent pullback recovery

- `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
- `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
- `governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json` — final bundle `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.
- `research/rmr_R1_reusable_validation_adjudication_20260908.md`
- `research/rmr_R1_reusable_blackbox_certification_20260908.json` — BLACKBOX query #1: `PASS`.
- `research/rmr_R1_economic_translation_round_closeout_20260908.md` — tested R1 economic family failed VALIDATION before BLACKBOX.
- `archive/rmr_R1_economic_translation_round_history_anchor_20260908.md` — implementation-history anchor.

## Certified mechanism 2 — R2 range-parent boundary re-entry

- `governance/reversal_mean_reversion_R2_state_v1.json`
- `governance/reversal_mean_reversion_R2_range_integrity_v2_protocol.json` — dedicated geometry-baseline + range-integrity contract.
- `governance/rmr_R2_range_integrity_v2_parameter_freeze.json` — final bundle `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.
- `research/rmr_R2_range_integrity_v2_validation_adjudication_20260908.md`
- `research/rmr_R2_range_integrity_v2_blackbox_certification_20260908.json` — BLACKBOX query #3: `PASS`.
- `research/rmr_R2_economic_translation_v1_closeout_20260908.md` — economic v1 failed detailed VALIDATION; no query #4.
- `archive/rmr_R2_range_integrity_and_economic_v1_history_anchor_20260908.md` — full R2 execution-history anchor.

## Closed specialist — R5-C

- `governance/reversal_mean_reversion_R5C_state_v1.json`
- `research/rmr_R5C_reusable_validation_adjudication_20260908.md`
- `research/rmr_R5C_reusable_blackbox_certification_20260908.json` — BLACKBOX query #2: `FAIL`.
- `research/rmr_R5C_reusable_closeout_20260908.md`
- `archive/rmr_R5C_v2_history_anchor_20260908.md`

## Current synthesis / next research

- `research/rmr_R1_R2_certified_mechanism_synthesis_20260908.md` — R1/R2 as complementary trend-like and range-like parent normal-state mechanisms.
- `research/rmr_R2_dedicated_program_review_20260908.md` — historical review that authorized the now-certified R2 dedicated identity.

Next task: write and freeze at most one low-capacity unified parent-state router identity using only certified R1/R2 features and event geometries. It must remain non-economic and must pass detailed VALIDATION before any possible BLACKBOX query #4.

## Core reusable code/data

- `../scripts/run_rmr_stage1_common_probe.py` — causal directional-change engine and original R1/R2 event geometry.
- `../scripts/run_rmr_R1_reusable_dev_validation.py` and `../scripts/certify_rmr_R1_reusable_blackbox.py` — retained R1 mechanism reproduction path.
- `../tests/test_reusable_three_role_blackbox.py` — permanent role/leakage/ledger boundary tests.
- `../data/high_open_dev_2015_2025/` — detailed DEV/VALIDATION historical source.
- `../archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet` — reusable BLACKBOX physical source; direct research inspection prohibited.

Completed R2 execution code is intentionally absent from the current surface and recoverable from the R2 history anchor.

Production authority remains false.
