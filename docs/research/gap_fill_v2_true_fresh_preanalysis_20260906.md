# Gap-Fill Prediction V2 v1 — true-fresh challenge preanalysis — 2026-09-06

## Purpose

Freeze the first scientifically fresh validation of the already-selected and already-parameter-frozen `gap_fill_prediction_v2` model **before any post-2026-08-21 fill target or model score is opened**.

This document does not authorize model redesign. The model remains:

- architecture SHA256 `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`;
- parameter bundle SHA256 `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`;
- separate high-gap and low-gap three-stage discrete-time hazards;
- runtime features exactly `abs_gap` and `abs_gap_over_rvol20`;
- no binary threshold and no probability-calibration layer.

The 2026-01-05..2026-08-21 window is already consumed repeat-only evidence. It must not be mixed into the fresh score or used to refit/calibrate the model.

## Why wait for a complete calendar block

On 2026-09-06 only a very short post-2026-08-21 period exists. Opening it now and later extending the same challenge would create sequential peeking and make the stopping rule outcome-dependent.

Therefore the first true-fresh block is frozen now as:

`2026-08-24 .. 2026-12-31`

The block may be opened only after the final session in that window is complete and the required source pack is finalized. No partial-window score is authorized.

## Frozen benchmark and gates

The fresh challenge deliberately reuses the **same fixed 2015-2025 empirical stage-hazard benchmark** and the **same six confirmation gates** preregistered for the 2026 repeat-only test. The repeat outcomes do not alter the benchmark, metrics, gap cohorts, horizon weights or gates.

For each sign head independently:

1. all-gap integrated Brier must be strictly lower than the fixed benchmark;
2. all-gap integrated log loss must be strictly lower than the fixed benchmark;
3. >10bp integrated Brier must be strictly lower than the fixed benchmark;
4. >30bp integrated Brier must be no higher than the fixed benchmark;
5. >10bp Brier must beat the benchmark at at least two of the three horizons;
6. cumulative-probability monotonicity violations must equal zero.

Secondary AUC/PR-AUC and descriptive calibration statistics are reported but cannot override these gates.

## Frozen sample-sufficiency rule

A sign head receives a confirm/reject judgment only if its fresh inventory contains at least:

- 25 nonzero-gap rows in total;
- 20 rows with `abs_gap > 10bp`;
- 12 rows with `abs_gap > 30bp`.

These counts use only the observed 09:31 gap state and do not inspect later fill outcomes. If a sign does not meet the counts, that sign is labeled `fresh_evidence_insufficient`; the window is **not extended** and no threshold is relaxed after seeing results.

Overall status:

- both signs sufficient and 6/6 pass → `gap_fill_v2_true_fresh_robustly_confirmed`;
- exactly one sign sufficient and 6/6 pass → `gap_fill_v2_true_fresh_partially_confirmed`;
- at least one sign sufficient but no sign passes all six gates → `gap_fill_v2_true_fresh_not_confirmed`;
- neither sign sufficient → `gap_fill_v2_true_fresh_evidence_insufficient`.

## Data boundary

Feature history before 2026-08-24 may be loaded only to compute the frozen prior-20-session `rvol20`. Target evaluation begins strictly on 2026-08-24.

The fresh source must contain the complete target window through 2026-12-31 and all required 09:31..15:00 one-minute bars for every target day represented by the panel. The evaluator must reject incomplete geometry rows or incomplete target construction rather than impute.

No row after 2026-12-31 belongs to this first fresh challenge.

## Hard prohibition after the fresh block is opened

Regardless of result, do not:

- refit model or scaler on the fresh block;
- fit or apply a calibration layer using fresh outcomes;
- change features, coefficients, gap thresholds, horizons, horizon weights or acceptance gates;
- select a binary probability threshold;
- use trading PnL as an acceptance gate;
- fold fresh rows into training and then call the same evidence fresh again;
- extend the 2026-12-31 endpoint because a sign fails or has weak results.

A failed or partial fresh result is evidence, not permission for post-hoc rescue under the same model identity.

Production authority remains false.
