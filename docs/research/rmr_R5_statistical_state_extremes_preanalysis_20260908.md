# R5 preanalysis — Statistical-state extremes

Date: 2026-09-08  
Identity: `R5_statistical_state_extremes_stage1_v1`  
Role: next broad-program shallow lane after R1/R2/R3 comparison.

## Question

Can an extreme value of a **market-path property**, rather than price distance from a line, define a useful temporary deviation state?

The first-pass question is not “which indicator makes money?” It is:

> When a causal market-path statistic becomes unusually extreme relative to its own recent normal state, does that extreme itself revert, and does it change the probability of subsequent price-path reversal versus continuation?

This lane deliberately treats “mean” as the normal state of a statistical property.

## Candidate budget — exactly three first-pass objects

No other statistical property may be added under this Stage-1 identity.

### R5-A — Path-efficiency extreme

Property:

`path_efficiency = abs(net_move) / sum(abs(incremental_moves))`

Interpretation:

- near 1: path is unusually one-directional;
- near 0: path contains substantial back-and-forth relative to net displacement.

Stage-1 questions:

1. does an extreme path-efficiency observation revert toward its rolling normal region?
2. conditional on move size, does an efficiency extreme change subsequent reversal/continuation probability?

Do **not** assume high efficiency is mean-reverting; continuation is an equally valid outcome.

### R5-B — Volatility-state displacement

Property:

`short_horizon_realized_volatility / parent_horizon_realized_volatility`

Interpretation:

- high value: local volatility has expanded relative to parent state;
- low value: local volatility has compressed.

Stage-1 questions:

1. does the volatility ratio itself decay back toward its recent normal level?
2. after controlling for price move severity, does a volatility-state displacement distinguish reversal from continuation?

Because volatility clusters, immediate mean reversion is **not** assumed in advance.

### R5-C — Event-density / wave-duration extreme

Property:

Use the already frozen causal directional-change event representation.

Measure either:

- completed-event count per fixed number of observed 1m bars; or
- duration in observed bars between completed same-scale events.

The primary representation will be the reciprocal relationship `event_density`, with duration retained as descriptive reporting.

Stage-1 questions:

1. do unusually dense/sparse event regimes revert toward their recent normal state?
2. does event-density extremity contain information about subsequent price reversal versus continuation beyond move severity?

## Common normalization

For each property, define the current state relative to a rolling **past-only** reference distribution.

First-pass normalization is frozen as:

- reference window: preceding `100` completed same-scale observations/events where applicable;
- center: rolling median;
- scale: rolling median absolute deviation (MAD), with zero-MAD observations excluded;
- extreme score: `(current_value - past_median) / past_MAD`.

The current observation is excluded from its own reference window.

No percentile/MAD-window search is allowed in Stage 1.

## Common price-path outcome

To keep R5 comparable with the broad framework, a statistical-state extreme is not enough by itself.

At a causal event time, report whether the subsequent price path:

- reverses by one predeclared event scale before extending by the same scale; or
- extends first before reversing.

Use symmetric first-passage boundaries where possible. Censored events remain censored.

The statistical property may itself be analyzed for reversion separately, but a lane is not promoted solely because the statistic returns to its median. It must also show a stable relationship to the subsequent price-path outcome or provide clear state-classification value to another broad lane.

## Minimal comparisons

For each of R5-A/B/C, only two primary comparison objects are authorized:

1. move severity / parent-state baseline without the statistical-extreme score;
2. the same baseline plus the one frozen statistical-extreme score.

This gives all three properties equal research budgets.

No interactions, threshold search or multi-indicator ensemble in Stage 1.

## Evidence roles

Reuse the already frozen broad-program roles unless a source problem forces a new contract:

- DEV: 2015–2019;
- chronological stability: 2020–2022, not fresh;
- 2023–2025 reserve: unopened and not available to rescue a failed property.

R5 is a new identity, but the raw data are historically consumed elsewhere, so no first-pass result may be called fresh.

## What counts as promising

A property is progression-worthy only if:

- there is adequate event supply;
- adding the extreme score improves the simple baseline in the same direction across multiple years and at more than one predeclared scale where applicable;
- the property-to-outcome relation is causal and interpretable;
- improvement does not depend on selecting a lucky extremity threshold;
- the effect is not merely the property itself mechanically decaying without price-path information.

## What closes or downgrades a property

- no stable property reversion;
- property reverts but has no useful price-path relationship;
- effect changes sign across years/scales;
- baseline explains the effect equally well;
- only one optimized threshold/window creates the result;
- sample becomes trivial after causal construction.

## Explicit non-goals

- no trading PnL;
- no indicator zoo;
- no wavelet/frequency-model complexity in this first identity;
- no optimized z-score threshold;
- no use of 2023–2025 reserve;
- no claim that statistical extremity implies price reversal.

If none of the three properties survives this shallow screen, close R5 v1 and move to a different broad direction rather than expanding the feature list.
