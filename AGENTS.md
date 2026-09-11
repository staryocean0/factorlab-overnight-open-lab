# Overnight Open Lab — agent instructions

This repository is the **Overnight/Open factor-product laboratory and downstream factor adapter** for FactorLab.

Before doing anything substantial, read:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_registry_v1.json`
3. the active identity's state + protocol
4. `docs/ops/README.md`

For any model, factor-family, routing, strategy, robustness, account, or cross-period change, also follow `.codex/skills/strategy-slice-rebuild/SKILL.md`.

`production_authority=false`.

## Scope

In scope: expected/observed China opening state, gap normalization, Gap-Fill hazards, global/offshore/FX Overnight drivers, causal trend/volatility/session-shape context, relative-index opening leadership, and frozen downstream adapters.

Out of scope: generic reversal/RMR, broad HighVol routing unrelated to Overnight/Open, two-wave logic, using downstream PnL to tune upstream factors, pretending the cash index is directly shortable, or production deployment.

## Current active task

The only active research identity is:

`overnight_volatility_conditioned_open_state_60m_v1`

Status:

`frozen_reusable_BLACKBOX_authorized_pending_local_execution`

Authority:

- state: `docs/governance/volatility_conditioned_open_state_60m_state_v1.json`
- protocol: `docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json`
- parent DEV adjudication: `docs/research/volatility_conditioned_open_state_dev_cloud_adjudication_20260911.md`
- handoff: `docs/ops/volatility_conditioned_open_state_60m_blackbox_handoff_20260911.md`
- runner: `scripts/run_volatility_conditioned_open_state_60m_blackbox.sh`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`

Frozen C2 factor:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
log_rvol20 = log(rvol20)
vol_gap_interaction = observed_gap_rvol * log_rvol20
```

The baseline includes both main effects and the validated C1 `trend_gap_interaction`.

Frozen target:

`09:35 -> 10:35`

The parent 2019-2020 C2 DEV identity is complete. Cloud adjudication authorized only this separately frozen 60-minute successor. The 15-minute C2 effect failed stability; the 30-minute effect was too weak/uneven for progression.

During the active BLACKBOX query:

- public output must be exactly `PASS`, `FAIL`, or `INSUFFICIENT`;
- do not expose exact metrics, counts, years, quarters, dates/events, yearly signs, bootstrap statistics, subgroup results, or internal gate details;
- do not create high/low-volatility thresholds or quantile buckets;
- do not change the 20-day volatility lookback, gap normalization, target horizon, or controls;
- do not remove the validated C1 control;
- do not add Opening Surprise terms;
- do not use downstream strategy returns;
- do not edit the reusable BLACKBOX ledger locally;
- do not persist or publish reconstructed 2021-2025 factor/target rows or convert them into a CSV text pack.

## Validated C1 product

`overnight_trend_conditioned_open_state_15m_v1` is already validated by reusable BLACKBOX `PASS` and is a shelf product only at the continuous 09:35→09:50 identity.

Do not infer authority for `up/range/down × high/low open` buckets from C1. A categorical consumer view requires a separate result-free threshold identity.

## Completed C2 DEV parent

Parent identity:

`overnight_volatility_conditioned_open_state_v1`

Cloud decision:

`C2_DEV_PROGRESS_60M_CONTINUOUS_COORDINATE_ONLY`

Do not rerun the parent DEV to select another horizon, volatility threshold, or lookback.

## Closed Opening Surprise identity

`overnight_open_surprise_factor_v1` is closed after DEV stability failure. No 2021-2025 BLACKBOX was opened. Do not rescue it by changing thresholds, horizons, signs, tails, buckets, or interactions.

## Product-shelf rule

This repo is not a Cartesian feature factory. Prefer reusable causal coordinates with clear meaning. Continuous coordinates come before categorical adapter views. Downstream strategy performance may validate a frozen adapter but may not teach or retune the upstream factor.

## Stable authority that must not be casually reopened

Repository-wide accepted next-open architecture:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

Current global-spillover single-head baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX query returned `PASS`. Do not decompose that BLACKBOX or use hidden behavior to design a successor.

Gap-Fill V2 remains frozen/repeat-confirmed, with its complete 2026-08-24..2026-12-31 true-fresh block separately gated. V21 P2 is closed at DEV with no successor.

## Execution rule

`docs/governance/current_authority_v1.json` is the canonical pointer for active execution. Do not run an old handoff or script merely because it remains in Git.
