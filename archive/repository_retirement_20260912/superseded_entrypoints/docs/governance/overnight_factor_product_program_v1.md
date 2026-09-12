# Overnight Factor Product Program v1

Date: 2026-09-12

## Program identity

This repository is governed as an **Overnight/Open factor-product laboratory and downstream factor adapter**, not as a project that must force one standalone all-day Overnight trading strategy.

Its job is to turn causal information around the next China open into small, versioned, reusable factor products with explicit availability clocks, mathematical definitions, evidence labels, provenance, and consumer-facing semantics.

A downstream timing, stock-selection, execution, or portfolio-risk system may consume one or more products. A useful factor does not need to be monetizable as an isolated strategy.

`docs/governance/current_authority_v1.json` is the canonical execution pointer. This program file defines stable architecture and current shelf state; it does not by itself authorize opening evidence.

`production_authority=false`.

## Research layers

The economic questions are separated into three layers:

1. **Opening-state information** — what state will or did the market open into?
2. **Short-horizon residual information** — after the opening state is known, what continuation, reversal, or fill information remains?
3. **Downstream adapter utility** — can a frozen timing, stock-selection, or risk consumer improve decisions by conditioning on an authority-bearing Overnight factor product?

The first two layers belong primarily in this repository. Strategy-specific alpha or account-PnL optimization belongs to a separately frozen consumer contract and may not redefine an upstream factor after outcomes are opened.

## Product-design rules

Do not create an unlimited Cartesian product of trend × volatility × gap sign × calendar × instrument × regime labels.

A factor product or adapter is admitted only when it has:

- a clear causal availability timestamp;
- a bounded mathematical identity;
- a frozen evidence boundary before adjudication;
- an explicit comparator and consumer-facing interpretation;
- reproducible source lineage;
- low enough dimensionality to interpret;
- a versioned state / protocol / authority chain;
- no downstream-return tuning of the upstream factor definition.

Continuous coordinates are preferred over arbitrary buckets. Any categorical view, threshold, magnitude bucket, alternate horizon, sign flip, reweighting, or consumer mutation requires its own result-free motivation and frozen identity before the relevant outcome evidence is opened.

## Product shelf

### Shelf A — Core Overnight/Open state

- **OFP-A1 Expected Open State** — confirmed components remain available under their exact authorities.
- **OFP-A2 Observed Open Geometry** — foundational post-open normalization coordinate.
- **OFP-A3 Opening Surprise / Residual** — Development closed after stability failure; no standalone validated A3 product and no automatic rescue.
- **OFP-A4 Gap-Fill Hazard** — frozen/repeat-confirmed Gap-Fill V2 family; true-fresh evaluation remains separately date-gated.

### Shelf B — Driver / attribution coordinates

- **OFP-B1 Global Risk Driver** — validated reusable continuous factor product; BLACKBOX PASS.
- **OFP-B2 China-Specific Offshore Driver** — validated reusable continuous factor product; BLACKBOX PASS.
- **OFP-B3 FX / Macro Overnight Driver** — BLACKBOX FAIL; no validated B3 product and no hidden-behavior rescue.
- **OFP-B4 Driver Coherence** — validated reusable continuous factor product; BLACKBOX PASS. Categorical agreement/disagreement views or alternate weights are not implied by the continuous product authority.

### Shelf C — Context coordinates

- **OFP-C1 Prior Trend Context** — validated reusable 15-minute continuous factor product; BLACKBOX PASS.
- **OFP-C2 Prior Volatility Context** — validated reusable 60-minute continuous factor product; BLACKBOX PASS.
- **OFP-C3 Previous China Session Shape** — Development progression existed, but the reusable joint BLACKBOX successor failed; no validated C3 product.
- **OFP-C4 Calendar / Closure Context** — the frozen weekend-gap candidate failed reusable BLACKBOX validation; no validated C4 product from that identity.

### Shelf D — Relative / cross-index opening state

- **OFP-D1 Relative Index Open** — Development progression existed, but the frozen joint reusable BLACKBOX successor failed; no validated D1 product and no rescue of the closed identity.

### Shelf E — Consumer adapters

These are thin mappings over frozen upstream products and frozen consumer contracts. They are not permission to invent a new strategy in this repository.

- **OFP-E1 Timing Adapter** — prior v1 reusable BLACKBOX failed. The later C1/C2 zero-boundary agreement adapter `overnight_c1_c2_timing_agreement_adapter_v1` closed at Development with `E1V2_DEV_NO_PROGRESS`. No successor is authorized from that result.
- **OFP-E2 Stock-Selection Adapter** — v1 B4 adapter closed `DEV_NO_PROGRESS`; v2 C2 adapter closed `DEV_INSUFFICIENT`; latest v3 B2 offshore-risk adapter `overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1` closed `E2V3_DEV_NO_PROGRESS`. No reusable validation successor is authorized from v3.
- **OFP-E3 Portfolio / Risk Adapter** — v1 closed `DEV_INSUFFICIENT`. The later B1 forward-cycle adapter progressed in Development, but its separately frozen reusable validation `overnight_b1_forward_cycle_portfolio_risk_abstention_validation_v1` returned BLACKBOX `FAIL` as query #12, so no validated E3v2 product exists.

Downstream adapter closures do **not** invalidate their upstream factor products.

## Latest downstream evidence

### E3v3 — C2 forward-cycle portfolio-risk adapter

The frozen C2 zero-boundary whole-portfolio abstention adapter closed as `E3V3_DEV_INSUFFICIENT`. Both 14:30 and 14:45 clocks have only 6 candidate-active decisions in 2017, below the frozen minimum of 8. Because sufficiency fails, incomplete-surface utility/downside statistics cannot authorize progression, rejection, rescue, or successor design. No 2021-2025 validation was opened, no BLACKBOX query was created, and the ledger remains 12. Validated upstream C2 remains authoritative.


### E2v3 — B2 stock-selection offshore-risk adapter

The frozen consumer was `REAKA_D5_H20_R5_CURRENT_GENERATION_V1` / `N30_equal_backfill_unconstrained` with 14:30 and 14:45 clocks jointly. The upstream coordinate was validated B2 `china_offshore_z`; the only semantic boundary was zero.

Development window: `2015-01-05..2020-12-31`.

Result: `E2V3_DEV_NO_PROGRESS`.

Both clocks satisfied all annual sufficiency gates, but neither satisfied the complete frozen progression contract. No 2021-2025 scientific rows were opened for E2v3, no account-PnL backtest was opened, and no BLACKBOX query was created. The reusable BLACKBOX ledger therefore remains at 12.

### E3v2 — B1 portfolio-risk adapter

The exact frozen B1 whole-portfolio abstention adapter progressed in Development, then entered a separately frozen compact reusable validation over 2021-2025.

Public result: `FAIL`.

Query: #12, `ce859f9c94f281b0ec49`.

The compact receipt intentionally persists no internal metrics, annual results, counts, bootstrap support, or failure attribution. The FAIL closes only the downstream adapter identity; validated upstream B1 remains authoritative.

## Validation hierarchy

A factor product or adapter should be evaluated in this order:

1. causal timing and source closure;
2. exact mathematical identity and reproducibility;
3. consumer/source admission when applicable;
4. incremental information versus the simpler frozen comparator;
5. sufficiency and stability across preregistered Development slices;
6. reusable BLACKBOX confirmation only after a successor identity is independently authorized and frozen;
7. account or strategy PnL only under a separately frozen consumer/account contract.

If a preregistered sufficiency gate fails, downstream utility values from the incomplete surface are diagnostic only and cannot be used to select, reject, tune, or rescue the candidate.

## Evidence policy

The reusable BLACKBOX ledger currently contains **12** opened logical queries.

Completed reusable BLACKBOX queries remain sealed at their allowed public decision surfaces. Hidden rows, years, quarters, residuals, bootstrap support, failure attribution, or behavior may not be used to design successors. Reusing 2021-2025 does not create an independent OOS sample.

Do not open post-2026-08-21 outcomes except under a separately frozen protocol.

The Gap-Fill V2 true-fresh evaluation remains date-gated until the complete `2026-08-24..2026-12-31` block exists and the already-frozen protocol permits evaluation.

## Current program state

There is currently **no active outcome-bearing research identity**.

The latest completed identity is `overnight_c2_forward_cycle_portfolio_risk_abstention_v1`, closed as `E3V3_DEV_INSUFFICIENT` with no reusable Validation successor, no account-execution backtest, no new BLACKBOX query, and no production authority.

No additional outcome-bearing research is automatically authorized. The repository should maintain the validated shelf until either:

1. a separately motivated, result-free identity is frozen under cloud-main research authority; or
2. the already-frozen Gap-Fill V2 true-fresh protocol reaches its date gate.

The cloud main agent owns research authority and should request the user only for a concrete missing-data dependency or when the user explicitly asks for status.

`production_authority=false`.
