# Gap-fill Prediction V2 — Phase-1 factor adjudication — 2026-09-06

## Decision

The preregistered Phase-1 factor diagnostic is accepted as a valid development-only mechanism study.

Research identity: `gap_fill_prediction_v2`.

Decision: **authorize a later bounded V2 hazard-family design, with high-open and low-open heads separated and with only Phase-1-admitted probes eligible for the first family.**

No gap-fill candidate model was fit in Phase-1. No feature, threshold or trading-return search was performed. The frozen V1 direction/magnitude models were recomputed only as expanding-year OOF references, and their fits did not use gap-fill outcomes. No 2026 row was loaded.

Cloud run: `34032893251`.

Execution evidence:

- frozen protocol / runner / test Git blob identities passed;
- frozen panel, 1m and offshore data SHA256 checks passed;
- package validator passed;
- pytest: 34 passed;
- common complete diagnostic inventory: 2,421 rows;
- high-open rows: 942;
- low-open rows: 1,479;
- 2026 rows loaded: false.

## Phase-1 result structure

There were 10 preregistered probes, two signs and three cumulative fill horizons. A probe was allowed to progress for a sign/horizon only if its predeclared direction held in pooled >10bp data, in at least 6/10 OOF years, in the median annual difference, in Q4-vs-Q1 fill-rate ordering, and in pooled >30bp data.

Thirty-six sign/horizon/probe cells passed. The important result is not the raw count but the block structure.

### 1. Gap geometry is a universal first-order state variable

Both of the preregistered geometry probes passed for **high and low gaps at all three horizons**:

- `abs_gap`;
- `abs_gap_over_rvol20`.

This is consistent with the frozen target ledger: larger displacement from the previous close is systematically harder to fill quickly and remains harder to fill through EOD. Geometry must therefore be present in any first V2 family rather than treated as a nuisance control.

### 2. Frozen V1 direction support survives as genuine V2 information

`v1_direction_support = sign(observed_gap) * frozen_v1_direction_score_oof` passed for **both gap signs and all three horizons**.

Interpretation: the V1 direction head remains useful even after the open has occurred. If the realized gap is strongly aligned with the pre-open conditional-median direction signal, that gap is less likely to be completely filled. This creates a clean V1 -> V2 interface without retuning V1.

For example, in a material high-gap EOD cell the >10bp fill rate fell from about 66.2% in the lowest-support quartile to about 49.0% in the highest-support quartile; the filled-minus-unfilled standardized support difference was about -0.329 and the preregistered direction held in 9/10 OOF years.

For material low gaps the same direction also held, though more weakly. In the EOD >10bp cell, the lowest-support quartile filled about 75.3% versus about 70.0% in the highest-support quartile, with 7/10 annual differences in the preregistered direction.

### 3. Nasdaq and VIX support are robust across both signs and all horizons

Both external-market alignment probes passed for **high and low gaps at 15m, 60m and EOD**:

- `nasdaq_interval_support = sign(gap) * us_nasdaq_interval`;
- `vix_interval_support = -sign(gap) * us_vix_interval`.

Interpretation: an opening gap that is supported by completed-US-session risk repricing is less likely to fill. This supports the V2 distinction between an information-supported gap and a gap that is weakly supported by the overnight global state.

These two probes are authorized for the first bounded V2 family.

### 4. Prior-China continuation state is asymmetric: useful for high gaps, not low gaps

For high gaps only, both of the following passed at all three horizons:

- `prior_daytime_alignment = sign(gap) * prev_daytime`;
- `prior_last_hour_alignment = sign(gap) * prev_last_hour`.

The same probes did not pass for low gaps.

Interpretation: a high opening that continues a same-direction prior-day or late-day China move has a persistent-state signature and is less likely to fill. The corresponding low-gap mechanism is not stable enough to admit.

Therefore these two variables may enter the **high-gap** first family but are forbidden from the **low-gap** first family unless a new preregistered mechanism study later justifies them.

### 5. V1 magnitude surprise failed its preregistered mechanism hypothesis

The preregistered hypothesis was:

> `v1_magnitude_surprise = abs(realized_gap) - V1_magnitude_oof` should increase fill probability when positive, because a gap that exceeds the pre-open magnitude expectation might represent opening overshoot.

That hypothesis was rejected.

In both high- and low-gap material cohorts, larger positive magnitude surprise was generally associated with **lower**, not higher, fill probability. For example, in a high-gap >10bp EOD cell the filled-minus-unfilled surprise difference was about -26.4bp-equivalent in gap units (`-0.002639`), only 1/10 annual differences matched the preregistered positive-fill direction, and the Q1-to-Q4 fill rate moved roughly 61.6% -> 39.1%. In the corresponding low-gap EOD cell, the pooled difference was also negative and only 1/10 annual differences matched the preregistered hypothesis.

A likely explanation is that this raw surprise measure remains strongly entangled with realized gap size: the V1 magnitude model underpredicts some genuinely large information shocks as well as any possible opening overshoot. That explanation was not preregistered as an alternative transform, so Phase-1 must not residualize, flip or otherwise rescue this probe post hoc.

`v1_magnitude_surprise` is therefore excluded from the first V2 candidate family.

### 6. Broad-China-specific ETF support did not survive this V2 objective

`broad_china_specific_support = sign(gap) * broad_china_specific_vs_spy` did not satisfy the frozen V2 mechanism gate.

This does not revoke the earlier OHR-06 finding that broad-China-vs-SPY contains information in a particular high-open false-negative slice. It means that the same state is not stable enough as a general 15m/60m/EOD gap-fill predictor under this new objective.

The first V2 family therefore does **not** need the offshore ETF source. This is a useful simplification.

### 7. Prior-gap alignment is not admitted

`prior_gap_alignment` did not pass the frozen mechanism gate and is excluded from the first family.

## Authorized first-family feature boundary

### High-gap head

Eligible first-family variables:

1. `abs_gap`;
2. `abs_gap_over_rvol20`;
3. `v1_direction_support`;
4. `nasdaq_interval_support`;
5. `vix_interval_support`;
6. `prior_daytime_alignment`;
7. `prior_last_hour_alignment`.

### Low-gap head

Eligible first-family variables:

1. `abs_gap`;
2. `abs_gap_over_rvol20`;
3. `v1_direction_support`;
4. `nasdaq_interval_support`;
5. `vix_interval_support`.

### Explicitly excluded from the first family

- `v1_magnitude_surprise`;
- `broad_china_specific_support`;
- `prior_gap_alignment`;
- prior-China daytime / last-hour alignment in the low-gap head;
- any post-09:31 China feature;
- any auction or constituent-breadth variable until its source and timestamp contract is separately frozen before target inspection;
- any feature not preregistered and admitted above.

## Architecture implication

The target ledger and Phase-1 results jointly support the parent V2 design:

- separate **high-gap** and **low-gap** heads;
- discrete-time fill hazards for 15m, 15->60m and 60m->EOD;
- cumulative probabilities must remain monotone by construction;
- geometry is the baseline;
- V1 direction support and global overnight support are the universal incremental information blocks;
- prior-China continuation state is high-gap-only in the first family.

A later Phase-2 family should be low-capacity and bounded before fitting. Phase-1 does not authorize hyperparameter, threshold or model-class search.

## Evidence boundary

- development material: 2015-01-05 through 2025-12-31;
- V1 reference OOF / Phase-1 diagnostic years: 2016-2025;
- 2021-2025 remains consumed development evidence, not fresh;
- 2026-01-05 through 2026-08-21 remains repeat-only and was not loaded;
- post-2026-08-21 remains unread true-fresh evidence;
- production authority remains false.
