# Gap-Fill Prediction V2 v1 — 2026 repeat-only cloud adjudication — 2026-09-06

## Decision

Research identity: `gap_fill_prediction_v2`.

Decision: **`gap_fill_v2_2026_repeat_robustly_confirmed`**.

Both frozen sign heads (`high`, `low`) passed all six preregistered repeat-confirmation gates on the fixed `2026-01-05 .. 2026-08-21` window.

This is **repeat-only temporal evidence, not fresh OOS**. The window had already been opened in the earlier direction-head research cycle. It therefore cannot be promoted to fresh evidence for V2 and cannot authorize retuning or production.

Frozen model identity:

- selected architecture SHA256: `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`;
- final parameter bundle SHA256: `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`;
- runtime features: `abs_gap`, `abs_gap_over_rvol20` only;
- separate high/low three-stage discrete-time fill hazards;
- no binary threshold or calibration layer.

## Execution integrity

The cloud first attempted direct current-session execution. Repository checkout failed before any target was loaded because the container could not resolve `github.com`. After the user had made the exact repeat pack available on public `main`, an execution-location-only authorization was recorded and GitHub Actions was used as the last-resort cloud execution location under the active cloud-local protocol.

### First cloud run

Run: `34038663086`.

Before evaluation:

- frozen protocol / evaluator / tests / parameter artifact Git blobs matched the pre-open execution freeze;
- repeat annotated-panel SHA256 matched `4619b00670b9443d0c0de7dd8a3a7a2d664a3c8907f28b0f997c9ae737cae216`;
- repeat 1m SHA256 matched `307e48021ef4576c2b364a1309a8b0474d6ab783afee16be41edb975abaa6dcd`;
- manifest confirmed 154 validation days and no post-2026-08-21 row;
- theme validator passed;
- pytest: 52 passed.

The frozen evaluator itself exited successfully and printed:

`gap_fill_v2_2026_repeat_robustly_confirmed`, 154 rows, 79 high, 75 low, both heads confirmed, `fresh_oos=false`, `post_2026_08_21_rows_loaded=false`.

The job then failed **after** evaluation because the workflow's receipt-verification wrapper referenced a stale/nonexistent receipt key (`trading_return_used_in_gate`) and stale output paths. No scientific code or gate failed. The first-run aggregate receipt was not committed. This post-evaluation incident is sealed in:

`docs/governance/cloud_session_20260906_gap_fill_v2_2026_repeat_execution_incident_v1.json`.

### Mechanical recovery run

Run: `34038784522`.

Only the workflow's post-evaluation receipt-schema verification / commit plumbing was corrected. Protocol, evaluator, tests, parameter artifact, parameter bundle, data bytes, validation window and all six confirmation gates remained unchanged.

The recovery run again passed all scientific/data identity checks, validator and tests, re-executed the identical frozen evaluator, passed the corrected post-evaluation schema checks and committed only the two aggregate receipts:

- `docs/research/cloud_session_20260906_local_gap_fill_v2_2026_repeat_receipt_v1.json`;
- `docs/governance/local_session_20260906_gap_fill_v2_2026_repeat_data_usage_v1.json`.

Receipt commit: `a97fe9cf1ed1ade5792971ab58c0b4979d368bf2`.

The second run is mechanical recovery evidence, not a second independent statistical validation.

## Validation inventory

Frozen window: `2026-01-05 .. 2026-08-21`.

- panel validation days: 154;
- target-valid days: 154;
- invalid target days: 0;
- repeat rows: 154;
- high-gap rows: 79;
- low-gap rows: 75;
- high >10bp: 65;
- high >30bp: 43;
- low >10bp: 69;
- low >30bp: 59;
- cumulative probability monotonicity violations: 0 for both heads.

## High-gap head

The sealed geometry model beat the frozen 2015-2025 empirical stage-hazard benchmark on every preregistered gate.

| cohort | benchmark integrated Brier | model integrated Brier | absolute improvement | relative Brier reduction |
|---|---:|---:|---:|---:|
| all | 0.240718 | 0.182450 | 0.058268 | 24.2% |
| >10bp | 0.245155 | 0.180877 | 0.064278 | 26.2% |
| >30bp | 0.259322 | 0.185629 | 0.073693 | 28.4% |

All-gap integrated log loss improved from `0.674327` to `0.539778`, an absolute reduction of `0.134548` (about 20.0% relative).

For >10bp gaps, all three horizon Brier scores beat the benchmark:

- 15m improvement: `0.058716`;
- 60m improvement: `0.051675`;
- EOD improvement: `0.082444`.

High-head repeat gate: **6/6 true**.

## Low-gap head

The sealed low-gap geometry model also passed every preregistered gate.

| cohort | benchmark integrated Brier | model integrated Brier | absolute improvement | relative Brier reduction |
|---|---:|---:|---:|---:|
| all | 0.226705 | 0.190677 | 0.036029 | 15.9% |
| >10bp | 0.234092 | 0.203770 | 0.030322 | 13.0% |
| >30bp | 0.249741 | 0.222332 | 0.027409 | 11.0% |

All-gap integrated log loss improved from `0.645670` to `0.569416`, an absolute reduction of `0.076254` (about 11.8% relative).

For >10bp gaps, all three horizon Brier scores beat the benchmark:

- 15m improvement: `0.032218`;
- 60m improvement: `0.019954`;
- EOD improvement: `0.038795`.

Low-head repeat gate: **6/6 true**.

## Scientific interpretation

The repeat result materially strengthens the V2 v1 geometry finding. The predictor was selected on 2017-2025 expanding-year OOF and then fit once on the allowed 2015-2025 development window. Without any V2 refit, scaler refit, feature change, threshold choice or calibration layer, it retained useful probability skill in the later 2026 temporal window for both gap signs and for large-gap cohorts.

The 2026 evidence is especially supportive because:

1. both sign heads pass, rather than only one side;
2. the >30bp cohorts remain positive versus the fixed benchmark;
3. the >10bp horizon improvements are positive at all three horizons for both signs;
4. the cumulative hazard construction has zero monotonicity violations.

This does **not** imply that the model is fully fresh-confirmed. The correct status is:

> **Gap-Fill V2 v1: development-selected, final-parameter-frozen, and robustly repeat-confirmed on the consumed 2026-01-05..2026-08-21 window.**

## Evidence boundary

The repeat evaluator and receipt confirm:

- `model_refit_performed=false`;
- `scaler_refit_performed=false`;
- `feature_selection_performed=false`;
- `hyperparameter_search_performed=false`;
- `threshold_search_performed=false`;
- `probability_calibration_layer_fit_or_applied=false`;
- `trading_return_used=false`;
- `raw_2026_rows_written_to_repo=false` by the evaluator (the user-authorized input pack itself is separately present in the public repo);
- `post_2026_08_21_rows_loaded=false`;
- `fresh_oos=false`;
- `production_authority=false`.

The model must not be changed in response to these repeat results. Post-2026-08-21 remains the true-fresh boundary for this V2 identity. No result from this repeat window may be used to change features, parameters, thresholds, calibration, horizons or acceptance gates before a future fresh challenge.
