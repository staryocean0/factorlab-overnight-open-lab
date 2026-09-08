# R3 preanalysis — Regime-conditioned residual reversion

Date: 2026-09-08  
Identity: `R3_regime_conditioned_residual_stage1_v1`  
Role: results-blind shallow screen, not deep latent-model development.

## Question

Does price revert more cleanly when “deviation” is measured relative to the **normal path/distribution for the current market state**, rather than relative to one unconditional mean?

The Stage-1 purpose is not to prove a Koopman model. It is to test whether state conditioning is scientifically necessary before investing in complex dynamics models.

## Coordinate definition

- **scale:** current and parent scales must be declared before outcome inspection;
- **parent state object:** low-capacity state vector using only causal price-path information;
- **deviation object:** residual between observed current movement and the state-conditioned expected movement/distribution;
- **candidate mean:** the state-conditioned expectation, not a global moving average;
- **reversion:** residual moves back toward the state-conditioned center before materially extending away or before a state transition invalidates the old expectation.

## Stage-1 state representation

No HMM, deep autoencoder, Koopman operator search, or large regime grid is authorized initially.

Use a low-capacity state vector built from a small common set:

1. completed-wave signed drift ratio;
2. path efficiency;
3. short-to-parent volatility ratio.

The first implementation may use either:

- a simple continuous low-capacity conditional model; or
- a small predeclared state partition derived from those variables.

The choice must be frozen before the outcome period is inspected. Do not search many regime counts.

## Normal-path / residual definition

Within training data only, estimate the expected near-term movement or distribution conditional on the state vector.

At event time:

`conditional_residual = observed_current_move - expected_move_given_state`

Primary comparator:

`unconditional_deviation = observed_current_move - unconditional_expected_move`

No future data may enter state estimation or residual construction.

## Primary outcome logic

Use a symmetric/structural first-passage comparison around the state-conditioned center where practical:

- **reversion boundary:** residual returns materially toward zero / the state-conditioned center;
- **extension boundary:** residual extends away by a predeclared comparable amount;
- **state invalidation:** a causally detected state transition censors or separately labels the event rather than forcing it into mean reversion.

Report first-passage share and time-to-event.

## Stage-1 hypotheses

H1. State-conditioned residual magnitude should predict reversion more consistently than unconditional deviation magnitude.

H2. The same raw deviation should have different recovery probabilities in materially different parent states.

H3. A low-capacity state model should capture enough of this difference to justify later regime/dynamics research.

## Minimal comparisons

Only three first-pass models/objects are authorized:

1. **unconditional deviation baseline**;
2. **state-conditioned residual** using the frozen low-capacity state representation;
3. **state-conditioned residual + residual magnitude only** as the smallest probability model if needed for calibration comparison.

Do not add dozens of technical factors or latent dimensions in Stage 1.

## What would count as promising

R3 is progression-worthy if:

- state conditioning materially improves the stability of residual reversion versus unconditional deviation;
- the improvement appears in multiple chronological or scale slices;
- the effect is not produced solely by one volatility state;
- a low-capacity representation is enough to show the phenomenon;
- residual construction is causal and reproducible.

## What would close or downgrade R3

- state conditioning does not improve on unconditional deviation;
- apparent improvement comes only from an overfit regime partition;
- regime labels are unstable or depend on future information;
- residual behavior changes sign across periods without a stable explanation;
- the effect only appears after increasing model capacity substantially.

## Escalation rule

Only if Stage 1 supports H1–H3 may a later identity consider:

- hidden/semi-Markov regimes;
- state-space models;
- Koopman operators;
- adaptive latent dynamics;
- residual-enhanced Koopman architectures.

Operator count, latent dimension, residual path, and model class then require a new bounded protocol. The 2026 ICASSP residual-enhanced adaptive Koopman paper is motivation for a possible implementation family, not evidence that it should be used here automatically.

## Data needed

Minimum:

- continuous OHLC history with reliable timestamps;
- enough history for causal state estimation and chronological OOS residual evaluation;
- no fundamentals, news, cross-asset data, or execution data required in Stage 1.

## Explicit non-goals

- no deep learning in the first pass;
- no regime-count search;
- no trading PnL optimization;
- no claim that every extreme residual should be faded.

The first-round question is whether **conditioning “normal” on market state produces a more stable reversion object than a single unconditional mean**.
