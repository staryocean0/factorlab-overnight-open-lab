# OFP-A1 expected-open validated-driver coordinate adapter v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_expected_open_validated_driver_coordinates_v1`

Training window: `2015-01-05..2018-12-31`.

Development evaluation window: `2019-01-01..2020-12-31`.

## Frozen comparison

Comparator: frozen V6A `StandardScaler + Ridge(alpha=1.0)` feature set, refit on the candidate-complete common sample.

Candidate: the same estimator and V6A feature set plus exactly the already validated B1 `global_risk_z` and B2 `china_offshore_z` continuous coordinates.

No Ridge-alpha, scaler, upstream add/drop, interaction, threshold, bucket, clock or target search occurred. B3 and B4 were excluded before outcomes.

## Development result

Sufficiency passes: training common complete cases = **899**; evaluation common complete cases = **461** with **230** in 2019 and **231** in 2020.

The candidate improves IC and remains within sign-accuracy tolerance, but fails the frozen error-improvement gates: pooled SSE is higher than the comparator, pooled R² is lower, and candidate SSE is lower in only one of the two evaluation years.

Decision:

**`A1_VALIDATED_DRIVER_ADAPTER_DEV_NO_PROGRESS`**

The result is narrow: the validated B1/B2 coordinates remain valid standalone factor products, but adding both of them to the already strong V6A model under this exact no-search adapter does not justify a successor.

No single-coordinate add/drop rescue, interaction, reweighting or Ridge retuning is authorized from this result. 2021–2025 remains unopened by this identity and no reusable BLACKBOX query is created.

`production_authority=false`.
