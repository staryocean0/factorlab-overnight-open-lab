# R1 preanalysis — Cross-scale pullback inside an intact parent trend

Date: 2026-09-08  
Identity: `R1_cross_scale_pullback_stage1_v1`  
Role: results-blind shallow screen, not strategy optimization.

## Question

When a parent-scale trend is already established and a lower-scale move suddenly runs against it, can information available **before recovery/failure** distinguish:

- a lower-scale pullback that later rejoins the parent trend;
- a genuine same-scale reversal that breaks the parent state?

This is not “buy after a large drop.” The parent trend must be measured independently from the counter-move.

## Coordinate definition

- **parent scale:** last two completed parent-scale waves before the lower-scale counter-move;
- **current/lower scale:** the completed counter-wave or causal shock event occurring against the parent drift;
- **parent state object:** signed two-wave drift, overlap, path efficiency, and parent volatility;
- **deviation object:** lower-scale counter-move relative to parent direction;
- **candidate mean:** intact parent-scale wave/trend path, not a moving-average line.

## Parent integrity measurements

Stage 1 uses continuous scores rather than choosing a hard trend threshold after seeing outcomes:

1. `signed_drift_ratio` from the last two completed parent waves;
2. `overlap_ratio` of those two wave price intervals;
3. `parent_path_efficiency`;
4. `counter_move_size / pre_event_parent_volatility`;
5. `counter_move_path_efficiency` and speed as descriptive severity measures.

No result-based search for the best “trend strength” cutoff is allowed.

## Primary event/outcome logic

For an up-parent case, after a causally confirmed lower-scale downward counter-move:

- **recovery boundary:** price first regains the pre-counter-move local high / shock origin;
- **parent-failure boundary:** price first breaks the last causally available parent structural low that anchored the parent upswing;
- down-parent cases are symmetric.

Primary outcome:

`recovery_first` vs `parent_failure_first`.

Also report time to either boundary. Events that hit neither within the predeclared maximum horizon are censored, not silently called failures.

## Stage-1 hypotheses

H1. Higher pre-event parent integrity should increase `recovery_first` probability after a lower-scale counter-move.

H2. For the same counter-move severity, parent-state measurements should add information beyond counter-move size alone.

H3. The sign of H1/H2 should remain the same across more than one parent/lower scale pairing or chronological block.

## Minimal comparisons

Only three first-pass comparisons are authorized:

1. **severity-only baseline** — counter-move size / volatility;
2. **parent-state-only** — completed two-wave integrity scores;
3. **parent-state + severity** — low-capacity combination.

No additional feature family may be added in Stage 1 without closing this identity and writing a new preanalysis.

## What would count as promising

R1 is progression-worthy if:

- event count is adequate;
- parent-state conditioning changes recovery probability in the predicted direction;
- the effect survives at least two independent time/scale slices;
- parent-state information adds beyond severity-only;
- the result is visible without optimizing a trading threshold.

## What would close or downgrade R1

- recovery probability is explained almost entirely by counter-move size;
- parent integrity has unstable or opposite effects across scales/periods;
- causal completed-wave definitions leave too few events;
- results depend on one wave threshold or one narrow period;
- the structural failure boundary cannot be defined causally.

## Data needed

Minimum:

- clean OHLC bars with exact timestamps;
- enough intraday/daily history to construct at least two parent/lower scale pairings;
- no need for cross-asset, fundamentals, news, or execution data in Stage 1.

Preferred first-pass universe: broad liquid index series rather than individual stocks, to reduce microstructure and survivorship complications.

## Explicit non-goals

- no optimal entry point;
- no stop-loss optimization;
- no PnL maximization;
- no deep model;
- no claim that every parent-trend pullback should be bought.

The only first-round question is whether **parent-state integrity separates temporary lower-scale pullback from genuine parent-state failure**.
