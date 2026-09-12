# OFP-B3 FX/CNY driver v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_fx_cny_driver_v1`

Development window: `2015-01-05..2020-12-31`.

Frozen candidate: `fx_cny_z = -hkma_usdcny_closure_return / RMS60_prev(hkma_usdcny_closure_return)`; positive values mean CNY strength / risk-on. Target is `opening_gap_rvol` with the preregistered domestic baseline only.

All preregistered sufficiency and progression gates pass. Pooled complete cases: **1419**; pooled partial correlation: **+0.1774543197**; pooled standardized coefficient: **+0.1734597248**; pooled delta R²: **+0.0296417058**. Annual coefficients are positive in **5 / 6** years and annual delta R² is positive in **6 / 6** years; median annual standardized coefficient is **+0.0528229637**.

B3 was preregistered before B2 outcomes were opened. No threshold, sign, lookback, interpolation, target or channel-combination search occurred. No 2021–2025 rows were opened.

Decision: **`B3_DEV_PROGRESS_CONTINUOUS_COORDINATE`**.

A reusable validation may proceed only through a separately frozen compact successor preserving the same continuous coordinate, causal HKMA semantics, normalization, domestic baseline and positive sign hypothesis.

`production_authority=false`.
