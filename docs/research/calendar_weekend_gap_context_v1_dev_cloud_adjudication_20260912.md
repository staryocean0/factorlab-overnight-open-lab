# OFP-C4 weekend-closure gap context v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_weekend_gap_conditioned_open_state_15m_v1`

Development window: `2015-01-05..2020-12-31`.

Frozen candidate: `weekend_gap_interaction = weekend * (gap / rvol20)`.

Frozen target: `09:35 -> 09:50` return. Baseline includes the observed gap main effect, weekend and holiday main effects, trend/rvol parents, validated C1 trend-gap interaction, `r1` and prior daytime return. No C2 60m interaction or B1/B2/B4 driver coordinate is imported.

All preregistered sufficiency and progression gates pass. Pooled complete cases: **1440**; weekend complete cases: **264**; pooled partial correlation: **+0.0674876584**; pooled standardized interaction coefficient: **+0.0742245615**; pooled delta R²: **+0.0043227191**. Five of six annual coefficients share the pooled positive sign; annual delta R² is positive in six of six years; median annual coefficient is **+0.1227938649**.

The first workflow attempt failed before a receipt was produced because the mechanical runner selected the `weekend` column twice. The retry changed only that dataframe column-selection bug. Candidate, target, evidence, baseline and gates were unchanged.

## Decision

**`C4_DEV_PROGRESS_WEEKEND_GAP_15M_CONTINUOUS_INTERACTION`**

The positive Development sign is now frozen for any successor validation.

This decision grants Development progression material only. It does not authorize weekday searches, holiday substitution, closure-length reconstruction, thresholds, buckets or strategy use.

`production_authority=false`.
