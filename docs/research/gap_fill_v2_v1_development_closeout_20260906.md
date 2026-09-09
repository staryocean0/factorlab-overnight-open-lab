# Gap-Fill Prediction V2 v1 — development closeout — 2026-09-06

## Status

Research identity: `gap_fill_prediction_v2`.

Development status: **V2 v1 selected and final development parameters frozen.**

This is a prediction-model milestone, not a trading-strategy or production authorization.

Selected architecture SHA256:

`07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`

Final parameter bundle SHA256:

`07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`

No 2026 row was loaded in the final fit. The 2026-01-05..2026-08-21 window remains unopened for this V2 identity and is repeat-only if a later protocol explicitly authorizes it. Post-2026-08-21 remains unread true-fresh evidence.

## V2 v1 prediction question

At 09:31 China time, after the CSI1000 opening gap is observed, predict the probability that the previous China trading day's 15:00 close is revisited:

- within the first 15 trading minutes;
- within the first 60 trading minutes;
- by EOD.

High opens and low opens use separate heads because their fill base rates and mechanisms are materially asymmetric.

## Selected model

Both high-gap and low-gap heads selected the same two-feature geometry state:

1. `abs_gap`;
2. `abs_gap_over_rvol20`.

No V1 direction score, FRED series, offshore ETF signal, auction variable or post-09:31 China feature is required at runtime.

For each sign there are three fixed discrete-time hazard stages:

- `h15 = P(fill by 15m | I_09:31)`;
- `h60 = P(fill between 15m and 60m | not filled by 15m, I_09:31)`;
- `hEOD = P(fill between 60m and EOD | not filled by 60m, I_09:31)`.

Cumulative probabilities are:

- `p15 = h15`;
- `p60 = 1-(1-h15)*(1-h60)`;
- `pEOD = 1-(1-h15)*(1-h60)*(1-hEOD)`.

Therefore `p15 <= p60 <= pEOD` by construction.

Every stage uses exactly:

`StandardScaler + LogisticRegression(C=1, penalty=L2, solver=lbfgs, class_weight=None)`.

There is no selected binary threshold and no fitted probability calibration layer.

## Why the model is geometry-only

Phase-1 showed that V1 direction support, Nasdaq/VIX support and, for high gaps, prior-China continuation variables have stable univariate mechanism relationships with fill outcomes.

Phase-2 asked the stricter question: do these variables improve out-of-sample probability quality beyond the observed gap geometry itself?

The answer was no under the frozen admission gates.

For both signs, geometry-only decisively beat an expanding empirical stage-hazard benchmark and improved >10bp integrated Brier score in 9/9 OOF years. The larger Phase-1 full models failed their preregistered incremental gates and were rejected rather than rescued post hoc.

The full Phase-2 adjudication is:

`docs/research/gap_fill_v2_phase2_hazard_adjudication_20260906.md`

## Final development parameter fit

Cloud run: `34034618914`.

Execution integrity:

- exact protocol / selected architecture / runner / tests / execution-freeze Git blobs passed;
- exact annotated-panel and official-1m source SHA256 checks passed;
- dependency versions were pinned;
- package validator passed;
- pytest: 46 passed;
- final fit performed no model, feature, hyperparameter, threshold or calibration selection;
- 2026 rows loaded: false;
- 2026 repeat validation opened: false.

The final geometry inventory contained 2,650 complete rows. Of 2,670 target-valid days, 20 early rows lacked a valid prior-20-session volatility because the required rolling history had not yet formed. The final model inventory begins on 2015-02-03 and ends on 2025-12-31. Feature/target gap identity matched exactly (`max_abs = 0`).

### High-gap head

Total sign rows: 1,067.

| stage | risk-set n | fill events | stage event rate |
|---|---:|---:|---:|
| 15m | 1,067 | 469 | 0.43955 |
| 15->60m | 598 | 136 | 0.22742 |
| 60m->EOD | 462 | 117 | 0.25325 |

Final standardized-logistic parameters are stored, not rounded, in:

`docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json`.

### Low-gap head

Total sign rows: 1,583.

| stage | risk-set n | fill events | stage event rate |
|---|---:|---:|---:|
| 15m | 1,583 | 787 | 0.49716 |
| 15->60m | 796 | 252 | 0.31658 |
| 60m->EOD | 544 | 175 | 0.32169 |

The exact scaler means/scales/variances and logistic coefficients/intercepts are sealed in the same parameter artifact.

## Runtime contract

At 09:31 the model needs only:

1. observed gap = `09:31 open / previous 15:00 close - 1`;
2. `rvol20`, computed from prior close-to-close daily returns only.

Compute:

- `abs_gap = abs(gap)`;
- `abs_gap_over_rvol20 = abs_gap / rvol20`.

Choose the high or low head from the observed gap sign, evaluate its three stage logistic models using the sealed stage-specific scalers, and combine stage hazards into `p15`, `p60`, `pEOD` with the frozen cumulative formulas.

## Parameter identity

Final parameter artifact:

`docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json`

Parameter bundle SHA256:

`07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`

Pinned execution environment:

- Python 3.11.16;
- NumPy 2.4.6;
- pandas 3.0.5;
- SciPy 1.17.1;
- scikit-learn 1.9.0;
- pyarrow 25.0.1.

The scikit-learn run emitted only a forward-looking deprecation warning for the explicit `penalty='l2'` argument. This did not alter execution or parameter identity; the exact library version and parameters are frozen.

## Evidence boundary and next scientific step

Development evidence is now consumed through 2025-12-31 for this V2 v1 identity.

The model must not be retuned on 2026 based on repeat-validation outcomes.

A **separate preregistered repeat-validation protocol** may next evaluate the already-frozen parameter bundle on 2026-01-05..2026-08-21. That window is not scientifically fresh because it was previously opened by the older direction-head research cycle, but it can provide useful repeat-only temporal evidence for this new target/model identity.

True fresh evidence remains post-2026-08-21.

Production authority remains false.
