# OFP-B2 China-offshore driver v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_china_offshore_driver_v1`

Development window: `2015-01-05..2020-12-31`.

Frozen candidate: `china_offshore_z = a50_channel_return / RMS60_prev(a50_channel_return)` using governed same-contract A50 ordinary/holiday causal cutoffs.

Target: `opening_gap_rvol` with the preregistered domestic baseline only.

All sufficiency and progression gates pass. Pooled complete cases: **1343**; pooled partial correlation: **+0.6366588843**; pooled standardized coefficient: **+0.6225252432**; pooled delta R²: **+0.3791905658**. Annual candidate coefficients and annual delta R² are positive in **6 / 6** years; median annual standardized coefficient is **+0.6481708484**.

The first workflow attempt failed only while serializing the receipt path after diagnostics had been computed in memory; no receipt or scientific output was persisted. The retry changed only the protocol-path invocation from relative to absolute. Candidate, target, data, normalization and gates were unchanged.

Decision: **`B2_DEV_PROGRESS_CONTINUOUS_COORDINATE`**.

No 2021–2025 rows were opened. A reusable validation may proceed only through a separately frozen compact successor preserving the same continuous coordinate and positive sign hypothesis.

`production_authority=false`.
