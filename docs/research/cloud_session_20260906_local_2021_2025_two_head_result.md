# Local 2021-2025 Two-Head Confirmation

Status: `research_candidate_local_2021_2025_confirmed`

Production authority: `false`

This is the one-shot local fresh confirmation required by
`docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json`.
Both frozen heads were fitted on 2015-2020 before any 2021-2025 target was
scored. Features, alphas, direction threshold, calendar exceptions and the
magnitude head were not changed after the window opened. Trading return was
not used in the gate.

## Fit freeze

- candidate SHA256: `76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f`
- direction head: `StandardScaler + Ridge(alpha=1.0)` on the frozen baseline features
- magnitude head: `StandardScaler + Ridge(alpha=100.0)` on the frozen clock-holiday-interaction features; magnitude = `abs(prediction)`
- n_fit_direction = n_fit_magnitude = 1437 out of 1462 development rows
- 2015-2020 reconstruction from the local annotated panel, DataHub 1m export and FRED prints matched the frozen package panel with maximum absolute error 0 on every contracted column
- freeze file: `docs/research/cloud_session_20260906_local_2021_2025_fit_freeze_v1.json`

## Fresh window

- 2021-01-01 through 2025-12-31
- actual trading days: 2021-01-04 through 2025-12-31
- n_validation_rows = n_validation_complete = 1212
- dropped missing = 0
- raw 2021-2025 rows were not written into this bounded repository

## Primary gate

| Metric | baseline | two-head | gate |
|---|---:|---:|---|
| direction hit | 0.693069 | 0.693069 | equal |
| corr(\|gap\|) | 0.319940 | 0.521871 | candidate higher |
| MAE(\|gap\|) | 0.002417 | 0.002400 | candidate lower |
| RMSE(\|gap\|) | 0.005410 | 0.005094 | candidate lower |

Year robustness:

| Year | n | candidate corr(\|gap\|) | beat both MAE and RMSE |
|---|---:|---:|---|
| 2021 | 243 | 0.464119 | no |
| 2022 | 242 | 0.483800 | yes |
| 2023 | 242 | 0.177664 | yes |
| 2024 | 242 | 0.535693 | yes |
| 2025 | 243 | 0.804769 | no |

Magnitude correlation is positive in every full validation year. The candidate
beats baseline on both magnitude MAE and RMSE in 3 of 5 years (2022, 2023,
2024). 2021 and 2025 raise correlation but not error. No calendar exception or
magnitude-head change is authorized from those two years.

## Secondary reporting only

These numbers do not authorize retuning.

- signed-gap IC: baseline 0.378858, candidate 0.346939
- signed-gap MAE: baseline 0.003086, candidate 0.003103
- signed-gap RMSE: baseline 0.006132, candidate 0.006859
- tail `|gap|>30bp` n = 374; direction hit 0.818182 for both; candidate tail MAE/RMSE 0.004113 / 0.008436 versus baseline 0.004141 / 0.009099

The signed-gap IC decline is consistent with the earlier consumed-holdout
finding: direction and magnitude are separate tasks. The confirmation gate was
written on direction hit plus magnitude correlation/error, not signed-gap IC
or trading return.

## Authority

- `fresh_oos=true` for this receipt only
- `production_authority=false`
- 2021-2025 is now consumed as the fresh challenge of this frozen two-head
  identity and may not be used to retune it in the same evidence cycle
- repository visibility was restored to private before the receipt was written

Machine-readable receipt:
`docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json`
