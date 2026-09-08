# Mechanism-to-execution diagnostic v1 preanalysis — 2026-09-08

Identity: `rmr_mechanism_to_execution_diagnostic_v1`

This is a **diagnostic study, not a strategy search**.

## Motivation

The project has two reusable-BLACKBOX-certified probability mechanisms:

- R1 trend-parent pullback recovery;
- R2 range-parent boundary re-entry.

Yet the bounded simple economic implementations tested so far failed detailed VALIDATION before BLACKBOX.

The question is therefore no longer whether parent-state information exists. It is:

> Where, mechanically, does certified restoration-probability information fail to become positive realized index-level PnL under the tested next-minute / structural-boundary execution convention?

The answer must be obtained from DEV/VALIDATION only. BLACKBOX is not part of this diagnostic and must not be queried.

## Frozen diagnostic population

Use the already-certified R1/R2 event definitions and frozen S1/S2/S3 scales.

Four cells:

- R1_A: S1-inside-S2 recovery/failure;
- R1_B: S2-inside-S3 recovery/failure;
- R2_A: S1-outside-S2 re-entry/continuation;
- R2_B: S2-outside-S3 re-entry/continuation.

Use all causally valid events under each certified event engine. No probability threshold, state threshold or economic filter is applied.

## Frozen execution convention for diagnosis

For every event:

- event information becomes available at the certified event confirmation bar;
- hypothetical entry = next observed 1m close;
- if the original structural target/failure boundaries are already invalidated before entry, mark the event `entry_invalid` and do not create a trade-return path;
- direction = restoration direction;
- diagnostic round-trip cost = fixed 10bp, matching the closed economic families;
- structural resolution horizon = the certified 1200 observed bars;
- unresolved events are censored at the frozen horizon / available data boundary.

This convention is descriptive only and is not being selected as a strategy.

## Frozen diagnostic objects

### D1 — structural reward/loss geometry at entry

For each tradeable event report:

- `target_gross`: directional return from entry price to the original restoration boundary;
- `failure_gross`: directional return from entry price to the original failure/continuation boundary;
- `reward_loss_abs_ratio = abs(target_gross) / abs(failure_gross)`;
- `break_even_restoration_probability_10bp` implied by the two boundaries and 10bp cost.

Do not search a ratio/probability threshold.

### D2 — realized structural-resolution economics

At actual first-passage/censor exit report:

- realized gross return;
- realized net return after 10bp;
- win indicator;
- holding bars;
- resolution class;
- boundary overshoot: realized exit return minus theoretical boundary return for the reached side.

### D3 — fixed markout term structure

From next-bar entry, report directional restoration markouts at exactly:

`[1, 5, 15, 30, 60, 120, 240]` observed 1m bars.

If a horizon is beyond available data, mark missing. Do not select or promote any horizon.

### D4 — restoration probability versus realized economics

Use the **already frozen final certified mechanism models** only. No refit.

For each cell compute the certified candidate restoration probability at event time and report on VALIDATION:

- Pearson correlation with realized net return among tradeable events;
- mean realized net return by fixed probability bins `[0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]`;
- event count in each bin;
- mean structural break-even restoration probability in each bin.

These bins are descriptive and fixed ex ante; they are not thresholds for a strategy.

### D5 — DEV versus VALIDATION stability

Report every D1–D4 object separately for:

- DEV `2015-01-05 .. 2020-12-31`;
- VALIDATION `2021-01-01 .. 2025-12-31`;

and for each of the four cells.

For VALIDATION additionally report annual summaries 2021–2025 for:

- tradeable count;
- restoration rate;
- mean gross/net return;
- win rate;
- censor rate;
- median holding bars.

No year may be selected or excluded.

## Diagnostic interpretation categories

The report may classify observed failure modes descriptively, without selecting a new strategy:

1. `geometry_unfavorable` — reward/loss geometry demands restoration probabilities materially above observed/certified levels;
2. `entry_slippage_or_confirmation_delay` — event-confirmation to next-bar move consumes much of theoretical reward;
3. `boundary_overshoot_tail` — failure-side overshoot creates losses larger than binary boundary approximation;
4. `slow_resolution_cost_exposure` — long/censored paths dominate despite probability edge;
5. `short_horizon_wrong_way_markout` — restoration probability is long-horizon but immediate markouts are adverse;
6. `probability_not_monetonic_with_realized_return` — higher certified restoration probability does not map monotonically to realized net return.

The final report may assign multiple categories. These are explanatory labels, not model features.

## Data governance

- DEV and VALIDATION only.
- Maximum read date: `2025-12-31`.
- BLACKBOX source must not be opened or referenced by the runner.
- No query is appended to the BLACKBOX ledger.

## Explicitly forbidden

- choosing a probability cutoff;
- choosing a markout horizon;
- changing entry delay;
- changing target/stop/horizon;
- changing the 10bp cost assumption;
- selecting scale, lane, year or regime;
- fitting a PnL model;
- portfolio optimization;
- BLACKBOX access;
- declaring production or a tradable strategy from this diagnostic.

## Intended next decision

After this diagnostic, a program review may decide whether a materially new **execution/instrument** identity is scientifically justified (for example, different tradable instrument mapping or execution timing theory). It may also conclude that no further economic translation should be attempted with the current data/instruments.

Production authority remains false.
