# Gap-Fill Prediction V2 — Phase-2 hazard adjudication — 2026-09-06

## Decision

Phase-2 is accepted as a valid bounded development-only probabilistic model selection.

Research identity: `gap_fill_prediction_v2`.

Decision: **select separate high-gap and low-gap geometry-only three-stage discrete-time hazard heads, freeze the complete V2 Phase-2 architecture, and do not open 2026 yet.**

Selected architecture SHA256:

`07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`

Selected head specs:

- high-gap head: `geometry_only`, spec SHA256 `068bb732f992d1e2800489b4e3ac2320bd13ec465e3c23f4b4cc800fe9e45a51`;
- low-gap head: `geometry_only`, spec SHA256 `f36f53d24b5f223094c6ad936a9de963365b686a1df474bfdfdc6336a9f53082`.

Both selected heads use only:

1. `abs_gap`;
2. `abs_gap_over_rvol20`.

The V1 direction/global-support variables remain valid Phase-1 mechanism findings, but the fixed Phase-2 full models did not satisfy the preregistered incremental probability-quality gates and are not admitted into V2 v1.

## Execution integrity

Cloud run: `34033989463`.

Before any hazard model fit:

- family / runner / test / parent / Phase-1 / V1 selected-spec Git blob identities passed;
- annotated panel, official 1m, FRED Nasdaq and FRED VIX SHA256 checks passed;
- package validator passed;
- pytest: 40 passed.

Selection used prior-year-only V1 direction OOF support for 2016-2025 and therefore began hazard OOF validation in 2017. The hazard selection window is 2017-2025 expanding natural-year OOF. No 2026 row was loaded. No 2026 repeat validation was opened.

No C, penalty, solver, class-weight, threshold, horizon-weight or model-class search was performed. Probability calibration diagnostics were descriptive only and were not used for selection. Trading return was not used.

## Architecture

High and low gaps are modeled separately.

For each sign:

- `h15 = P(fill by 15m | information at 09:31)`;
- `h60 = P(fill between 15m and 60m | not filled by 15m, information at 09:31)`;
- `hEOD = P(fill between 60m and EOD | not filled by 60m, information at 09:31)`.

Cumulative outputs are:

- `p15 = h15`;
- `p60 = 1 - (1-h15)(1-h60)`;
- `pEOD = 1 - (1-h15)(1-h60)(1-hEOD)`.

Thus `p15 <= p60 <= pEOD` is guaranteed by construction. No binary action threshold is selected in V2.

The fixed estimator for every stage is `StandardScaler + LogisticRegression(C=1, L2, lbfgs, class_weight=None)`.

## High-gap result

The geometry model passed **every** skill gate against the expanding empirical stage-hazard benchmark.

On `abs_gap > 10bp`, integrated Brier improvement versus the empirical benchmark was positive in **9/9** OOF years; the median annual improvement was about `0.04221`.

Pooled geometry improvement versus the empirical benchmark:

| cohort | integrated Brier improvement | integrated log-loss improvement |
|---|---:|---:|
| all nonzero high gaps | +0.06349 | +0.13876 |
| high gaps >10bp | +0.04696 | +0.09973 |
| high gaps >30bp | +0.08001 | +0.17031 |

The Phase-1 full high-gap model did show some conditional incremental structure, but failed the frozen full-admission gate:

- pooled all-gap integrated Brier: **worse** than geometry by about `0.000451`;
- pooled all-gap integrated log loss: **worse** by about `0.003311`;
- >10bp integrated Brier: better by about `0.001708`;
- >30bp integrated Brier: **worse** by about `0.002141`;
- >10bp annual integrated-Brier improvement was positive in 6/9 years and all three horizon Briers improved, but this cannot override the all-gap and >30bp failures.

Therefore the high-gap full model is rejected and the high-gap geometry head is selected.

The apparent >10bp-only improvement must **not** be converted post hoc into a gap-size gating rule on this consumed evidence. A future size-conditional architecture would require a new preregistered identity.

## Low-gap result

The low-gap geometry model also passed **every** skill gate against the empirical benchmark.

On `abs_gap > 10bp`, integrated Brier improvement was positive in **9/9** OOF years; median annual improvement was about `0.01453`.

Pooled geometry improvement versus the empirical benchmark:

| cohort | integrated Brier improvement | integrated log-loss improvement |
|---|---:|---:|
| all nonzero low gaps | +0.02768 | +0.06282 |
| low gaps >10bp | +0.02290 | +0.04857 |
| low gaps >30bp | +0.04882 | +0.10443 |

The Phase-1 full low-gap model produced only tiny Brier changes and failed the preregistered robustness/log-loss gates:

- pooled all-gap integrated Brier: better by only about `0.000201`;
- pooled all-gap integrated log loss: **worse** by about `0.001184`;
- >10bp integrated Brier: better by about `0.000051`;
- >30bp integrated Brier: better by about `0.000215`, but log loss was worse;
- only 5/9 >10bp OOF years improved integrated Brier versus the required 6/9;
- 15m and 60m Brier improved slightly, while EOD Brier worsened.

Therefore the low-gap full model is rejected and the low-gap geometry head is selected.

## Scientific interpretation

Phase-1 established that V1 direction support and global overnight support have stable univariate relationships with gap-fill outcomes. Phase-2 adds an important multivariate result:

> Those support variables do not yet provide sufficiently robust incremental probability quality after the observed gap geometry itself is known.

This is not a contradiction. Phase-1 asked whether the variables carry directional mechanism information; Phase-2 asked the harder question of whether they improve an out-of-sample cumulative probability model beyond gap geometry.

For V2 v1, the answer is that **gap geometry dominates**.

The observed gap size and its size relative to recent volatility are sufficient to form a stable first probabilistic fill model. The more elaborate support variables remain progression material but are not part of the accepted v1 predictor.

## Evidence boundary

- target / development data: through 2025-12-31;
- hazard OOF selection: 2017-2025;
- 2021-2025 is consumed development evidence and is not fresh;
- 2026-01-05 through 2026-08-21 remains unopened for this V2 identity and is repeat-only if later authorized;
- post-2026-08-21 remains unread true-fresh evidence;
- production authority remains false.

## Next step

Before any repeat validation, freeze a deterministic final-development refit of the selected high/low geometry hazard heads on the full permitted 2015-2025 development target inventory, recording scaler parameters, logistic coefficients/intercepts, training-risk-set counts, source hashes and library versions. Only after that fit identity is sealed may a separate repeat-validation protocol consider 2026-01-05..2026-08-21.
