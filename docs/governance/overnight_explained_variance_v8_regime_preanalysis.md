# V8 continuous-regime preanalysis

Date: 2026-09-06  
Branch: `codex/overnight-regime-v8-20260906`

## Financial question

V6 established a strong causal offshore-China information channel: the same-contract SGX FTSE China A50 move from the previous mainland close to strictly before the 09:15 mainland opening call auction. The next question is not whether another market contains the same overnight information, but whether **the mapping from a given offshore A50 move into the next CSI1000 opening gap is state dependent**.

The intended financial mechanism is pass-through elasticity:

> When the mainland market enters the next session with a different pre-existing volatility/fragility state, should the same offshore China price-discovery move be absorbed with the same opening-gap coefficient?

This is materially different from adding another correlated price source. It asks whether the coefficient on an already-validated causal information source changes with an already-known domestic state.

## Literature prior

The literature provides a clear prior that international/China spillovers are state dependent rather than constant:

- Zhang, Lei & Wei, *Forecasting the Chinese stock market volatility with international market volatilities: The role of regime switching*, North American Journal of Economics and Finance (2020), DOI `10.1016/j.najef.2020.101145`. Regime-switching versions of international-volatility forecasting models improve out-of-sample Chinese volatility forecasts and directional accuracy relative to fixed-coefficient counterparts.
- Sheng et al., *The asymmetric volatility spillover across Shanghai, Hong Kong and the U.S. stock markets: A regime weighted measure and its forecast inference*, International Review of Financial Analysis 91 (2024), article 102964, DOI `10.1016/j.irfa.2023.102964`. Spillover asymmetry is regime dependent and intensifies in high-volatility regimes; regime-dependent spillovers improve Shanghai-market forecasting.
- *Regime-dependent volatility spillover asymmetry in Shanghai and Hong Kong stock markets with forecasting and portfolio inferences*, Economic Modelling (2025), DOI `10.1016/j.econmod.2025.107268`. The reported high-frequency evidence finds spillover asymmetry intensifies in high-volatility regimes.
- Valadkhani & Marashdeh, *Regime-dependent causality between Chinese and U.S. equity markets: Evidence from Markov switching models*, Research in International Business and Finance 83 (2026), article 103285. The direction/strength of China-U.S. causality changes across stable and crisis regimes.

These papers support **state dependence as an economic prior**. They do not justify importing their Markov-state machinery or thresholds into this project.

## Why not Markov switching / HMM in the first regime experiment

A Markov-switching implementation would introduce several additional research degrees of freedom at once:

- state count;
- transition structure;
- initialization and local-optimum concerns;
- state-identification/labeling;
- whether coefficients, variances, or both switch;
- inference and fallback behavior when state probabilities are diffuse.

With only 2015-2018 training and consumed 2019-2020 repeat-audit material in the cloud, that is too much freedom for the first test. It would also make it difficult to distinguish a genuine financial state mechanism from a flexible nonlinear fit.

## Minimal mathematical realization

Use the existing frozen `rvol20` feature as the domestic state variable and the frozen V6 ordinary A50 feature as the causal foreign-information variable.

The only new feature is:

`a50_ordinary_x_rvol20 = a50_ordinary_preauction_closure_return * rvol20`

No centering threshold, quantile bucket, sign split, spline, absolute-value transform, or state classification is introduced.

The hierarchy condition is satisfied because both main effects already exist in V6:

- `rvol20` is a frozen baseline feature;
- `a50_ordinary_preauction_closure_return` is the retained V6 offshore-China feature.

The frozen `StandardScaler + Ridge(alpha=1.0)` pipeline then standardizes the interaction along with the existing features.

## Economic interpretation

For ordinary sessions, the conditional A50 pass-through in the raw linear representation becomes approximately:

`gap contribution = beta_A50 * A50 + beta_interaction * A50 * rvol20`

so the marginal sensitivity to A50 is:

`d gap / d A50 = beta_A50 + beta_interaction * rvol20`.

The interaction coefficient's sign is **diagnostic, not a validity gate**. High domestic volatility could amplify offshore information transmission through fragility/information sensitivity, but it could also attenuate the linear price mapping if mainland-specific noise dominates. The falsifiable question is whether allowing one continuous state-dependent slope improves the frozen predictive objective stably, not whether a preconceived sign appears.

## Scope behavior

The ordinary A50 feature is zero on frozen holiday rows. Therefore the interaction is exactly zero on holiday rows as well. This preserves the semantic separation between:

- ordinary-session offshore A50 pass-through; and
- the already-frozen holiday-closure A50 mechanism.

Refitting can still redistribute other Ridge coefficients, so holiday SSE must be reported and preserved as a hard gate.

## Why `rvol20`

`rvol20` is selected **before results** because:

1. it already exists in the original frozen baseline and is available before the target open;
2. it expresses the intended financial state directly: recent mainland realized volatility/fragility;
3. it requires no new data source, threshold, latent-state estimator, or target-driven feature engineering;
4. it produces exactly one extra degree of freedom when interacted with the strongest validated ordinary offshore-China channel.

No alternative state variable is evaluated in V8. If this mechanism fails, the result does not authorize trying `abs_r1`, VIX, rolling drawdown, quantile buckets, or another state variable on the same consumed holdout without a new independent preregistration and scientific rationale.

## Evidence boundary

- Train: 2015-2018.
- 2019-2020: consumed repeat-audit only; not fresh OOS.
- 2021+: cloud-forbidden and remains owned by the local unseen controller.
- No PnL, total return, Sharpe, execution profitability, threshold search, state-count search, or model-family search.
- V6 unseen-controller identity remains unchanged regardless of V8 result.
