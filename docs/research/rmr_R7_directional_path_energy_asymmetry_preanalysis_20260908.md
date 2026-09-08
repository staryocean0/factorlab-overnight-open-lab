# R7 preanalysis — Directional path-energy asymmetry state

Date: 2026-09-08  
Identity: `R7_directional_path_energy_asymmetry_stage1_v1`  
Role: new broad-program shallow lane after R6 fixed amplitude-state closure.

## Question

For two causally completed moves of comparable severity, does the **directional balance of realized movement immediately preceding confirmation** contain information about whether price reverses before extending?

This is not an unsigned volatility-state test. R5-B already showed that a short/parent volatility displacement is not cross-scale stable. R7 instead asks whether realized movement energy has been disproportionately concentrated **with versus against the direction of the just-completed wave**.

The hypothesis is deliberately agnostic about sign:

- strongly same-direction-dominated energy could represent exhaustion and increase reversal;
- or it could represent coherent state continuation and decrease reversal.

Stage 1 asks only whether the causal asymmetry state adds stable information beyond completed-wave severity.

## Coordinate definition

- **base observation:** official CSI1000 1m close;
- **event scales:** already frozen causal directional-change S1 and S2 completed-wave confirmations;
- **state object:** directional realized-energy balance over a fixed trailing observation window;
- **deviation object:** current asymmetry relative to its own past-only same-scale normal state;
- **price outcome:** symmetric same-scale reversal-first versus extension-first.

## Exact state measurement — one score only

At each completed-wave confirmation time:

1. take the trailing `240` observed 1m bars ending at the confirmation bar;
2. construct adjacent 1m log returns only when the two adjacent observations share the same `trading_day`; cross-session returns are excluded;
3. let `d` be the direction of the just-completed wave (`+1` up, `-1` down);
4. compute squared-return energy for returns aligned with `d` and opposed to `d`:

`E_same = sum(r_t^2 where sign(r_t) == d)`

`E_opp = sum(r_t^2 where sign(r_t) == -d)`

5. define

`directional_energy_balance = (E_same - E_opp) / (E_same + E_opp)`

if total energy is positive and at least `120` valid within-session 1m returns exist.

The score is bounded in `[-1, 1]`.

There is **no second R7 score** and no alternate linear/absolute-return definition in Stage-1 v1.

## Past-only normalization

Within each event scale separately:

- preceding `100` completed same-scale R7 score observations;
- rolling median center;
- rolling MAD scale;
- current observation excluded from its own reference;
- zero/nonfinite MAD observations excluded;
- continuous z-score is primary;
- `abs(z) >= 2` may be reported descriptively only.

No normalization/window/threshold search is allowed.

## Price-path outcome

Reuse the broad-program symmetric same-scale first-passage definition:

- **reversion:** after confirmation, price moves opposite the completed-wave direction by one same-scale threshold from the event price;
- **extension:** price moves in the completed-wave direction by one same-scale threshold;
- maximum horizon: `1200` observed 1m bars;
- unresolved events are censored;
- ambiguous same-bar outcomes are censored;
- do not start another R7 event at the same scale until the prior event resolves or censors.

## Model budget — exactly two objects per scale

1. `severity_only`;
2. `severity_plus_directional_energy_z`.

Estimator is frozen as:

`StandardScaler + LogisticRegression(C=1, penalty=l2, solver=lbfgs, max_iter=1000)`

No interaction, nonlinear transform, sign bucket, threshold classifier, calibration or model search is allowed.

## Evidence roles

Reuse the already frozen broad-program roles:

- DEV: 2015-01-05..2019-12-31;
- chronological stability: 2020-01-01..2022-12-31, not fresh;
- internal reserve: 2023-01-01..2025-12-31, unopened;
- all 2026 rows: unopened.

No Stage-1 result is scientifically fresh.

## Hypotheses

H1. Directional realized-energy asymmetry adds information about reversal-first probability beyond completed-wave severity.

H2. If the state is meaningful rather than a scale accident, the same score should improve the severity baseline at both S1 and S2.

H3. The improvement should appear in multiple held-forward years, not one isolated calendar year.

H4. Any effect should be visible continuously without selecting a lucky z-score threshold.

## Results-blind gate

R7 can become only a `candidate_for_program_review` if all conditions hold:

- at least `200` resolved stability events at each of S1 and S2;
- at least `50` resolved events in each of 2020, 2021 and 2022 at each scale;
- pooled augmented Brier strictly lower than severity-only at S1 and S2;
- pooled augmented log-loss strictly lower at S1 and S2;
- annual Brier improvement positive in at least 2 of 3 stability years at each scale;
- no causal or sealed-boundary violation.

A positive R7 result **does not auto-promote a third mechanism**. R1 and R5-C are already progressed, so R7 must enter a new explicit cross-lane review before any promotion.

## What closes R7 v1

Close R7 if the single score fails the cross-scale gate. Do not rescue by:

- switching from squared returns to absolute returns;
- changing 240 bars;
- using only one direction or one scale;
- adding semivariance ratios, skewness, jump counts or order-flow proxies;
- opening 2023–2025;
- selecting an asymmetry threshold from results.

Any materially different asymmetry concept requires a new identity after program review.

## Explicit non-goals

- no PnL;
- no threshold optimization;
- no alternative asymmetry family;
- no 2023–2025 reserve;
- no 2026;
- no deep model;
- no production authority.
