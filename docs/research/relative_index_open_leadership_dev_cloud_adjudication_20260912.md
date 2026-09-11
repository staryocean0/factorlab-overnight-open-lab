# OFP-D1 Relative-Index Opening Leadership — cloud DEV adjudication

Date: 2026-09-12

Research identity: `overnight_relative_size_open_leadership_v1`

## Frozen question

Does the continuous relative opening coordinate

`size_open_leadership = gap_rvol_CSI1000 - gap_rvol_CSI300`

carry incremental information for CSI1000-minus-CSI300 post-open relative returns after controlling for the preregistered baseline:

- `common_open_component`
- `relative_r1`
- `relative_log_rvol`

The candidate pair, clocks, horizons, controls and progression gates were frozen before D1 outcome inspection. CSI500 remained carrier-inventory-only and was not searched as a candidate. The closed V2.1 P2 relative-gap-excess family was not imported or rescued.

## Evidence boundary

Detailed development evidence is limited to 2015-01-05 through 2020-12-31. The accepted carrier receipt states that no 2021-2025 row-level text was generated and no D1 outcome diagnostic was performed during carrier materialization. The DEV runner additionally verified the six carrier SHA256 values against the accepted manifest before computation. No 2021-2025 BLACKBOX was opened in this stage.

## Preregistered gate results

### 09:35 -> 09:50 relative return

PASS progression.

- pooled partial correlation: `+0.07480075235014566`
- pooled standardized candidate coefficient: `+0.083251034216728`
- pooled delta R2: `+0.005533815058615277`
- annual coefficient same-sign count: `6/6`
- annual positive delta R2 count: `6/6`
- minimum annual complete-case count: `242`
- annual median coefficient: `+0.09319071088521061`

### 09:35 -> 10:05 relative return

PASS progression.

- pooled partial correlation: `+0.07093744954232052`
- pooled standardized candidate coefficient: `+0.07892911898790761`
- pooled delta R2: `+0.004980490280348193`
- annual coefficient same-sign count: `6/6`
- annual positive delta R2 count: `6/6`
- minimum annual complete-case count: `242`
- annual median coefficient: `+0.11188344959673348`

### 09:35 -> 10:35 relative return

PASS progression.

- pooled partial correlation: `+0.04828719570132659`
- pooled standardized candidate coefficient: `+0.05372289667178318`
- pooled delta R2: `+0.002304839002244208`
- annual coefficient same-sign count: `5/6`
- annual positive delta R2 count: `6/6`
- minimum annual complete-case count: `242`
- annual median coefficient: `+0.08915840371955029`

The one opposite-sign annual coefficient at 60m is 2016 and is near zero; no post-hoc exception is granted or needed because the preregistered gate requires at least 4 of 6 annual coefficients to share the pooled sign.

## Decision

`D1_DEV_PROGRESS_15M_30M_60M_SHARED_CONTINUOUS_COORDINATE`

All three preregistered horizons pass. The frozen multiple-passing-horizons rule therefore applies: retain all three jointly. There is no authority to choose a unique 15m, 30m or 60m winner after observing these results.

This closes the parent DEV identity with progression support only. It does not itself authorize a 2021-2025 reusable BLACKBOX query, categorical size-leadership buckets, index-pair substitution, threshold search, strategy PnL optimization, or production use.

Any reusable BLACKBOX validation must use a separately frozen joint 15m+30m+60m successor identity and result-free protocol. The successor must preserve CSI1000-versus-CSI300, the continuous coordinate, the three horizons, and the baseline controls without using hidden BLACKBOX behavior for redesign.

Production authority remains false.
