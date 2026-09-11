# OFP-B4 Driver Agreement / Disagreement — cloud adjudication

Date: 2026-09-12

Research identity: `overnight_driver_coherence_v1`

Decision: **`B4_DEV_PROGRESS_DRIVER_COHERENCE_CONTINUOUS_COORDINATE`**

## Boundary and execution review

The development run used only `2015-01-05..2020-12-31` from the connector-readable factor carrier and the newly admitted A50/HKMA driver carrier. The receipt records no post-2020 target rows, no 2021-2025 reusable BLACKBOX opening, no alternate normalization, no driver-weight search, no channel drop/add search, no threshold/bucket search, no target search, and no trading-return optimization.

The A50/HKMA carrier separately passed source assertions, A50 cutoff integrity, and HKMA causal timing checks, while generating no 2021-2025 text shards.

## Frozen candidate

The only candidate was:

`driver_coherence = (global_risk_z + china_offshore_z + fx_cny_z) / (|global_risk_z| + |china_offshore_z| + |fx_cny_z|)`

Each driver was normalized by its own causal 60-China-trading-day lagged RMS (`shift(1)`, minimum 20 prior valid observations). The target was exactly `opening_gap_rvol = gap / rvol20`.

## Preregistered gate review

Count sufficiency passed in every natural year and pooled.

Pooled diagnostics:

- partial correlation: approximately `-0.10055`;
- standardized driver-coherence coefficient: approximately `-0.10513`;
- delta R2: approximately `+0.005142`.

Annual stability:

- all 6 of 6 annual standardized coefficients are negative, matching the pooled sign;
- the annual median standardized coefficient is negative;
- all 6 of 6 annual delta R2 values are positive.

Therefore every preregistered development progression condition passes.

## Interpretation boundary

The stable negative conditional coefficient must not be rewritten into a post-hoc risk-on/risk-off trading rule. The baseline already contains the three signed driver main effects. The B4 result says that the preregistered nonlinear cross-channel coherence coordinate carries stable incremental information about normalized opening gap after those main effects and domestic causal context are controlled.

This result does not authorize thresholds, high/low agreement buckets, alternative driver weights, pairwise rescues, PnL optimization, or production use.

## Authority

B4 is retained as **development progression material** for the continuous `driver_coherence` coordinate.

A 2021-2025 reusable BLACKBOX may be considered only under a separately frozen successor identity and result-free protocol. The parent development identity itself may not open the BLACKBOX.

`production_authority=false`.
