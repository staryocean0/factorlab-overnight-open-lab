# Documentation index

This index describes the **current worktree only**. Historical experiments removed during consolidation remain available in Git history; see `archive/README.md`.

## Current authority

- `../CONTINUE_HERE.md` — exact next action and prohibitions.
- `governance/reversal_mean_reversion_program_state_v1.json` — repository-wide current state.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json` — R1 specialist state.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json` — next frozen true-fresh gate.

## Frozen R1 specialist assets

- `governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json` — frozen 2015–2022 parameters and model/scaler bundle.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_protocol_v1.json` — bounded representation-selection contract.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_execution_freeze_v1.json` — selection execution identity.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_protocol_v1.json` — 2023–2025 mechanism-holdout contract.
- `governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_execution_freeze_v1.json` — holdout execution identity.
- `governance/reversal_mean_reversion_stage1_scale_contract_v1.json` — causal directional-change scale definitions inherited by R1.

## Decisive R1 evidence

- `research/rmr_R1_parent_integrity_v2_preanalysis_20260908.md` — specialist hypothesis and bounded family frozen before holdout.
- `research/reversal_mean_reversion_R1_parent_integrity_v2_selection_adjudication_20260908.md` — 1D composite selected on consumed 2015–2022 evidence.
- `research/reversal_mean_reversion_R1_parent_integrity_v2_holdout_adjudication_20260908.md` — 2023–2025 no-refit mechanism-holdout PASS.

## Program-level context

- `research/reversal_mean_reversion_stage1_discovery_round_closeout_20260908.md` — why broad R8/R9-style lane creation stopped.
- `research/reversal_mean_reversion_two_promotion_program_review_20260908.md` — R1 Priority A vs R5-C Priority B review.
- `research/reversal_mean_reversion_program_whitepaper_v1.md` — conceptual framework; background, not next-action authority.
- `research/reversal_mean_reversion_literature_map_20260908.md` — literature constraints; background, not next-action authority.
- `ops/rmr_R5C_event_density_promotion_handoff_20260908.md` — secondary Priority-B mechanism queued behind R1.

## Reproduction code

The active code surface is intentionally small:

- `../scripts/run_rmr_stage1_common_probe.py` — causal directional-change/event construction used by R1.
- `../scripts/run_rmr_R1_parent_integrity_v2_selection.py` — historical representation-selection reproduction.
- `../scripts/evaluate_rmr_R1_parent_integrity_v2_holdout.py` — historical no-refit holdout reproduction.
- matching R1 tests under `../tests/`.

These scripts reproduce completed evidence; they do **not** authorize early 2026Q4 scoring. A future Q4 evaluator must be written against the frozen true-fresh protocol only after source admission is appropriate.

## Data

- `../data/high_open_dev_2015_2025/` — active frozen CSI1000 source used for R1 consumed evidence and 2023–2025 mechanism holdout.
- `../archive/data/gap_fill_repeat_2026/` — legacy repeat-only pack consolidated from the retired temporary repository; historical evidence only.

## Historical evidence

`archive/README.md` records immutable commit anchors for the large pre-consolidation tree. Old workflow/protocol/receipt files not present here remain retrievable there and have no current authority.
