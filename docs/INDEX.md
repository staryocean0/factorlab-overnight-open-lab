# Overnight Open Lab — Current Index

This index is intentionally **current-first**. Historical evidence remains in Git, but only files referenced by current authority/state are active execution surfaces.

## 1. Current authority

Read these first:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_program_v1.md`
3. `docs/governance/overnight_factor_product_registry_v1.json`
4. `README.md`
5. `AGENTS.md`

## 2. Active research — C2 60m volatility-conditioned opening state

Identity:

`overnight_volatility_conditioned_open_state_60m_v1`

- state: `docs/governance/volatility_conditioned_open_state_60m_state_v1.json`
- BLACKBOX protocol: `docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json`
- controller: `scripts/run_volatility_conditioned_open_state_60m_blackbox_local.py`
- one-command runner: `scripts/run_volatility_conditioned_open_state_60m_blackbox.sh`
- local handoff: `docs/ops/volatility_conditioned_open_state_60m_blackbox_handoff_20260911.md`
- expected compact receipt: `docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`
- query ledger: `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`

Public scientific output is restricted to `PASS / FAIL / INSUFFICIENT`.

Frozen candidate:

`observed_gap_rvol * log(rvol20)`

Validated C1 baseline control:

`trend20_rvol * observed_gap_rvol`

Frozen target:

`09:35 -> 10:35`

No volatility buckets, alternate volatility lookbacks/horizons, Opening Surprise rescue, strategy PnL, or detailed 2021-2025 output are authorized.

## 3. Completed C2 DEV parent

Parent identity:

`overnight_volatility_conditioned_open_state_v1`

Decision:

`C2_DEV_PROGRESS_60M_CONTINUOUS_COORDINATE_ONLY`

Evidence:

- cloud receipt: `docs/research/cloud_volatility_conditioned_open_state_dev_diagnostic_v1.json`
- cloud adjudication: `docs/research/volatility_conditioned_open_state_dev_cloud_adjudication_20260911.md`
- parent state: `docs/governance/volatility_conditioned_open_state_v1_state.json`
- preanalysis: `docs/research/volatility_conditioned_open_state_preanalysis_20260911.md`

The 15-minute C2 interaction failed cross-year stability. The 30-minute interaction was directionally stable but too weak/uneven for progression. The 60-minute interaction was the only supported successor.

## 4. Validated C1 trend-context product

Identity:

`overnight_trend_conditioned_open_state_15m_v1`

Status:

`BLACKBOX_PASS_promoted_validated_15m_continuous_factor_product`

Evidence:

- DEV adjudication: `docs/research/trend_conditioned_open_state_dev_cloud_adjudication_20260911.md`
- compact BLACKBOX receipt: `docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`
- BLACKBOX adjudication: `docs/research/trend_conditioned_open_state_15m_blackbox_cloud_adjudication_20260911.md`
- state: `docs/governance/trend_conditioned_open_state_15m_state_v1.json`

C1 authority is continuous and 15-minute only. It does not authorize categorical `up/range/down × high/low open` products.

## 5. Closed Opening Surprise

`overnight_open_surprise_factor_v1` is closed after DEV stability failure. No 2021-2025 BLACKBOX was opened for A3.

Evidence:

- `docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`
- `docs/research/opening_surprise_factor_cloud_adjudication_20260911.md`
- `docs/governance/opening_surprise_factor_v1_state.json`

## 6. Stable next-open prediction authority

Repository-wide architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

Global-spillover single-head baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX decision is `PASS`.

Key authority:

- `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`
- `docs/governance/global_spillover_current_baseline_v1.json`
- `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`

## 7. Gap-Fill product line

Gap-Fill V2 remains frozen/repeat-confirmed. The complete `2026-08-24..2026-12-31` block is its separately gated true-fresh challenge.

V21 P2 remains closed at DEV with no successor because the frozen per-year sample gate was insufficient.

Key state files:

- `docs/governance/gap_fill_v2_true_fresh_state_v1.json`
- `docs/governance/gap_fill_v21_state_v1.json`

## 8. Data surfaces

Read:

- `data/README.md`
- `docs/governance/package_scope.json`

Main packs:

- `data/development/` — frozen 2015-2020 core pack plus bounded connector-readable 2019-2020 text carrier
- `data/runtime_text_2015_2025/` — yearly connector-readable runtime carrier; only 2015-2020 shards are published. Not a new scientific dataset and not a 2021-2025 BLACKBOX export.
- `data/high_open_dev_2015_2025/` — CSI1000 carrier through 2025; detailed 2021-2025 use remains BLACKBOX-governed where applicable
- `data/offshore_etf_dev_2015_2025/` — bounded offshore ETF pack
- `data/v6a_external_sources_2015_2025/` — HKMA + SGX A50 admitted pack
- `data/gap_fill_repeat_2026/` — repeat-only pack through 2026-08-21

Physical data presence does not grant evidence authority.

## 9. Operations and archive

Read `docs/ops/README.md` before executing any handoff.

Active handoff:

`docs/ops/volatility_conditioned_open_state_60m_blackbox_handoff_20260911.md`

Closed/completed executable entrypoints may be retained under `archive/`. Historical files elsewhere are not automatically active. `docs/governance/current_authority_v1.json` is the canonical pointer.
