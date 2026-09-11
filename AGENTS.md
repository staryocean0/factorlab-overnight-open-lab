# Overnight Open Lab — agent instructions

This repository is the **Overnight/Open factor-product laboratory and downstream factor adapter** for FactorLab.

Before doing anything substantial, read:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_registry_v1.json`
3. the active identity state + protocol
4. `docs/ops/README.md`

For any model, factor-family, routing, strategy, robustness, account, or cross-period change, also follow `.codex/skills/strategy-slice-rebuild/SKILL.md`.

`production_authority=false`.

## Scope

In scope:

- expected and observed China opening state;
- gap normalization and short-horizon opening information;
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

## Current active task

The only active research identity is:

`overnight_trend_conditioned_open_state_15m_v1`

Status:

`frozen_reusable_BLACKBOX_authorized_pending_local_execution`

Authority:

- state: `docs/governance/trend_conditioned_open_state_15m_state_v1.json`
- protocol: `docs/governance/trend_conditioned_open_state_15m_blackbox_protocol_v1.json`
- handoff: `docs/ops/trend_conditioned_open_state_15m_blackbox_handoff_20260911.md`
- runner: `scripts/run_trend_conditioned_open_state_15m_blackbox.sh`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`

Frozen factor:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
```

Frozen target:

`09:35 -> 09:50`

The parent 2019-2020 DEV identity is complete and closed for selection. Cloud adjudication retained only this separately frozen 15-minute successor.

During the active BLACKBOX query:

- public output must be exactly `PASS`, `FAIL`, or `INSUFFICIENT`;
- do not expose exact metrics, counts, years, quarters, dates/events, yearly signs, bootstrap statistics, subgroup results, or internal gate details;
- do not search alternate horizons;
- do not create `up/range/down` thresholds or trend quantile buckets;
- do not change the trend lookback or normalization;
- do not add volatility conditioning or Opening Surprise terms;
- do not use downstream strategy returns;
- do not edit the reusable BLACKBOX ledger locally;
- do not persist temporary reconstructed 2021-2025 factor rows.

## Completed C1 DEV parent

Parent identity:

`overnight_trend_conditioned_open_state_v1`

Cloud decision:

`C1_DEV_PROGRESS_15M_CONTINUOUS_COORDINATE_ONLY`

The 15-minute coefficient direction was stable across 2019 and 2020. The 30/60-minute coefficient directions were not stable and must not be revived as alternative choices after the fact.

Adjudication:

`docs/research/trend_conditioned_open_state_dev_cloud_adjudication_20260911.md`

## Closed Opening Surprise identity

`overnight_open_surprise_factor_v1` is closed after valid 2019-2020 DEV execution.

Decision:

`NO_STANDALONE_OPENING_SURPRISE_PRODUCT_PROMOTION_STABILITY_FAILURE`

No 2021-2025 BLACKBOX was opened for A3. Do not rescue it by changing thresholds, horizons, signs, tails, buckets, or interactions.

## Product-shelf rule

This repo is not a Cartesian feature factory. Prefer reusable causal coordinates with clear meaning. Continuous coordinates come before categorical adapter views. A label such as `uptrend × high-open` is not automatically a factor product; thresholds require a separately frozen identity and evidence boundary.

Downstream strategy performance may validate a frozen adapter but may not teach or retune the upstream factor.

## Stable authority that must not be casually reopened

Repository-wide accepted next-open architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

Current global-spillover single-head baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX query returned `PASS`. Do not decompose that BLACKBOX or use hidden behavior to design a successor.

Gap-Fill V2 remains frozen/repeat-confirmed, with its complete 2026-08-24..2026-12-31 true-fresh block separately gated.

V21 P2 is closed at DEV with no successor; do not rescue its frozen insufficiency or open sealed audits.

## Archive / execution rule

`docs/governance/current_authority_v1.json` is the only canonical pointer for active execution. Do not run an old handoff or script merely because it remains in Git. Archived entrypoints must not be revived without a new result-free protocol.
