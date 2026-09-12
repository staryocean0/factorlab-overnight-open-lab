# GFV2-R1 — Gap-Fill V2 2026 repeat-only validation handoff

## Status

**Cloud design and execution identity are frozen. The user later authorized a public in-repo 2026 pack, so the cloud evaluator can now run without a local FactorLab/DataHub absolute path.**

Research identity: `gap_fill_prediction_v2`.

Scientific role: **repeat-only temporal validation, not fresh OOS**.

Frozen validation window: `2026-01-05 .. 2026-08-21`.

Post-2026-08-21 remains true unread fresh evidence and must not be loaded.

## Frozen model identity

- architecture SHA256: `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`
- parameter bundle SHA256: `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`
- parameter artifact: `docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json`
- repeat protocol: `docs/governance/cloud_session_20260906_gap_fill_v2_2026_repeat_protocol_v1.json`
- execution freeze: `docs/governance/cloud_session_20260906_gap_fill_v2_2026_repeat_execution_freeze_v1.json`
- evaluator: `scripts/evaluate_local_gap_fill_v2_2026_repeat.py`

The evaluator performs **no model/scaler refit**. It applies the sealed scaler means/scales and Logistic coefficients/intercepts directly.

## Required local data

The user-authorized public pack is:

- `data/gap_fill_repeat_2026/annotated_panel_2025Q4_to_20260821.parquet`
- `data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet`

Set exactly two source paths. From this repository root:

```bash
export OVERNIGHT_ANNOTATED_PANEL="$PWD/data/gap_fill_repeat_2026/annotated_panel_2025Q4_to_20260821.parquet"
export OVERNIGHT_DATAHUB_1M="$PWD/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
```

`OVERNIGHT_ANNOTATED_PANEL` must contain:

- enough pre-2026 `close_1500` history to compute the frozen prior-20-session `rvol20`;
- 2026-01-05..2026-08-21 `open_0931`, `prev_close`, `close_1500`, `overnight_gap` rows.

`OVERNIGHT_DATAHUB_1M` must contain 000852.SH one-minute OHLC rows for the complete frozen repeat window, including all 09:31..15:00 trading-minute bars needed to construct the targets.

Do **not** load or commit any row after 2026-08-21. The frozen evaluator, protocol, tests and parameter artifact stay unmodified.

## Frozen commands

Run from repository root, after updating to the execution-freeze commit or a descendant that has not modified the frozen protocol/runner/tests/parameter artifact:

```bash
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/evaluate_local_gap_fill_v2_2026_repeat.py
```

No other modeling command is authorized before the repeat receipt is returned to cloud review.

## Frozen repeat gate

For each sign head independently (`high`, `low`), the sealed V2 model is compared with a **fixed 2015–2025 empirical stage-hazard benchmark**. The benchmark is not re-estimated on 2026.

A sign head is repeat-confirmed only if all six frozen gates pass:

1. pooled all-gap integrated Brier strictly beats benchmark;
2. pooled all-gap integrated log loss strictly beats benchmark;
3. >10bp integrated Brier strictly beats benchmark;
4. >30bp integrated Brier is not worse than benchmark;
5. >10bp Brier beats benchmark at at least 2 of 3 horizons;
6. zero cumulative-probability monotonicity violations.

Overall decision:

- both signs pass → `gap_fill_v2_2026_repeat_robustly_confirmed`;
- exactly one passes → `gap_fill_v2_2026_repeat_partially_confirmed`;
- neither passes → `gap_fill_v2_2026_repeat_not_confirmed`.

This decision is repeat evidence only. It cannot authorize retuning or production.

## Hard denylist after the window is opened

Do not:

- refit any V2 model or scaler on 2026;
- fit/apply a probability calibration layer;
- change features, coefficients, horizons, horizon weights or gates;
- change 10bp/30bp definitions or choose between them by result;
- select a binary probability threshold;
- use trading PnL as a gate;
- modify V1 or V2 based on this repeat result;
- load any row after 2026-08-21;
- label this validation `fresh_oos`.

Descriptive calibration intercept/slope may be reported, but no calibrated probabilities may replace the sealed predictions.

## Expected repository outputs

Only aggregate outputs should be committed:

- `docs/research/cloud_session_20260906_local_gap_fill_v2_2026_repeat_receipt_v1.json`
- `docs/governance/local_session_20260906_gap_fill_v2_2026_repeat_data_usage_v1.json`

Do not commit raw target rows or raw predictions. The user-authorized input pack in `data/gap_fill_repeat_2026/` is the only allowed 2026 raw-row exception.

## Return to cloud for acceptance

Return/commit the two aggregate outputs above and report:

1. execution commit SHA;
2. validator exit code;
3. pytest exit code and passed count;
4. evaluator exit code;
5. exact local source SHA256 values recorded by the receipt;
6. validation min/max day and target-valid/invalid counts;
7. repeat row counts: total/high/low and >10bp/>30bp by sign;
8. for each sign: model vs frozen benchmark integrated Brier/log-loss for all, >10bp and >30bp;
9. all six gate booleans and `repeat_confirmed` per sign;
10. overall `decision`;
11. confirmation that `post_2026_08_21_rows_loaded=false`, no refit/search/calibration layer/trading-return gate occurred, and no additional raw 2026 rows were committed beyond `data/gap_fill_repeat_2026/`.

Cloud will independently inspect the returned aggregate receipts and frozen-code identity before accepting the repeat result.
