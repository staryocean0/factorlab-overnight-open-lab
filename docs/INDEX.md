# Documentation index

This index describes the current worktree only. Historical implementation details remain recoverable from Git history and compact history anchors.

## Current authority

1. `../CONTINUE_HERE.md`
2. `governance/reusable_three_role_data_policy_v1.json`
3. `governance/reversal_mean_reversion_program_state_v1.json`
4. this index

## Reusable data governance

- `governance/reusable_three_role_data_policy_v1.json` — DEV 2015–2020, VALIDATION 2021–2025, reusable BLACKBOX 2026-01-05..2026-08-21.
- `governance/reusable_blackbox_query_ledger_v1.json` — append-only BLACKBOX ledger; current completed count = **3**.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Exact metrics, counts, dates, subperiods, events, probabilities, attribution and failure examples must never enter the research surface.

## Certified mechanism 1 — R1 trend-parent pullback recovery

- `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
- `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
- `governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json` — final bundle `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.
- `research/rmr_R1_reusable_validation_adjudication_20260908.md`
- `research/rmr_R1_reusable_blackbox_certification_20260908.json` — BLACKBOX query #1: `PASS`.
- `research/rmr_R1_economic_translation_round_closeout_20260908.md` — tested simple R1 economic family failed VALIDATION before BLACKBOX.
- `archive/rmr_R1_economic_translation_round_history_anchor_20260908.md`.

## Certified mechanism 2 — R2 range-parent boundary re-entry

- `governance/reversal_mean_reversion_R2_state_v1.json`
- `governance/reversal_mean_reversion_R2_range_integrity_v2_protocol.json`
- `governance/rmr_R2_range_integrity_v2_parameter_freeze.json` — final bundle `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.
- `research/rmr_R2_range_integrity_v2_validation_adjudication_20260908.md`
- `research/rmr_R2_range_integrity_v2_blackbox_certification_20260908.json` — BLACKBOX query #3: `PASS`.
- `research/rmr_R2_economic_translation_v1_closeout_20260908.md` — economic v1 failed detailed VALIDATION; no query #4.
- `archive/rmr_R2_range_integrity_and_economic_v1_history_anchor_20260908.md`.

## Closed specialist — R5-C

- `governance/reversal_mean_reversion_R5C_state_v1.json`
- `research/rmr_R5C_reusable_validation_adjudication_20260908.md`
- `research/rmr_R5C_reusable_blackbox_certification_20260908.json` — BLACKBOX query #2: `FAIL`.
- `research/rmr_R5C_reusable_closeout_20260908.md`
- `archive/rmr_R5C_v2_history_anchor_20260908.md`

## R1 / R2 synthesis and closed unified router

- `research/rmr_R1_R2_certified_mechanism_synthesis_20260908.md` — certified trend-like and range-like parent normal-state synthesis.
- `research/rmr_unified_parent_state_router_program_review_20260908.md` — results-blind router review.
- `research/rmr_unified_parent_state_router_v1_validation_adjudication_20260908.md` — corrected VALIDATION result; R2 lane worsened.
- `research/rmr_unified_parent_state_router_v1_closeout_20260908.md` — router v1 closed with no BLACKBOX query.
- `archive/rmr_unified_parent_state_router_v1_history_anchor_20260908.md` — full implementation/history anchor, including execution commit `d3ffab43c9e2d7ad4f644a81e3d15d0628686811`.

The router result means R1/R2 are conceptually complementary but are not supported as one common standardized state-consistency axis. No router v2 rescue is authorized.

## Mechanism → execution diagnostic — complete

- `research/rmr_mechanism_to_execution_diagnostic_v1_adjudication_20260908.md` — quantitative explanation of mechanism PASS versus current execution FAIL and program decision.
- `research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json` — compact decisive DEV/VALIDATION evidence with all frozen markout horizons and annual VALIDATION summaries.
- `archive/rmr_mechanism_to_execution_diagnostic_v1_history_anchor_20260908.md` — exact runner/tests/workflow/preanalysis execution anchor; authoritative Actions run `34226850838` at `f35f64dcb567b681f583ae16881226c6ca738784`.

The completed diagnostic runner, tests, workflow and preanalysis have been removed from current surface after successful execution. The full implementation remains recoverable from Git history.

Diagnostic conclusion:

- payoff geometry is the primary bridge failure;
- probability is not a monotonic realized-return score;
- R1_A and R2 current simple index-level economic families are closed;
- R1_B delayed markout term structure motivates only a new results-blind temporal execution theory review;
- instrument mapping was not selected by this diagnostic;
- BLACKBOX query count remains 3; no query #4 exists.

## Current next research

Next task: write a results-blind **R1_B temporal execution theory program review**. It may authorize at most one materially new temporal identity and must not select a markout horizon, threshold, entry delay, stop, target, cost, scale, year/regime or time-of-day using the completed diagnostic.

The immediate review and subsequent DEV/VALIDATION work have **no BLACKBOX authority**. Broad R8/R9 indicator discovery remains paused.

## Core reusable code/data

- `../scripts/run_rmr_stage1_common_probe.py` — causal directional-change engine and original R1/R2 event geometry.
- `../scripts/run_rmr_R1_reusable_dev_validation.py` and `../scripts/certify_rmr_R1_reusable_blackbox.py` — retained R1 mechanism reproduction path.
- `../tests/test_reusable_three_role_blackbox.py` — permanent role/leakage/ledger boundary tests.
- `../data/high_open_dev_2015_2025/` — detailed DEV/VALIDATION historical source.
- `../archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet` — reusable BLACKBOX physical source; direct research inspection prohibited.

Production authority remains `false`.
