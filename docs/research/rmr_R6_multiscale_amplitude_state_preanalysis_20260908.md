# R6 preanalysis — Multi-scale amplitude-state displacement

Date: 2026-09-08  
Identity: `R6_multiscale_amplitude_state_stage1_v1`  
Role: new broad-program shallow lane after the R1/R5-C two-promotion review.

## Question

Does the **shape of realized movement amplitude across fixed time scales** contain causal state information about subsequent reversal versus continuation beyond the severity of the just-completed move?

This is not another generic volatility-ratio test and not a wavelet/model search. The scientific object is the relative concentration of movement amplitude across short, intermediate and parent observation scales.

The motivating distinction is:

> Two completed moves can have similar size, while one is embedded in unusually short-scale movement concentration and the other in broader-scale movement concentration. Do those states have different reversal-first probabilities?

## Coordinate definition

- **base observation:** official CSI1000 1m close;
- **event scale:** the already frozen causal directional-change S1 and S2 completed-wave confirmations;
- **deviation object:** the current multi-scale amplitude curve relative to its own past-only normal state;
- **candidate mean:** the rolling normal shape of that amplitude curve, not a price level;
- **price outcome:** symmetric same-scale reversal-first versus extension-first after event confirmation.

## Fixed multi-scale amplitude measurement

At each causal event confirmation time, use only information available through that bar.

Lookback:

- trailing `240` observed 1m bars;
- cross-session returns are excluded rather than treated as ordinary 1m increments.

For each fixed horizon `k ∈ {4, 16, 64}` observed bars:

1. construct all valid trailing within-session `k`-bar log returns ending inside the lookback;
2. compute `amp_k = median(abs(k_bar_log_return)) / sqrt(k)`;
3. require finite positive amplitude at all three horizons.

No horizon search is allowed.

## Exactly two spectral-shape scores

### R6-A — short-to-mid amplitude concentration

`short_mid = log(amp_4 / amp_16)`

Interpretation:

- high value: movement energy is unusually concentrated at the shorter observation scale relative to the intermediate scale;
- low value: intermediate-scale amplitude dominates relative to the short scale.

### R6-B — mid-to-parent amplitude concentration

`mid_parent = log(amp_16 / amp_64)`

Interpretation:

- high value: intermediate-scale movement is elevated relative to parent-scale movement;
- low value: movement is concentrated more broadly at the parent scale.

These are fixed measurement objects, not candidate trading signals.

## Past-only state normalization

Each score is normalized separately within each event scale using:

- preceding `100` completed same-scale score observations;
- center: median;
- scale: MAD;
- current observation excluded from its own reference;
- zero/nonfinite MAD observations excluded.

Continuous z-scores are primary. `abs(z) >= 2` may be reported descriptively only; no extremity threshold may be selected from results.

## Price-path outcome

Reuse the already frozen broad/R5 symmetric first-passage semantics.

After a completed S1 or S2 wave confirmation:

- **reversion:** price moves opposite the completed-wave direction by one same-scale directional-change threshold from the event price;
- **extension:** price moves in the completed-wave direction by one same-scale threshold;
- maximum horizon: 1,200 observed 1m bars;
- unresolved or same-bar ambiguous events are censored;
- overlapping events are suppressed within each score×scale until the prior event resolves/censors.

## Candidate/model budget — exactly three objects per scale

1. `severity_only` — completed-wave severity in scale units;
2. `severity_plus_short_mid_z`;
3. `severity_plus_mid_parent_z`.

Estimator is fixed:

`StandardScaler + LogisticRegression(C=1, penalty=l2, solver=lbfgs, max_iter=1000)`

No combined two-score model, interaction, regime split, calibration, threshold selection or hyperparameter search is allowed in Stage-1 v1.

## Evidence roles

Reuse the frozen broad-program roles:

- DEV: 2015-01-05..2019-12-31;
- chronological stability: 2020-01-01..2022-12-31, not fresh;
- 2023-01-01..2025-12-31 reserve: unopened;
- all 2026 rows: unopened.

The source is historically consumed, so no result is scientifically fresh.

## Stage-1 hypotheses

H1. Multi-scale amplitude concentration contains price-path state information beyond completed-wave severity.

H2. If the mechanism is real, at least one of the two fixed concentration scores should improve the severity baseline in pooled held-forward Brier/log-loss at both S1 and S2.

H3. The improvement direction should be stable in multiple chronological years, not one lucky period.

H4. The effect should not require choosing an amplitude horizon or z threshold after outcomes are seen.

## Results-blind review rule

A score may become a **candidate for cross-lane review** only if all are true:

- at least `200` resolved stability events at each of S1 and S2;
- at least `50` resolved events in each stability year at each scale;
- pooled augmented Brier is strictly lower than severity-only at both S1 and S2;
- pooled augmented log-loss is strictly lower at both scales;
- annual Brier improvement is positive in at least 2 of 3 years at each scale;
- no frozen-boundary or causal-integrity violation occurs.

If both scores qualify, rank them only for review by the mean pooled Brier improvement across S1/S2, then mean log-loss improvement. This ranking does **not** itself promote a third mechanism.

Because two mechanisms (R1 and R5-C) are already progressed, any R6 positive result remains `candidate_for_program_review`, not `promoted`, until a new explicit cross-lane review is written.

## What closes R6 v1

- neither score qualifies at both scales;
- gains are one-scale or one-year only;
- the severity baseline explains the outcome equally well;
- results require adding frequency bands, changing horizons, changing the 240-bar lookback, or tuning z thresholds.

If R6 v1 closes, do not rescue it by adding FFT/wavelet variants under the same identity.

## Explicit non-goals

- no PnL;
- no Fourier/wavelet model search;
- no optimized band edges;
- no search over 4/16/64;
- no combined spectral feature vector;
- no use of the 2023–2025 reserve;
- no deep model;
- no production authority.
