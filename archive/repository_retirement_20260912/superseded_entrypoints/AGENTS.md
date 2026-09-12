# Overnight Open Lab — agent instructions

This repository is the **Overnight/Open factor-product laboratory and downstream factor adapter** for FactorLab.

Before doing anything substantial, read in this order:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_registry_v1.json`
3. the active identity's state + protocol, if `active_research` is non-null
4. `docs/ops/README.md`

For any model, factor-family, routing, strategy, robustness, account, or cross-period change, also follow `.codex/skills/strategy-slice-rebuild/SKILL.md`.

`production_authority=false`.

## Scope

In scope: expected/observed China opening state, gap normalization, Gap-Fill hazards, global/offshore/FX Overnight drivers, causal trend/volatility/session-shape context, relative-index opening leadership, and separately frozen downstream adapters.

Out of scope: generic reversal/RMR, broad HighVol routing unrelated to Overnight/Open, two-wave logic, using downstream PnL to tune upstream factors, pretending the cash index is directly tradable, manufacturing stock-specific alpha from market-level factors, or production deployment.

## Current execution state

There is **no active research identity** after the completed E1 reusable validation.

Most recent completed identity:

`overnight_c1_b4_timing_confidence_adapter_validation_v1`

Result:

`BLACKBOX_FAIL_closed_no_validated_E1_product`

Authority surfaces:

- development protocol: `docs/governance/downstream_timing_adapter_v1_protocol.json`
- development state: `docs/governance/downstream_timing_adapter_v1_state.json`
- development receipt: `docs/research/cloud_downstream_timing_adapter_v1_dev_diagnostic.json`
- development adjudication: `docs/research/downstream_timing_adapter_v1_dev_cloud_adjudication_20260912.md`
- validation protocol: `docs/governance/downstream_timing_adapter_validation_v1_blackbox_protocol.json`
- validation state: `docs/governance/downstream_timing_adapter_validation_v1_state.json`
- compact receipt: `docs/research/local_downstream_timing_adapter_validation_v1_blackbox_receipt.json`
- validation adjudication: `docs/research/downstream_timing_adapter_validation_v1_blackbox_cloud_adjudication_20260912.md`
- reusable BLACKBOX ledger: `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`

The E1 parent development result remains retrospective evidence only: the exact C1-direction + B4-zero-boundary-abstention adapter improved factor utility versus the C1-only comparator in 2015-2020, but the separately frozen 2021-2025 validation returned `FAIL`. Do not inspect hidden validation attribution and do not rescue this identity with thresholds, magnitude buckets, fitted weights, alternate horizons, alternate sign conventions, or extra upstream products.

## Reusable BLACKBOX ledger

The ledger currently contains **6** logical queries. Relevant validated shelf products remain:

- V6A global-spillover baseline — `PASS`;
- C1 15m continuous trend-conditioned open-state coordinate — `PASS`;
- B4 continuous driver-coherence coordinate — `PASS`.

Closed validation identities include D1 query 4 `FAIL`, C3 query 5 `FAIL`, and E1 query 6 `FAIL`. Detailed hidden behavior from any reusable BLACKBOX may not design or rescue later identities. Reuse of the same 2021-2025 physical block is not independent OOS.

## Deferred C2

`overnight_volatility_conditioned_open_state_60m_v1` remains frozen but **unopened and deferred**. Do not execute it unless `docs/governance/current_authority_v1.json` explicitly reactivates it.

## Downstream adapter boundary

`docs/governance/downstream_adapter_research_boundary_v1.json` governs E1/E2/E3 work.

- E1 failed reusable validation; no validated E1 timing-adapter product exists.
- E2 stock-selection work requires a new result-free identity bound to an explicitly named frozen consumer strategy. It may only scale or abstain that consumer strategy and may not become stock-specific alpha in this repository.
- E3 portfolio/risk work requires a new result-free identity bound to an explicitly named frozen consumer/account contract.
- Factor-utility evidence never substitutes for Strategy Slice Rebuild, Strategy Science Acceptance, post-training account audit, execution/cost validation, or production authorization.

## Stable authority that must not be casually reopened

Repository-wide accepted next-open architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

Global-spillover baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Validated C1 product:

`overnight_trend_conditioned_open_state_15m_v1`

Validated B4 product:

`overnight_driver_coherence_open_gap_v1`

Gap-Fill V2 remains frozen/repeat-confirmed, with its complete 2026-08-24..2026-12-31 true-fresh block separately gated. V2.1 P2 is closed at DEV with no successor.

## Execution rule

`docs/governance/current_authority_v1.json` is the canonical execution pointer. Do not run an old handoff, workflow, controller, or script merely because it remains in Git. When `active_research` is null, do not invent a successor from historical results; any new adapter/research identity must be independently motivated and result-free preregistered first.
