# Overnight Open Lab — Current Index

This index is intentionally **current-first**. Historical files remain in Git and
in their original evidence paths, but they are not all active execution surfaces.

## 1. Current authority

Read these first, in order:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_program_v1.md`
3. `docs/governance/overnight_factor_product_registry_v1.json`
4. `README.md`
5. `AGENTS.md`

## 2. Active research — Opening Surprise

Identity: `overnight_open_surprise_factor_v1`

- state: `docs/governance/opening_surprise_factor_v1_state.json`
- protocol: `docs/governance/opening_surprise_factor_v1_protocol.json`
- preanalysis: `docs/research/opening_surprise_factor_preanalysis_20260910.md`
- runner: `scripts/diagnose_opening_surprise_factor_dev.py`
- one-command runner: `scripts/run_opening_surprise_factor_dev.sh`
- local handoff: `docs/ops/opening_surprise_factor_dev_handoff_20260910.md`
- expected local output: `docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`

Current detailed evidence boundary: `2019-01-01..2020-12-31` only.

## 3. Stable next-open prediction authority

### Repository-wide two-head architecture

- acceptance: `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`
- direction selected: `docs/governance/cloud_session_20260906_direction_head_selected_v1.json`
- direction 2026 receipt: `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`
- magnitude / two-head selection: `docs/governance/cloud_session_20260906_two_head_selected_v1.json`
- 2021-2025 magnitude receipt: `docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json`

Accepted architecture remains:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

### V6A global-spillover baseline

- current baseline pointer: `docs/governance/global_spillover_current_baseline_v1.json`
- baseline replacement review: `docs/governance/global_spillover_v6a_baseline_replacement_review_20260910.json`
- V6A state: `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- compact BLACKBOX receipt: `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`
- query ledger: `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`
- source admission: `docs/governance/global_spillover_v6a_source_admission_20260910.json`
- source pack: `data/v6a_external_sources_2015_2025/`

V6A is the active baseline for the global-spillover single-head signed-gap lineage
only. Its completed 2021-2025 BLACKBOX decision is `PASS`.

## 4. Gap-Fill product line

### Gap-Fill V2

Current scientific authority:

- development closeout: `docs/research/gap_fill_v2_v1_development_closeout_20260906.md`
- repeat adjudication: `docs/research/gap_fill_v2_2026_repeat_cloud_adjudication_20260906.md`
- true-fresh state: `docs/governance/gap_fill_v2_true_fresh_state_v1.json`
- true-fresh protocol: `docs/governance/cloud_session_20260906_gap_fill_v2_true_fresh_protocol_v1.json`
- true-fresh evaluator: `scripts/evaluate_gap_fill_v2_true_fresh_2026q4.py`

2026-01-05..2026-08-21 is repeat-only. The complete
2026-08-24..2026-12-31 block remains the separately gated true-fresh challenge.

### Historical extension / transport / V2.1

Key lineage:

- historical source adjudication: `docs/research/gap_fill_v2_he00_cloud_source_adjudication_20260906.md`
- transport protocol: `docs/governance/cloud_session_20260906_gap_fill_cross_index_transport_protocol_v1.json`
- CT-DEV: `docs/research/gap_fill_cross_index_ct_dev_cloud_adjudication_20260907.md`
- Audit A: `docs/research/gap_fill_cross_index_audit_a_cloud_adjudication_20260907.md`
- Audit B: `docs/research/gap_fill_cross_index_audit_b_cloud_adjudication_20260907.md`
- V21 RD1: `docs/research/gap_fill_v21_rd1_cloud_adjudication_20260907.md`
- V21 final DEV adjudication: `docs/research/gap_fill_v21_dev_cloud_adjudication_20260909.md`
- V21 current state: `docs/governance/gap_fill_v21_state_v1.json`

V21 P2 is closed at DEV with no successor. Do not reopen sealed audits or rescue
its frozen sample insufficiency.

## 5. Data surfaces

Read `data/README.md` and `docs/governance/package_scope.json`.

- `data/development/` — frozen 2015-2020 core pack
- `data/high_open_dev_2015_2025/` — CSI1000 development carrier through 2025
- `data/offshore_etf_dev_2015_2025/` — bounded offshore ETF pack
- `data/v6a_external_sources_2015_2025/` — HKMA + SGX A50 admitted pack
- `data/gap_fill_repeat_2026/` — repeat-only 2026 pack through 2026-08-21

## 6. Operations

Read `docs/ops/README.md` before executing any handoff.

Active handoff:

`docs/ops/opening_surprise_factor_dev_handoff_20260910.md`

Other handoffs are historical unless a current state file explicitly reactivates
them.

## 7. Archive

Read `archive/README.md`.

Current archived groups:

- `archive/v6a_short0935_to_close_20260910/`
- `archive/v6a_reusable_blackbox_completed_20260910/`

Archived executable files must not be treated as active work.

## 8. Governance / provenance

- repository scope restoration: `docs/governance/repository_scope_restoration_20260909.md`
- package scope: `docs/governance/package_scope.json`
- production readiness / current economic boundary: `docs/governance/cloud_session_20260906_production_readiness_review_v1.json`
- cloud-local communication history: `docs/ops/cloud_local_communication.md`

## 9. Historical closed research retained in place

The following families remain useful as evidence/history but are not the current
active task:

- high-open recall OHR-01..04;
- offshore China price-discovery OHR-05..08;
- clock-gate and early holdout investigations;
- Gap-Fill V2 development internals;
- cross-index transport internals;
- V21 diagnostic and candidate-family internals.

Do not rerun them merely because their scripts, receipts, or handoffs remain in
the repository. Their current state/adjudication files govern whether an identity
is closed, sealed, repeat-only, or active.
