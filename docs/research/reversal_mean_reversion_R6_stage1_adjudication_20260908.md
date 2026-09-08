# R6 Stage-1 cloud adjudication — 2026-09-08

Research identity: `R6_multiscale_amplitude_state_stage1_v1`

Decision:

`R6_STAGE1_closed_no_multiscale_amplitude_score_qualifies_for_program_review`

## Execution integrity

The first R6 Action attempt failed at synthetic/static tests before any market runner execution. That incident is recorded in:

`docs/governance/reversal_mean_reversion_R6_stage1_execution_incident_v1.json`

No market result was exposed in that attempt. The scientific protocol and runner remained unchanged; only two incorrect test expectations were corrected. A new execution identity was frozen before the first market outcome run:

`docs/governance/reversal_mean_reversion_R6_stage1_execution_freeze_v2.json`

The corrected frozen run executed successfully in GitHub Actions run `34185451407` at head `45efc30037927131d136312ba16b5881b5db5268`.

All steps passed:

- corrected synthetic and boundary tests;
- frozen runner execution;
- reserve/2026/no-auto-promotion verification;
- aggregate artifact upload.

Cloud compact receipt:

`docs/research/cloud_session_20260908_rmr_R6_stage1_action_receipt_v1.json`

## Data boundary

Only CSI1000 1m rows through `2022-12-30` were loaded:

- rows loaded: `466,961`;
- DEV: 2015–2019;
- chronological stability: 2020–2022, not fresh;
- 2023–2025 reserve: unopened;
- all 2026 rows: unopened.

No amplitude-band search, lookback search, z-threshold search, combined-score model, FFT/wavelet family search, scale search, hyperparameter search, PnL, calibration, deep model or automatic third promotion was used.

## R6-A — short-to-mid amplitude concentration

Score:

`log(amp_4 / amp_16)`

### S1

- stability resolved events: `2,329`;
- severity baseline Brier `0.25015489`;
- augmented Brier `0.25020099`;
- augmented-minus-baseline Brier `+0.00004610` — worse;
- log-loss delta `+0.00009387` — worse;
- annual Brier: improves only in 2020, worsens in 2021 and 2022.

### S2

- stability resolved events: `831`;
- baseline Brier `0.24904271`;
- augmented Brier `0.25095131`;
- Brier delta `+0.00190860` — materially worse relative to the tiny Stage-1 effects under study;
- log-loss delta `+0.00383473` — worse;
- all three stability years worsen.

The score itself shows descriptive normalization decay, but that does not provide useful cross-scale price-path information.

Decision:

`close_R6_A`

## R6-B — mid-to-parent amplitude concentration

Score:

`log(amp_16 / amp_64)`

### S1

S1 alone is mildly positive:

- stability resolved events: `2,329`;
- baseline Brier `0.25015489`;
- augmented Brier `0.25013111`;
- delta `-0.00002378`;
- log-loss delta `-0.00004800`;
- annual Brier improves in 2020 and 2022, worsens in 2021.

Therefore the S1 local gate passes.

### S2

The same score fails at the coarser predeclared scale:

- stability resolved events: `831`;
- baseline Brier `0.24904271`;
- augmented Brier `0.24961357`;
- delta `+0.00057086` — worse;
- log-loss delta `+0.00114361` — worse;
- worsens in 2020 and 2021, with only a tiny improvement in 2022.

The frozen R6 gate required the same score to improve pooled Brier and log-loss at **both S1 and S2**, with at least 2/3 annual Brier improvements at each scale. S1 cannot rescue S2.

Decision:

`close_R6_B`

## Overall decision

No score qualifies:

- `qualified_score_ids = []`;
- `ranked_for_review = []`;
- `third_mechanism_auto_promotion = false`.

The mean cross-scale pooled improvements are negative for both scores because the augmented model is worse on average:

- R6-A mean Brier improvement: `-0.00097735`;
- R6-B mean Brier improvement: `-0.00027354`.

R6 Stage-1 v1 is therefore **closed**.

## Scientific interpretation

The fixed 4/16/64 amplitude-curve shape does not show a robust cross-scale incremental reversal/continuation signal beyond completed-wave severity under this causal measurement.

This does **not** prove that all frequency-domain information is useless. It does mean this identity may not be rescued by:

- changing 4/16/64 after seeing results;
- adding more bands;
- trying FFT/wavelet decompositions on the same consumed window;
- combining R6-A and R6-B;
- selecting only S1;
- opening 2023–2025 to find a favorable configuration.

Any future frequency-domain study must be a genuinely new results-blind identity with independent scientific motivation, not R6 post-hoc rescue.

The 2023–2025 reserve remains unopened.

Production authority remains `false`.
