# R1 specialist v2 — parent-integrity representation preanalysis

Date: 2026-09-08  
Identity: `rmr_cross_scale_pullback_parent_integrity_v2`

This is the dedicated mechanism identity graduated from broad R1. It is **not** a trading-strategy optimization stage.

## Carried scientific claim

For a counter-move of comparable severity, causally available parent structure adds information about whether price recovers the counter-move before the parent structure fails.

The broad screen established incremental information but used three parent measurements together. The specialist first asks whether that state can be compressed into one interpretable integrity coordinate without losing the mechanism.

## Event identity — unchanged

Reuse exactly the broad R1 causal construction:

- directional-change thresholds from DEV median 20-day volatility;
- pairings `S1 inside S2` and `S2 inside S3`;
- only lower-scale waves opposite the parent sign;
- parent sign from the signed drift of the last two causally confirmed parent waves;
- recovery boundary = lower-wave start price;
- failure boundary = frozen structural boundary derived from the last two parent waves;
- maximum first-passage horizon = 1200 observed 1m bars;
- overlapping events suppressed until prior event resolves/censors;
- target = recovery-first versus failure-first.

No event, scale or outcome boundary search is allowed.

## Evidence roles for representation selection

- source: CSI1000 1m, exact existing SHA;
- DEV: 2015-01-05..2019-12-31;
- chronological stability: 2020-01-01..2022-12-31, not fresh;
- 2023-01-01..2025-12-31: **must remain unread during representation selection**;
- all 2026 rows: unread.

## Baseline

`severity_only = [severity]`

where severity remains `abs(lower_wave.move) / DEV_median_rvol20`.

## Candidate 1 — simple composite first

Within each scale pairing separately, fit parent-feature standardization on DEV events only:

- `z_drift = z(abs_drift)`;
- `z_overlap = z(overlap)`;
- `z_eff = z(parent_eff)`.

Freeze equal outcome-blind weights:

`parent_integrity = (z_drift - z_overlap + z_eff) / 3`.

The sign is fixed by structural interpretation before results:

- more net parent drift = higher integrity;
- more wave overlap = lower integrity;
- greater parent path efficiency = higher integrity.

Candidate model:

`[severity, parent_integrity]`.

No weight fitting is allowed.

## Candidate 2 — original broad representation

Only if Candidate 1 fails the full gate, test the original broad representation:

`[severity, abs_drift, overlap, parent_eff]`.

This is not a new feature search; it is the carried Stage-1 incumbent representation.

## Estimator

For baseline and candidates:

`StandardScaler + LogisticRegression(C=1, penalty=l2, solver=lbfgs, max_iter=1000)`.

No calibration, threshold selection, class weights or hyperparameter search.

## Eligibility gate — required at both scale pairings

A representation is eligible only if:

1. stability resolved events >= 200 at each pairing;
2. resolved stability events >= 50 in each of 2020, 2021 and 2022 at each pairing;
3. pooled Brier is strictly lower than severity-only at both pairings;
4. pooled log loss is strictly lower than severity-only at both pairings;
5. annual Brier improvement is positive in at least 2 of 3 stability years at each pairing;
6. the fitted parent-integrity direction is positive at both pairings.

Direction gate:

- composite candidate: standardized logistic coefficient on `parent_integrity` > 0;
- original-three candidate: standardized coefficient projection `coef(abs_drift) - coef(overlap) + coef(parent_eff) > 0`.

## Selection rule

Complexity-first and stop early:

1. if composite passes all gates, select composite and **do not use original-three scores to replace it**;
2. otherwise test original-three;
3. if original-three passes, select original-three;
4. if neither passes, close `rmr_cross_scale_pullback_parent_integrity_v2` before any 2023–2025 access.

## Post-selection freeze before holdout

If one representation is selected:

- refit the selected candidate and severity baseline on all consumed 2015–2022 events;
- for the selected composite, refit constituent mean/std on all 2015–2022 training events with the same fixed equal-weight formula;
- freeze all scaler parameters, logistic coefficients/intercepts, event thresholds and source identity;
- write a parameter bundle and digest;
- **do not open 2023–2025 in the same execution**.

A separate holdout authorization is mandatory.

## Forbidden

- tune integrity weights;
- add trend indicators;
- change parent features;
- change wave scales;
- choose a trend/range threshold;
- inspect 2023–2025 during candidate choice;
- select by trading PnL;
- add entry/stop/holding period;
- rescue failure with nonlinear/deep models.

Production authority remains `false`.
