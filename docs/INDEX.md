# Documentation index

This index describes the current worktree only. Historical implementation details remain recoverable from Git history and compact history anchors.

## Current authority

1. `../CONTINUE_HERE.md`
2. `governance/reusable_three_role_data_policy_v1.json`
3. `governance/reversal_mean_reversion_program_state_v1.json`
4. `research/rmr_payoff_object_instrument_theory_review_v1.md`
5. this index

## Reusable data governance

- `governance/reusable_three_role_data_policy_v1.json` — DEV 2015–2020, VALIDATION 2021–2025, reusable BLACKBOX 2026-01-05..2026-08-21.
- `governance/reusable_blackbox_query_ledger_v1.json` — append-only ledger; completed query count = **3**.

BLACKBOX output is restricted to `PASS / FAIL / INSUFFICIENT`. Exact hidden metrics, counts, dates, subperiods, events, probabilities, attribution and failure examples must not enter the research surface.

## Certified mechanism 1 — R1 trend-parent pullback recovery

- `governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
- `governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
- `governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json` — final bundle `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.
- `research/rmr_R1_reusable_validation_adjudication_20260908.md`
- `research/rmr_R1_reusable_blackbox_certification_20260908.json` — BLACKBOX query #1: `PASS`.
- `research/rmr_R1_economic_translation_round_closeout_20260908.md`.
- `archive/rmr_R1_economic_translation_round_history_anchor_20260908.md`.

## Certified mechanism 2 — R2 range-parent boundary re-entry

- `governance/reversal_mean_reversion_R2_state_v1.json`
- `governance/reversal_mean_reversion_R2_range_integrity_v2_protocol.json`
- `governance/rmr_R2_range_integrity_v2_parameter_freeze.json` — final bundle `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.
- `research/rmr_R2_range_integrity_v2_validation_adjudication_20260908.md`
- `research/rmr_R2_range_integrity_v2_blackbox_certification_20260908.json` — BLACKBOX query #3: `PASS`.
- `research/rmr_R2_economic_translation_v1_closeout_20260908.md`.
- `archive/rmr_R2_range_integrity_and_economic_v1_history_anchor_20260908.md`.

## Closed specialist — R5-C

- `governance/reversal_mean_reversion_R5C_state_v1.json`
- `research/rmr_R5C_reusable_validation_adjudication_20260908.md`
- `research/rmr_R5C_reusable_blackbox_certification_20260908.json` — BLACKBOX query #2: `FAIL`.
- `research/rmr_R5C_reusable_closeout_20260908.md`
- `archive/rmr_R5C_v2_history_anchor_20260908.md`

## Closed unified router

- `research/rmr_R1_R2_certified_mechanism_synthesis_20260908.md`
- `research/rmr_unified_parent_state_router_program_review_20260908.md`
- `research/rmr_unified_parent_state_router_v1_validation_adjudication_20260908.md`
- `research/rmr_unified_parent_state_router_v1_closeout_20260908.md`
- `archive/rmr_unified_parent_state_router_v1_history_anchor_20260908.md`

The corrected router worsened both R2 cells, so the tested common standardized state-consistency axis is closed. No router BLACKBOX query occurred. The historical router branch is behind `main` and has no commits ahead, so it is historical only and requires no merge.

## Mechanism → execution diagnostic — complete

- `research/rmr_mechanism_to_execution_diagnostic_v1_adjudication_20260908.md`
- `research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json`
- `archive/rmr_mechanism_to_execution_diagnostic_v1_history_anchor_20260908.md`

Conclusion: payoff geometry is the primary bridge failure; probability is not a monotonic realized-return score; R1_A and R2 current simple index execution are closed; R1_B delayed markouts justified one separate temporal theory test only.

The current `main` surface no longer carries the one-time diagnostic runner, diagnostic/router-specific tests, or completed Actions workflows. Reproduction is preserved by decisive receipts, adjudications, history anchors and Git history.

## R1_B temporal impulse completion v1 — closed on DEV

- `research/rmr_R1B_temporal_execution_theory_program_review_20260908.md` — results-blind theory review that authorized the single candidate.
- `research/rmr_R1B_temporal_impulse_completion_DEV_adjudication_20260908.md` — decisive DEV closeout.
- `research/rmr_R1B_temporal_impulse_completion_DEV_decisive_receipt_20260908.json` — compact DEV evidence.
- `archive/rmr_R1B_temporal_impulse_completion_v1_history_anchor_20260908.md` — execution commit/run/artifact and removed implementation surface.

The candidate used next-bar entry and the first subsequent parent-aligned S2 **confirmation close** as temporal completion, with original S3 failure, 10bp cost and 1200-bar safety cap unchanged.

DEV on 682 tradeable events produced mean net `+10.59bp` and positive mean net in `5/6` years, but median net `-32.11bp` and win rate `37.10%`. The predeclared positive-median gate failed, so the identity closed before VALIDATION.

No temporal v2 rescue, horizon selection, probability filtering or noncausal S2-extreme exit is authorized from this result.

## Payoff-object / instrument-theory review — current boundary

- `research/rmr_payoff_object_instrument_theory_review_v1.md` — completed results-blind boundary review and current stage-specific authority.

This review does **not** authorize an empirical candidate. It leaves three theory-level outcomes only:

- materially independent execution-timing theory;
- instrument mapping after a frozen instrument-specific source and cost-model contract;
- stop economic translation.

No DEV, VALIDATION or BLACKBOX execution is authorized for a new economic identity by this review alone.

## Current next research

There is currently **no empirical economic candidate authorized**.

A new economic identity may be opened only after a materially independent payoff/instrument theory is separately preregistered and authorized. Any ETF/futures/options mapping must first freeze an instrument-specific source and cost-model contract covering spread, basis, carry, liquidity, convexity/premium and execution conventions.

Broad R8/R9 indicator discovery remains paused. BLACKBOX query count remains 3; no query #4 exists.

## Core reusable code/data

- `../scripts/run_rmr_stage1_common_probe.py` — causal directional-change engine and original R1/R2 event geometry.
- `../scripts/run_rmr_R1_reusable_dev_validation.py` and `../scripts/certify_rmr_R1_reusable_blackbox.py` — retained R1 mechanism reproduction path.
- `../tests/test_reusable_three_role_blackbox.py` — permanent role/leakage/ledger boundary tests.
- `../data/high_open_dev_2015_2025/` — detailed DEV/VALIDATION historical source.
- `../archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet` — reusable BLACKBOX physical source; direct research inspection prohibited.

Production authority remains `false`.
