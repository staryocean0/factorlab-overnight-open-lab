# Overnight Open Lab — agent instructions

This repository is the **Overnight/Open factor-product laboratory and downstream factor adapter** for FactorLab.

Before doing anything substantial, read:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_registry_v1.json`
3. the active identity's state + protocol
4. `docs/ops/README.md`

For any model, factor-family, routing, strategy, robustness, account, or cross-period change, also follow:

`.codex/skills/strategy-slice-rebuild/SKILL.md`

## Scope

In scope:

- expected and observed China opening state;
- opening-gap normalization and short-horizon residual information;
- Gap-Fill hazards;
- global / offshore-China / FX Overnight drivers;
- causal trend/volatility/session-shape context;
- relative-index opening leadership under new identities;
- frozen adapters for timing, stock-selection, execution, and risk.

Out of scope:

- generic reversal/RMR/parent-trend strategies;
- broad HighVol routing unrelated to Overnight/Open;
- two-wave strategy logic;
- using downstream strategy PnL to tune upstream factors;
- pretending the CSI1000 cash index is directly executable/shortable;
- live registry mutation or production deployment.

`production_authority=false`.

## Current active task

The only active research identity is:

`overnight_trend_conditioned_open_state_v1`

Status:

`mechanism_diagnostic_frozen_pending_local_2019_2020_execution`

Authority:

- protocol: `docs/governance/trend_conditioned_open_state_v1_protocol.json`
- state: `docs/governance/trend_conditioned_open_state_v1_state.json`
- preanalysis: `docs/research/trend_conditioned_open_state_preanalysis_20260911.md`
- handoff: `docs/ops/trend_conditioned_open_state_dev_handoff_20260911.md`
- runner: `scripts/run_trend_conditioned_open_state_dev.sh`

Frozen continuous coordinates:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
```

The baseline already includes `observed_gap_rvol` and `trend20_rvol`. The candidate adds exactly the interaction term.

Detailed outcomes are authorized only for `2019-01-01..2020-12-31`.

For this identity:

- do not read detailed 2021-2025 outcomes;
- do not read 2026 outcomes;
- do not run trading-return optimization;
- do not search `up/range/down` thresholds or trend quantile buckets;
- do not search alternate trend lookbacks or target horizons;
- do not add volatility conditioning;
- do not add Opening Surprise terms as a rescue;
- do not open a reusable BLACKBOX until cloud review freezes a later protocol.

## Closed Opening Surprise identity

`overnight_open_surprise_factor_v1` is closed after valid 2019-2020 DEV execution.

Decision:

`NO_STANDALONE_OPENING_SURPRISE_PRODUCT_PROMOTION_STABILITY_FAILURE`

The coefficient changed sign between 2019 and 2020 at all three frozen horizons and pooled incremental information was very small. No 2021-2025 BLACKBOX was opened.

Do not rescue A3 by changing thresholds, horizons, signs, tails, buckets, or interactions. Its execution entrypoint is archived under `archive/opening_surprise_completed_20260911/`.

## Product-shelf rule

This repo is not a Cartesian feature factory.

Prefer reusable causal coordinates with clear meaning:

- expected open;
- observed gap;
- gap-fill probability;
- driver attribution;
- trend / volatility / session-shape context;
- relative-index opening state.

Continuous coordinates come before categorical views. A label such as `uptrend × high-open` is not automatically a factor product; thresholds must be frozen before the evidence used to judge them is opened.

Downstream strategy performance may validate a frozen adapter but may not teach or retune the upstream factor.

## Stable authority that must not be casually reopened

### Next-open architecture

Repository-wide accepted architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

### Global-spillover lineage

Current single-head signed-gap baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its one reusable 2021-2025 BLACKBOX query returned `PASS`. Do not decompose hidden BLACKBOX behavior or use it to design a successor.

### Gap-Fill V2

Frozen and repeat-confirmed. The complete `2026-08-24..2026-12-31` block remains the separately gated true-fresh challenge.

### V2.1 P2

Closed at DEV with no successor because its frozen yearly sample gate was insufficient. Do not rescue it or open sealed audits.

## Evidence / data rules

Physical data presence does not grant evidence authority. Read the active state/protocol first.

- 2021-2025 may be reusable aggregate BLACKBOX for separately frozen identities, but reuse is not a new independent OOS sample.
- Detailed hidden BLACKBOX rows/years/quarters/events remain forbidden unless a protocol explicitly grants detailed development use.
- Post-2026-08-21 outcomes remain sealed wherever current protocols require.
- Do not substitute continuous A50/CFD/ETF proxies for the frozen same-contract SGX source identity.

## Cloud-local collaboration

When the user activates cloud-local collaboration, execution priority is:

1. current cloud session if data/tools are available;
2. local model through a minimal executable handoff;
3. GitHub Actions only as a last resort and only when quota/authorization allow it.

Do not dispatch Actions while the user has said quota is unavailable. Use `[skip ci]` for documentation/code commits where applicable.

Local execution must not mutate authority/registry/BLACKBOX ledgers unless the handoff explicitly authorizes it. The cloud main agent reviews receipts and performs adjudication.

## Archive

Archived executables are provenance, not active work. Read `archive/README.md` and never run an archived entrypoint unless a new result-free protocol explicitly revives it.
