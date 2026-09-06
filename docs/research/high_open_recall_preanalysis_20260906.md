# High-open recall mechanism preanalysis — 2026-09-06

## Research objective

The accepted direction head (`median_quantile_sign`) is a real improvement over the old Ridge direction head, but its remaining error is strongly asymmetric: the accepted 2026 receipt showed much stronger low-open recall than high-open recall. This branch does **not** treat that observation as permission to tune on 2026. The exact 2026-01-05 through 2026-08-21 window is sealed from development under `cloud_session_20260906_high_open_recall_research_protocol_v1.json`.

The financial question is narrower than “raise accuracy by one point”:

> What causal mechanism makes the model systematically under-call actual high opens, and can that mechanism be represented with a low-capacity mathematical feature without giving back the direction-hit and balanced-accuracy gains already achieved?

## Why a threshold patch is not the default answer

The current head estimates the conditional median of the signed opening gap and classifies `prediction >= 0` as high open. For a continuous target and symmetric daily sign loss, this is a coherent decision rule. Raising the quantile, changing the zero threshold, or class-weighting high opens would mechanically increase predicted-up frequency, but that would primarily change **error utility**, not discover new information.

Such a move is legitimate only if the financial owner explicitly states that a missed high open is more costly than a missed low open. That utility decision has not been made here. Therefore threshold/quantile shifts are diagnostic comparators only, not the preferred scientific solution.

## Mechanisms to distinguish before choosing a new model

### H1 — Boundary-noise hypothesis

Many apparent false negatives may be tiny positive gaps close to zero. If most missed high opens are, for example, +0 to +10 bp while materially large high opens are already captured well, then raw high-open recall exaggerates the financial weakness. In that case the right conclusion may be “classification boundary noise,” not “missing positive-shock mechanism.”

Required test: split actual high opens into 0–10 bp, 10–30 bp and >30 bp, and separately report recall for >10 bp and >30 bp.

### H2 — Slow opening-regime / base-rate state

The unconditional and conditional tendency to open high can drift over months. The current feature set contains a 5-day overnight mean but no longer-horizon estimate of the opening-gap sign distribution. A persistent positive opening regime could make a historically conservative median under-call high opens even while its cross-sectional/time-series ranking remains useful.

Causal probes:

- prior-only 20-day and 60-day high-open share;
- prior-only 20-day/60-day mean and median gap;
- prior-only slow overnight drift state.

This is financially interpretable as a changing overnight risk-premium / auction-demand state, not a calendar rule.

### H3 — Asymmetric overseas pass-through

The current direction head uses linear NASDAQ and VIX daily changes. A-share opening response need not be symmetric: a +1% NASDAQ move may not be the mirror image of a -1% move, and simultaneous NASDAQ-up/VIX-down can represent a qualitatively different global risk-on impulse.

Causal probes:

- completed-session NASDAQ interval positive part and negative part;
- VIX-up and VIX-down parts;
- joint NASDAQ-up × VIX-down risk-on impulse;
- US-session count.

The key test is not whether these variables correlate with the gap in-sample, but whether high-open false negatives are systematically enriched in their high-risk-on regions in expanding OOF predictions.

### H4 — China weakness × US risk-on catch-up

An opening high may be a catch-up response when China closed weakly but the completed US information set subsequently turns strongly risk-on. An additive linear model can miss this interaction because prior-China weakness is negative while US risk-on is positive; the interaction, not either marginal variable, is the mechanism.

Causal probes:

- negative part of prior full-day return × positive US NASDAQ interval;
- negative part of prior afternoon return × positive US NASDAQ interval;
- negative part of prior last-hour return × positive US NASDAQ interval.

A valid mechanism should appear across multiple development years and should be strongest on actual high-open misses, not merely on all high-open days.

### H5 — Exceptional clock accumulation

Earlier research established that multiple completed US sessions and holiday reopenings carry unusually strong magnitude information, while a simple full-model gate did not produce stable direction improvement. This branch may revisit the **positive-direction** side only if Phase 1 shows that high-open false negatives are concentrated there. It must not revive the previously rejected hard route without new mechanism evidence.

## Phase-1 mathematics

Use the incumbent Median head unchanged in expanding natural-year OOF:

- train 2015 → test 2016;
- train 2015–2016 → test 2017;
- …;
- train 2015–2024 → test 2025.

No row from 2026 may be loaded.

For each OOF test row, define:

- `actual_up = gap >= 0`;
- `pred_up = median_prediction >= 0`;
- false negative = `actual_up and not pred_up`;
- score margin for a false negative = `-median_prediction`.

The diagnosis must report annual confusion metrics, false-negative magnitude bins, score-margin bins, and prior-only causal probe enrichment. Row-level 2015+ market data remains local and must not be committed.

## What would justify a candidate family

A new feature family is allowed only when the mechanism is both financially meaningful and development-stable. Examples:

- If H2 is supported across years, a low-capacity slow-state extension may be admitted.
- If H3 is supported, positive/negative overseas pass-through terms may be admitted.
- If H4 is supported, at most a small number of catch-up interaction terms may be admitted.
- If only H1 is supported, do **not** add complexity merely to relabel tiny positive gaps.
- If no mechanism is stable, retain the incumbent and report that the high-open recall gap is unresolved rather than patching the threshold.

## Development selection rule for the later candidate phase

The user’s requested target is higher high-open recall, but the new solution is not allowed to buy that improvement by destroying the model’s existing strengths. On 2016–2025 expanding OOF, an eligible successor must satisfy:

1. `recall_up` strictly improves over the incumbent;
2. `direction_hit` is not lower than the incumbent;
3. `balanced_accuracy` is not lower than the incumbent;
4. `recall_down > 0.5`;
5. no 2026 information is used in design or ranking.

Selection among eligible low-capacity candidates will be frozen only after Phase 1 results are reviewed. Trading return is not a model gate.

## Evidence status of 2026

`2026-01-05 .. 2026-08-21` is operationally sealed from this development branch and will be used only after a successor is frozen. However it was already opened in the prior cycle, and this branch itself was motivated by the known high-open-recall weakness. Therefore it is **not scientifically fresh again**. It can reject or reproduce a frozen successor, but it cannot by itself grant new fresh-OOS authority.

The first genuinely unread evidence for an integrated successor remains post-2026-08-21 and must stay sealed until a successor identity and challenge protocol are frozen.
