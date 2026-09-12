# FactorLab Overnight Open Lab

This repository is the **Overnight/Open factor-product laboratory and downstream factor-adapter lab** for FactorLab. It researches causal information around the next China open, freezes reusable factor coordinates, and tests narrowly defined downstream timing / stock-selection / portfolio-risk adapters.

`production_authority=false`.

## Start here

Read in this order:

1. `docs/governance/current_authority_v1.json` — canonical execution pointer;
2. `docs/governance/overnight_factor_product_program_v1.md` — stable program architecture;
3. `docs/governance/overnight_factor_product_registry_v1.json` — product shelf and adapter registry;
4. the state / protocol / adjudication for the identity being inspected;
5. `docs/ops/README.md` for operational material.

Historical runners, README text, archived protocols, or prior research plans do **not** reopen a closed identity.

## Latest completed research — E3v3

`overnight_c2_forward_cycle_portfolio_risk_abstention_v1` closed as **`E3V3_DEV_INSUFFICIENT`**. Both frozen clocks have only 6 C2-active decisions in 2017 versus the preregistered minimum of 8, so no reusable validation, query #13, rescue, or successor is authorized. Validated upstream C2 remains valid; reusable BLACKBOX ledger count remains **12**.

## Current authority — 2026-09-12

There is currently **no active outcome-bearing research identity**.

A previously completed downstream line is:

`overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1`

It used validated B2 `china_offshore_z` as a zero-boundary whole-decision abstention overlay on the frozen `REAKA_D5_H20_R5_CURRENT_GENERATION_V1` stock-selection consumer. Its six-year Development result is:

`E2V3_DEV_NO_PROGRESS`

Both 14:30 and 14:45 clocks had sufficient Development support, but neither passed the full frozen progression contract. No reusable 2021-2025 validation was authorized, no new BLACKBOX query was created, no account-PnL backtest was opened, and no successor/rescue is authorized from that result.

Authority:

- state: `docs/governance/downstream_b2_stock_selection_offshore_risk_adapter_v1_state.json`
- adjudication: `docs/research/downstream_b2_stock_selection_offshore_risk_adapter_v1_dev_cloud_adjudication_20260912.md`
- Development receipt: `docs/research/cloud_downstream_b2_stock_selection_offshore_risk_adapter_v1_dev_diagnostic.json`

Immediately before E2v3, E3v2 `overnight_b1_forward_cycle_portfolio_risk_abstention_validation_v1` reached reusable validation and returned sealed BLACKBOX `FAIL` as query **#12** (`ce859f9c94f281b0ec49`). That result closes the exact E3 adapter contract only; it does not revoke validated upstream B1.

## Validated reusable shelf

Current authority-bearing reusable products include:

- **V6A Global Spillover** — PASS;
- **OFP-B1 Global Risk Driver** — BLACKBOX PASS, validated continuous factor product;
- **OFP-B2 China-Specific Offshore Driver** — BLACKBOX PASS, validated continuous factor product;
- **OFP-C1 Prior Trend Context** — BLACKBOX PASS, validated 15-minute continuous factor product;
- **OFP-C2 Prior Volatility Context** — BLACKBOX PASS, validated 60-minute continuous factor product;
- **OFP-B4 Driver Coherence** — BLACKBOX PASS, validated continuous factor product;
- **OFP-A4 Gap-Fill V2** — frozen/repeat-confirmed; true-fresh evaluation remains separately date-gated.

These are shelf products only at their validated identities. A categorical view, alternate threshold, bucket, horizon, sign, weighting, or downstream mapping requires a separately motivated result-free identity before outcome evidence is opened.

## Important closed lines

Closed negative / insufficient evidence remains part of the research record but is not an active candidate:

- Opening Surprise A3 — Development closed, no standalone validated A3 product;
- B3 FX driver — reusable BLACKBOX FAIL, no validated B3 product;
- C3 previous-session-shape successor — reusable BLACKBOX FAIL;
- C4 weekend-gap candidate — reusable BLACKBOX FAIL (#11);
- D1 relative-index successor — reusable BLACKBOX FAIL;
- E1 timing adapters — latest v2 closed `DEV_NO_PROGRESS`;
- E2 stock-selection adapters — v1 `DEV_NO_PROGRESS`, v2 `DEV_INSUFFICIENT`, latest v3 `DEV_NO_PROGRESS`;
- E3 portfolio-risk adapters — v1 `DEV_INSUFFICIENT`; latest v2 reusable BLACKBOX FAIL (#12);
- A1 validated-driver adapter — `DEV_NO_PROGRESS`.

Downstream adapter closures must not be reinterpreted as failures of their upstream validated factors.

## Reusable BLACKBOX boundary

The reusable BLACKBOX ledger contains **12** opened logical queries.

Completed queries remain sealed at their permitted public decision surfaces. Hidden rows, years, quarters, bootstrap support, residuals, failure attribution, or other hidden behavior may not be used to design successors. Reusing 2021-2025 does not create a new independent OOS sample.

Do not open post-2026-08-21 outcomes except under a separately frozen protocol.

## What happens next

No additional outcome-bearing research is automatically authorized at this breakpoint.

The repository should remain on the validated shelf until either:

1. a **separately motivated, result-free** identity is frozen under cloud-main research authority; or
2. the already-frozen Gap-Fill V2 true-fresh protocol reaches its date gate after the complete `2026-08-24..2026-12-31` block exists.

The cloud main agent owns research authority. The user should be interrupted only for a concrete missing-data dependency or an explicit status request.

## Data and archive

Repository data carriers have explicit evidence boundaries. Historical files are not automatically active. Read `data/README.md`, `docs/governance/package_scope.json`, and the identity-specific protocol before opening evidence.

For model/factor/strategy changes also follow `.codex/skills/strategy-slice-rebuild/SKILL.md`.

`production_authority=false`.
