# OFP-B1 global-risk driver v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_global_risk_driver_v1`

Development window: `2015-01-05..2020-12-31`

## Frozen coordinate

`global_risk_z = 0.5 * (us_nasdaq / RMS60_prev(us_nasdaq) + (-us_vix_chg / RMS60_prev(us_vix_chg)))`

with 60-China-trading-day lagged RMS, current observation excluded, minimum 20 observations.

Target: `opening_gap_rvol = gap / rvol20`.

The baseline contains only the preregistered domestic causal controls. A50, FX and B4 coherence are excluded from this B1 identity.

## Development result

All preregistered sufficiency and progression gates pass.

Pooled complete cases: **1417**.

Pooled partial correlation: **+0.4787568170**.

Pooled standardized `global_risk_z` coefficient: **+0.4704831151**.

Pooled baseline R²: **0.0585151036**.

Pooled candidate R²: **0.2743110583**.

Pooled delta R²: **+0.2157959547**.

Annual standardized coefficients are positive in **6 / 6** years and annual delta R² is positive in **6 / 6** years. Median annual standardized coefficient is **+0.5183167496**.

No candidate-weight, normalization, threshold, bucket, channel add/drop or target search occurred. No 2021–2025 rows were opened.

## Decision

**`B1_DEV_PROGRESS_GLOBAL_RISK_CONTINUOUS_COORDINATE`**

This preserves the exact continuous global-risk coordinate as Development progression material. It does not itself grant validated product authority.

A reusable 2021–2025 validation may proceed only under a separately frozen compact successor identity. The validation must preserve the same coordinate, target, domestic baseline and positive sign hypothesis and may release only `PASS / FAIL / INSUFFICIENT`.

`production_authority=false`.
