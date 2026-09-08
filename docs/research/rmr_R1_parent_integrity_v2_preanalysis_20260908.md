# R1 specialist preanalysis — Parent-integrity compression and holdout confirmation

Date: 2026-09-08  
Research identity: `rmr_cross_scale_pullback_parent_integrity_v2`  
Source: promoted R1 Stage-1 broad-screen evidence.

## Scientific question

The broad screen showed that, conditional on counter-move severity, causally available parent structure improves recovery-before-parent-failure probability at both frozen scale pairings.

The specialist asks two narrower questions before any PnL work:

1. Can the parent-state information be compressed into one interpretable scalar without losing the cross-scale effect?
2. After the representation is frozen on already-consumed 2015–2022 evidence, does the selected representation survive the untouched 2023–2025 within-program mechanism holdout?

The mechanism remains:

> for a counter-move of comparable severity, stronger parent integrity should increase recovery-first probability before parent structural failure.

## Evidence roles

Common source remains `data/high_open_dev_2015_2025/1m_official.parquet`.

- representation selection DEV: 2015-01-05 .. 2019-12-31;
- held-forward selection/stability: 2020-01-01 .. 2022-12-31, already consumed and not fresh;
- specialist mechanism holdout: 2023-01-01 .. 2025-12-31, currently unopened for this program and not scientifically fresh across the wider research history;
- all 2026 rows remain sealed.

The holdout may not be used to alter the representation, model class, scale, event rule, boundary, gates, or candidate order.

## Frozen event geometry

Reuse the broad Stage-1 causal directional-change construction without modification.

Two mandatory pairings:

- PAIR_A: lower S1 inside parent S2;
- PAIR_B: lower S2 inside parent S3.

The event is a causally confirmed lower-scale completed wave opposite to the net drift of the last two causally available parent waves.

Outcome:

- recovery: regain the lower counter-wave origin first;
- failure: break the latest causally available parent structural trough/peak first;
- maximum horizon: 1200 observed 1m bars;
- unresolved events: censored;
- no overlapping same-pair event until the prior event resolves/censors.

## Candidate family — exactly two parent representations

All candidates retain the exact broad-screen severity definition:

`severity = abs(lower_wave_move) / DEV_median_rvol20`.

The directional-change threshold determines the measurement scale; it is **not** substituted into the severity denominator. This preserves the promoted broad R1 baseline exactly.

### C1 — `R1_PARENT_COMPOSITE_1D`

Within each scale pairing, fit feature standardization on the training partition only:

- `z_drift = z(abs_drift)`;
- `z_overlap = z(overlap)`;
- `z_eff = z(parent_eff)`.

Define:

`parent_integrity = (z_drift - z_overlap + z_eff) / 3`.

The signs are frozen from structural interpretation before holdout access: stronger drift and higher path efficiency raise integrity; greater wave overlap lowers integrity.

Probability model:

`severity + parent_integrity`.

### C2 — `R1_PARENT_ORIGINAL_3D`

Probability model:

`severity + abs_drift + overlap + parent_eff`.

This is the broad-screen parent representation carried forward unchanged.

No third candidate, interaction, threshold, nonlinear transform, alternative scaler, model-class search, hyperparameter search, calibration, or PnL selection is allowed.

## Selection rule on consumed 2015–2022 evidence

Complexity ladder:

1. `R1_PARENT_COMPOSITE_1D`;
2. `R1_PARENT_ORIGINAL_3D`.

For each candidate, fit on 2015–2019 and score on 2020–2022 at both PAIR_A and PAIR_B.

A candidate is eligible only if, at both pairings:

- stability resolved events >= 200 pooled;
- each 2020/2021/2022 year has >= 50 resolved events;
- pooled Brier is strictly lower than severity-only baseline;
- pooled log-loss is strictly lower than severity-only baseline;
- annual Brier improvement is positive in at least 2 of 3 years.

Stop at the first eligible candidate. If C1 passes, C2 is not selected even if numerically better. If C1 fails, C2 may be evaluated. If neither passes, close the specialist before opening 2023–2025.

## Full consumed-data refit before holdout

If one candidate is selected, refit the severity baseline and selected candidate separately for each scale pairing on all consumed 2015–2022 resolved events.

Freeze:

- feature names and orientation;
- scalers;
- logistic coefficients/intercepts;
- source SHA;
- event thresholds;
- broad-compatible severity denominator;
- candidate identity;
- model/parameter digest;
- holdout gates.

Only after this parameter freeze may 2023–2025 be opened.

## Holdout confirmation gate

On untouched 2023–2025, with no refit:

At both PAIR_A and PAIR_B require:

- >= 200 pooled resolved events;
- >= 50 resolved events in each of 2023, 2024, 2025;
- selected-candidate pooled Brier strictly lower than frozen severity baseline;
- selected-candidate pooled log-loss strictly lower than frozen severity baseline;
- annual Brier improvement positive in at least 2 of 3 years.

For `R1_PARENT_COMPOSITE_1D`, the frozen full-consumed-data parent-integrity coefficient must be positive. For `R1_PARENT_ORIGINAL_3D`, report the directional integrity contrast but do not require every correlated component coefficient to have a particular sign.

Passing the mechanism holdout is still **not fresh confirmation, not PnL evidence, and not production authority**. A later truly fresh period/source must be separately reserved before strategy optimization.

## Explicitly forbidden

- opening 2023–2025 before selection and parameter freeze;
- choosing only one scale pairing;
- changing directional-change thresholds;
- changing the broad-compatible severity definition;
- adding trend indicators or volatility filters;
- searching an integrity cutoff;
- modifying recovery/failure boundaries;
- changing logistic C/penalty/model class;
- probability calibration or binary threshold selection;
- trading-return/PnL selection;
- treating 2023–2025 as scientifically fresh;
- reading any 2026 outcome.

Production authority remains false.
