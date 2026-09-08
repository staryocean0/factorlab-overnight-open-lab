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

Certified frozen identities must be reused without refit:

- R1 parameter bundle SHA256: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`
- R2 parameter bundle SHA256: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`
- S1: `0.003445827004614232`
- S2: `0.006891654009228464`
- S3: `0.013783308018456928`

The historical certified scale identity is not re-estimated from the current DEV window.

## Frozen execution convention for diagnosis

For every event:

- event information becomes available at the certified event confirmation bar;
- hypothetical entry = next observed 1m close;
- if the original structural target/failure boundaries are already invalidated before entry, mark the event `entry_invalid` and do not create a trade-return path;
- direction = restoration direction;
- diagnostic round-trip cost = fixed 10bp, matching the closed economic families;
- structural resolution horizon = certified 1200 observed bars;
- unresolved events are censored at the frozen horizon / available data boundary.

This convention is descriptive only and is not being selected as a strategy.

## Frozen diagnostic objects

### D0 — event and tradeability inventory

For each cell and role report:

- confirmed event count;
- next-minute tradeable count;
- next-minute tradeable fraction;
- entry-invalid count;
- resolved restoration rate;
- mean frozen certified restoration probability.

### D1 — structural reward/loss geometry at entry

For each tradeable event report:

- `target_gross`: directional return from entry price to original restoration boundary;
- `failure_gross`: directional return from entry price to original failure/continuation boundary;
- `reward_loss_abs_ratio = abs(target_gross) / abs(failure_gross)`;
- `break_even_restoration_probability_10bp` implied by the two boundaries and 10bp cost;
- `binary_structural_expected_net_10bp = p_certified * target_gross + (1-p_certified) * failure_gross - 10bp`.

Do not search a ratio/probability threshold.

### D2 — confirmation-to-entry reward consumption

Using the fixed next-observed-1m entry only, report:

- restoration-direction move from confirmation price to entry price;
- structural target reward available at confirmation;
- structural target reward available at entry;
- reward consumed by the fixed confirmation-to-entry delay;
- reward-consumed fraction where defined.

This is diagnostic evidence for possible `entry_slippage_or_confirmation_delay`; it is not permission to search entry delay.

### D3 — realized structural-resolution economics

At actual first-passage/censor exit report:

- realized gross return;
- realized net return after 10bp;
- win indicator;
- holding bars;
- censor rate;
- target-side overshoot;
- failure-side overshoot.

Resolution time must include mean, median and p90 holding bars. Overshoot is signed realized return minus the theoretical reached-boundary return.

### D4 — fixed markout term structure

From next-bar entry, report directional restoration markouts at exactly:

`[1, 5, 15, 30, 60, 120, 240]` observed 1m bars.

For every horizon report both mean markout and positive-share where available. If a horizon is beyond available data, mark missing. Do not select or promote any horizon.

### D5 — restoration probability versus realized economics

Use the **already frozen final certified mechanism models** only. No refit.

For each cell compute the certified candidate restoration probability at event time and report:

- Pearson correlation with realized net return among tradeable events;
- mean realized net return by fixed probability bins `[0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]`;
- event count in every fixed bin;
- mean certified probability in every fixed bin;
- mean binary structural expected net in every fixed bin;
- mean structural break-even restoration probability in every fixed bin;
- descriptive check whether non-empty bin mean realized-net returns are monotonic non-decreasing.

These bins are descriptive and fixed ex ante; they are not thresholds for a strategy.

### D6 — DEV versus VALIDATION stability

Report D0-D5 separately for:

- DEV `2015-01-05 .. 2020-12-31`;
- VALIDATION `2021-01-01 .. 2025-12-31`;

and for each of the four cells.

For VALIDATION also report full summaries for each calendar year 2021, 2022, 2023, 2024 and 2025. No year may be selected or excluded.

## Diagnostic interpretation categories

The later adjudication may classify observed failure modes descriptively, without selecting a new strategy:

1. `geometry_unfavorable` — reward/loss geometry demands restoration probabilities above frozen certified levels;
2. `entry_slippage_or_confirmation_delay` — event-confirmation to fixed next-bar move consumes material theoretical reward;
3. `boundary_overshoot_tail` — failure-side overshoot creates losses larger than binary boundary approximation;
4. `slow_resolution_cost_exposure` — long/censored paths dominate despite probability information;
5. `short_horizon_wrong_way_markout` — restoration probability is long-horizon while immediate fixed markouts are adverse;
6. `probability_not_monotonic_with_realized_return` — higher certified restoration probability does not map monotonically to realized net return.

These labels are adjudication language only. The runner must not introduce hidden classification thresholds or use them to select observations.

## Data governance

- DEV and VALIDATION only.
- Maximum read date: `2025-12-31`.
- BLACKBOX source must not be opened or referenced as an input by the runner.
- No query is appended to the BLACKBOX ledger.
- This diagnostic does not create BLACKBOX query #4.

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

After the detailed DEV/VALIDATION receipt is read in full, program adjudication must choose one of only three directions:

1. a materially new execution-timing theory;
2. a materially new instrument-mapping theory (ETF / futures / options or another explicitly motivated tradable representation);
3. stop economic translation for the certified mechanisms under current evidence.

Any new identity must have independent theory motivation and cannot be threshold/entry/stop/cost/scale rescue of the closed economic families.

Production authority remains false.
