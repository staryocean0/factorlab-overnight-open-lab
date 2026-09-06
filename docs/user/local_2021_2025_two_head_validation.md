# Local Controller Handoff — Fresh 2021-2025 Two-Head Validation

## Execution status

This window was opened once on 2026-09-06.

- fit freeze: `docs/research/cloud_session_20260906_local_2021_2025_fit_freeze_v1.json`
- receipt: `docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json`
- decision: `research_candidate_local_2021_2025_confirmed`
- `fresh_oos=true` for that receipt only
- `production_authority=false`

Do not retune features, alphas, thresholds, calendar exceptions or the magnitude
head on 2021-2025. A later run may only reproduce the frozen receipt.

## Mission

Run exactly one fresh local confirmation of the frozen two-head CSI1000 overnight-open candidate on 2021-2025 data.

Do **not** use 2021-2025 for training, calibration, feature selection, threshold search, alpha search, calendar exceptions, or model choice.

Authoritative protocol:

`docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json`

Frozen candidate:

`docs/governance/cloud_session_20260906_two_head_selected_v1.json`

Candidate SHA256:

`76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f`

## Before opening 2021+ targets

1. Verify the repository package validator and tests pass.
2. Verify all 2015-2020 source files and target definitions match the current repository contract.
3. Verify the frozen candidate SHA and exact feature lists.
4. Build the causal US-clock features with the frozen rule:
   - for China day `D` and previous China trading day `P`, use the last completed US close strictly before `D` versus the last completed US close strictly before `P`;
   - zero intervening US sessions => interval return = 0;
   - multiple intervening US sessions => cumulative interval return;
   - do not use same-morning China information.
5. Fit both frozen heads using **2015-2020 only**.

## Frozen direction head

Pipeline:

`StandardScaler + Ridge(alpha=1.0)`

Target:

`gap`

Features:

- `r1`
- `r20`
- `abs_r1`
- `prev_gap`
- `overnight_trend_5`
- `prev_daytime`
- `prev_last_hour`
- `prev_afternoon`
- `rvol20`
- `weekend`
- `holiday_reopen`
- `us_nasdaq`
- `us_vix_chg`

Direction output:

`direction_up = baseline_prediction >= 0`

## Frozen magnitude head

Pipeline:

`StandardScaler + Ridge(alpha=100.0)`

Fit target:

`gap`

Features:

- `r1`
- `r20`
- `abs_r1`
- `prev_gap`
- `overnight_trend_5`
- `prev_daytime`
- `prev_last_hour`
- `prev_afternoon`
- `rvol20`
- `weekend`
- `holiday_reopen`
- `us_nasdaq_interval`
- `us_vix_interval`
- `us_session_count`
- `us_nasdaq_interval_x_holiday`
- `us_vix_interval_x_holiday`

Magnitude output:

`magnitude = abs(clock_signed_prediction)`

Secondary signed-gap output only:

`signed_gap = (+1 if direction_up else -1) * magnitude`

## Fresh validation window

Open the target only after both models are fitted and frozen:

`2021-01-01` through `2025-12-31`.

Do not alter anything after viewing these results.

## Required primary metrics

For both the two-head candidate and the same-refit baseline comparator, report:

- direction hit;
- correlation between predicted magnitude and `abs(gap)`;
- MAE of predicted magnitude versus `abs(gap)`;
- RMSE of predicted magnitude versus `abs(gap)`.

The candidate direction hit must equal the baseline direction hit exactly because the direction head is the baseline itself.

## Required secondary reporting

Also report:

- signed-gap IC;
- signed-gap MAE;
- signed-gap RMSE;
- tail (`abs(gap) > 0.003`) direction hit;
- tail magnitude MAE;
- tail magnitude RMSE;
- the four primary metrics separately for each full year 2021, 2022, 2023, 2024 and 2025.

These secondary metrics do not authorize parameter changes.

## Frozen pass gate

The candidate passes fresh local confirmation only if all of the following hold:

1. candidate direction hit equals baseline direction hit exactly;
2. pooled `corr(predicted magnitude, abs(gap))` is higher than baseline;
3. pooled magnitude MAE is lower than baseline;
4. pooled magnitude RMSE is lower than baseline;
5. magnitude correlation is positive in every full validation year;
6. candidate beats baseline on **both** magnitude MAE and magnitude RMSE in at least 3 of the 5 validation years.

Trading return is not part of this gate.

## Decision semantics

If the gate passes:

- record status as `research_candidate_local_2021_2025_confirmed`;
- production authority still remains `false` until a separate production review.

If the gate fails:

- retain the frozen baseline;
- record the two-head candidate as not confirmed;
- do not retune using 2021-2025 within the same evidence cycle.

## Return receipt

Write a machine-readable receipt containing at minimum:

- exact data hashes / snapshot identifiers;
- candidate SHA256;
- fit window and validation window;
- row counts and missing-data mask counts;
- all primary and secondary metrics;
- per-year metrics;
- pass/fail for every gate condition;
- final decision;
- explicit flags: `fresh_oos=true` for the 2021-2025 validation receipt only, and `production_authority=false`.

Do not upload raw 2021-2025 data into this bounded repository unless the package boundary is explicitly revised first.
