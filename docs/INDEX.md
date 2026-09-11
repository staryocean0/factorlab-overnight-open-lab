# Overnight Open Lab — Current Index

This index is intentionally **current-first**. Historical evidence remains in Git, but only files referenced by current authority/state are active execution surfaces.

## 1. Current authority

Read these first:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_program_v1.md`
3. `docs/governance/overnight_factor_product_registry_v1.json`
4. `README.md`
5. `AGENTS.md`

## 2. Active research — Trend-conditioned opening state

Identity:

`overnight_trend_conditioned_open_state_v1`

- state: `docs/governance/trend_conditioned_open_state_v1_state.json`
- protocol: `docs/governance/trend_conditioned_open_state_v1_protocol.json`
- preanalysis: `docs/research/trend_conditioned_open_state_preanalysis_20260911.md`
- runner: `scripts/diagnose_trend_conditioned_open_state_dev.py`
- one-command runner: `scripts/run_trend_conditioned_open_state_dev.sh`
- local handoff: `docs/ops/trend_conditioned_open_state_dev_handoff_20260911.md`
- expected receipt: `docs/research/local_trend_conditioned_open_state_dev_diagnostic_v1.json`

Detailed evidence boundary: `2019-01-01..2020-12-31` only.

No categorical trend buckets, alternate lookbacks/horizons, Opening Surprise rescue terms, strategy PnL, detailed 2021-2025 outcomes, or 2026 outcomes are authorized.

## 3. Recently closed — Opening Surprise

Identity:

`overnight_open_surprise_factor_v1`

Decision:

`NO_STANDALONE_OPENING_SURPRISE_PRODUCT_PROMOTION_STABILITY_FAILURE`

Evidence:

- local receipt: `docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`
- cloud adjudication: `docs/research/opening_surprise_factor_cloud_adjudication_20260911.md`
- state: `docs/governance/opening_surprise_factor_v1_state.json`

No 2021-2025 BLACKBOX was opened for A3. Execution entrypoints are archived under `archive/opening_surprise_completed_20260911/`.

## 4. Stable next-open prediction authority

### Repository-wide two-head architecture

Accepted architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

Key authority:

- `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`
- `docs/governance/cloud_session_20260906_direction_head_selected_v1.json`
- `docs/governance/cloud_session_20260906_two_head_selected_v1.json`

### V6A global-spillover baseline

Current single-head signed-gap baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX decision is `PASS`.

Key authority:

- `docs/governance/global_spillover_current_baseline_v1.json`
- `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`
- `docs/governance/overnight_reusable_blackbox_policy_v1.json`
- `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`
- `docs/governance/global_spillover_v6a_source_admission_20260910.json`

## 5. Gap-Fill product line

### Gap-Fill V2

- development closeout: `docs/research/gap_fill_v2_v1_development_closeout_20260906.md`
- repeat adjudication: `docs/research/gap_fill_v2_2026_repeat_cloud_adjudication_20260906.md`
- true-fresh state: `docs/governance/gap_fill_v2_true_fresh_state_v1.json`
- true-fresh protocol: `docs/governance/cloud_session_20260906_gap_fill_v2_true_fresh_protocol_v1.json`

2026-01-05..2026-08-21 is repeat-only. The complete 2026-08-24..2026-12-31 block remains the separately gated true-fresh challenge.

### V2.1 P2 successor

Current state:

`docs/governance/gap_fill_v21_state_v1.json`

Closed at DEV with no successor because the frozen per-year sample gate was insufficient. Do not rescue it or open sealed audits.

## 6. Data surfaces

Read:

- `data/README.md`
- `docs/governance/package_scope.json`

Main packs:

- `data/development/` — frozen 2015-2020 core pack
- `data/high_open_dev_2015_2025/` — CSI1000 carrier through 2025
- `data/offshore_etf_dev_2015_2025/` — bounded offshore ETF pack
- `data/v6a_external_sources_2015_2025/` — HKMA + SGX A50 admitted pack
- `data/gap_fill_repeat_2026/` — repeat-only pack through 2026-08-21

Physical data presence does not grant evidence authority.

## 7. Operations

Read `docs/ops/README.md` before executing any handoff.

Current active handoff:

`docs/ops/trend_conditioned_open_state_dev_handoff_20260911.md`

## 8. Archive

Read `archive/README.md`.

Current groups:

- `archive/v6a_short0935_to_close_20260910/`
- `archive/v6a_reusable_blackbox_completed_20260910/`
- `archive/opening_surprise_completed_20260911/`

Archived executable files are provenance, not active work.

## 9. Historical closed research retained in place

Useful historical families that are not current execution tasks include:

- high-open recall OHR-01..04;
- offshore China price-discovery OHR-05..08;
- clock-gate / early holdout investigations;
- Gap-Fill V2 development internals;
- cross-index transport internals;
- V21 diagnostic / candidate-family internals.

Do not rerun them merely because their scripts, receipts, or handoffs remain in repository history.
