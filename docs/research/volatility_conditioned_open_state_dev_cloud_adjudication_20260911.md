# Volatility-conditioned opening state — cloud DEV adjudication (2026-09-11)

## Identity

`overnight_volatility_conditioned_open_state_v1`

Product family:

`OFP-C2_prior_volatility_context_x_OFP-A2_observed_open_geometry`

Cloud receipt:

`docs/research/cloud_volatility_conditioned_open_state_dev_diagnostic_v1.json`

## Execution / boundary review

Cloud execution is accepted as procedurally valid.

- The identity, factor definition, controls and target horizons were frozen before the 2019-2020 diagnostics were evaluated.
- The bounded text carrier is `data/development/trend_open_state_dev_pack_2019_2020/`, an already-opened development interval only.
- The text pack is bound to the historical frozen parquet sources by stored SHA256 lineage.
- Before evaluating C2, the same cloud text bridge reproduced the prior C1 development diagnostics to machine-negligible numerical tolerance, providing a parity check on the carrier/bridge path.
- No detailed target row after 2020 was opened.
- No 2021-2025 reusable BLACKBOX was opened for C2.
- No volatility bucket, threshold, alternate lookback, alternate horizon, trend bucket, Opening Surprise rescue, or trading-return search was performed.
- Production authority remains false.

## Frozen C2 coordinate

`log_rvol20 = log(rvol20)`

`vol_gap_interaction = observed_gap_rvol * log_rvol20`

The baseline includes the volatility and gap main effects plus the already-validated C1 trend-conditioned interaction, so C2 receives credit only for incremental volatility conditioning.

## Scientific decision

**`C2_DEV_PROGRESS_60M_CONTINUOUS_COORDINATE_ONLY`**

The evidence does not support one generic volatility-conditioned opening factor across all three inherited horizons.

### 15 minutes

The 09:35→09:50 interaction is not stable across the two development years: the standardized C2 coefficient and partial-correlation direction are positive in 2019 and negative in 2020. That sign reversal is decisive negative evidence against a stable 15-minute C2 product.

### 30 minutes

The 09:35→10:05 direction is negative in both years and in pooled development, but the incremental contribution is weak in 2019 relative to 2020. The cross-year magnitude is too uneven to justify opening a separate reusable BLACKBOX identity from this two-year mechanism diagnostic.

### 60 minutes

The 09:35→10:35 horizon is the only development result that combines all of the following:

- negative incremental direction in both 2019 and 2020;
- very similar year-specific partial correlations;
- very similar year-specific standardized interaction coefficients;
- positive incremental R² in both development years;
- stronger pooled incremental information than the shorter frozen horizons.

The 60-minute development result is therefore allowed to progress to a **separately frozen continuous validation identity**.

This decision does not authorize high-vol/low-vol buckets or any categorical volatility grid. It validates only the right to test the same continuous C2 interaction at the fixed 09:35→10:35 target under the reusable BLACKBOX protocol.

## Authority consequences

- Parent identity `overnight_volatility_conditioned_open_state_v1` closes after DEV with 60m-only progression support.
- 15m C2 progression is rejected for stability failure.
- 30m C2 progression is not authorized because the incremental evidence is too weak/uneven across the two development years.
- A new identity may be frozen for 60m validation without changing factor definition, controls, volatility lookback, gap normalization or target clock.
- No categorical high/low-vol view is authorized.
- No 2021-2025 BLACKBOX detail may be inspected or used to redesign a successor.

`production_authority=false`.
