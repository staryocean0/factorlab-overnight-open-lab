# Gap-fill prediction v2 preanalysis — 2026-09-06

## Research objective

Version 2.0 remains a **prediction** project, not a trading-strategy project.

Version 1.0 predicts the next CSI1000 opening gap. Version 2.0 starts only after the opening gap is observed and asks whether that gap is subsequently absorbed by the market.

Primary timestamp: **09:31 China time**, after the target opening price is observed.

Primary question:

> Conditional on an observed material high-open or low-open gap at 09:31, what is the probability that the previous 15:00 close is revisited within the next 15 minutes, within the next 60 minutes, or by the same-day close?

This is a price-discovery / gap-absorption problem. It is not equivalent to predicting raw post-open return direction.

## Target definitions

Let:

- `Cprev` = previous China trading day's 15:00 close;
- `O` = current trading day's 09:31 open;
- `gap = O / Cprev - 1`;
- `s = sign(gap)`.

For a high open (`O > Cprev`), a full fill occurs once the observed post-open low reaches or falls below `Cprev`.
For a low open (`O < Cprev`), a full fill occurs once the observed post-open high reaches or exceeds `Cprev`.

Frozen horizons for initial research:

1. `fill_15m`: first full fill occurs by the end of the first 15 one-minute bars after 09:31;
2. `fill_60m`: first full fill occurs by the end of the first 60 one-minute bars after 09:31;
3. `fill_eod`: first full fill occurs by the current 15:00 close.

The events are nested: `fill_15m <= fill_60m <= fill_eod`.

Secondary continuous targets:

- `fill_ratio_15m`, `fill_ratio_60m`, `fill_ratio_eod`: fraction of the opening gap closed by the most favorable path excursion toward `Cprev`, capped to [0,1] for the primary ratio report;
- uncapped excursion ratio for overshoot diagnostics;
- `time_to_first_fill_minutes` with right-censoring at the horizon/end of day.

## Material-gap cohorts

Do not search a significance threshold on development outcomes.

Train/diagnose on all complete non-zero-gap rows, but always report fixed material cohorts separately:

- `abs_gap > 10bp`;
- `abs_gap > 30bp`.

A later deployment threshold, if any, requires a separately frozen objective. Neither 10bp nor 30bp may be selected post hoc based on model performance.

## Why the problem should be modeled as gap absorption

The open is a discrete price-discovery event. Literature across markets documents that opening prices can contain temporary pricing error and that some opening moves reverse during the trading day. In China specifically, opening-auction opinion divergence and order imbalance are linked to subsequent intraday correction, while price discovery is concentrated near the open and can continue through the first 15–30 minutes.

The economically useful latent distinction is:

1. **information-supported repricing** — the gap is supported by pre-open/global/China-specific information and should be less likely to fill quickly;
2. **temporary opening pressure / disagreement / liquidity imbalance** — the gap overshoots available information and should be more likely to fill;
3. **mixed state** — the gap is partly informative and partly temporary, producing partial fill or delayed fill.

## Pre-registered factor blocks for mechanism research

### A. Gap geometry — mandatory

- gap sign;
- absolute gap magnitude;
- gap magnitude normalized by recent realized volatility;
- gap magnitude relative to previous-day range / recent intraday range;
- weekend / holiday reopen / calendar gap days.

Rationale: a 30bp opening move has different informational meaning in a quiet regime than in a high-volatility regime.

### B. V1 surprise / support decomposition — highest priority

Freeze the accepted V1 prediction architecture and derive only pre-defined comparisons between the realized open and what V1 expected before the open:

- realized gap sign agrees/disagrees with V1 direction head;
- V1 direction score / margin;
- realized `abs(gap)` minus V1 predicted magnitude;
- realized `abs(gap)` divided by V1 predicted magnitude with a fixed numerical floor only for division safety;
- signed support indicator combining realized gap sign with the pre-open direction call.

Hypothesis: a gap that substantially exceeds or contradicts the pre-open information set is more likely to be temporary and fill; a gap consistent with strong pre-open support is less likely to fill.

V1 parameters must remain frozen. Gap-fill outcomes may not be used to retune V1.

### C. Overnight / external-information support — highest priority

Only causal information complete by 09:31 may enter:

- Nasdaq interval / risk-on state;
- VIX interval / risk-off state;
- frozen Yahoo offshore-China representations, especially `broad_china_specific_vs_spy`;
- A-share ETF consensus as a supporting diagnostic, not automatically a selected feature;
- CNH / offshore FX state if a frozen causal source is available;
- A50 / relevant pre-open index-futures information if a frozen timestamp-safe source is available.

Primary mechanism variable should be **alignment with the observed gap**, not merely the raw external return. Example: a high-open gap accompanied by strong positive broad-China repricing is information-supported; the same gap without external support is more plausibly an opening overshoot.

### D. Prior-China state — fixed existing family

- `prev_last_hour`;
- `prev_afternoon`;
- `prev_daytime`;
- `prev_gap`;
- `r1`, `r20`, `rvol20`, `abs_r1`;
- previous close location / previous-day range position if reconstructible without new tuning.

High-open and low-open gaps must be analyzed separately because rebound/continuation mechanisms can be asymmetric.

### E. Opening-auction microstructure — high-priority missing-information block

If timestamp-safe auction/order data can be obtained, preregister before inspecting target relationships:

- final call-auction order imbalance;
- auction matched volume / abnormal volume;
- buy-side vs sell-side quote dispersion;
- cancellation/amendment intensity before the non-cancellable cutoff, if available;
- indicative-price path / auction price pressure;
- auction-to-09:31 price slippage.

These variables directly target temporary opening pressure and opinion disagreement. They are likely more relevant to gap fill than adding more slow technical indicators.

### F. Cross-sectional breadth / concentration at the open — high priority if constituent data are available

For CSI1000, distinguish broad market repricing from concentrated index movement using only information available by 09:31:

- fraction of constituents opening in the index-gap direction;
- value/weight-adjusted breadth;
- median constituent gap;
- cross-sectional gap dispersion;
- top-decile contribution concentration;
- number/fraction near price limits if applicable.

Hypothesis: broad, coherent gaps are less likely to fill than narrow, dispersed, concentration-driven gaps.

### G. Opening liquidity / first-minute information

For the **09:31 model**, do not use future information from 09:32 onward.

If valid contemporaneous 09:31-bar information is not timestamp-separable from the subsequent minute path, it must be excluded from the 09:31 model and reserved for a later dynamic-update identity.

A future model may separately predict remaining fill probability at 09:36 or 09:46 using first-5m/15m volume, volatility, order imbalance and path efficiency, but that is not part of the initial V2 identity.

## Model form

Do not begin with an unrestricted black-box model.

The initial target architecture should preserve horizon coherence through a discrete-time fill-hazard formulation:

- `h15 = P(fill by 15m | information at 09:31)`;
- `h60 = P(fill in (15m,60m] | not filled by 15m, information at 09:31)`;
- `hEOD = P(fill in (60m,EOD] | not filled by 60m, information at 09:31)`.

Cumulative probabilities are then mechanically monotone:

- `P15 = h15`;
- `P60 = 1 - (1-h15)(1-h60)`;
- `PEOD = 1 - (1-h15)(1-h60)(1-hEOD)`.

Begin with low-capacity regularized/logistic or equivalent interpretable hazard heads after factor-block diagnostics. More flexible models can only be admitted after the mechanism and validation protocol is frozen.

## Evaluation

Primary metrics are probability and event metrics, not trading return:

- Brier score;
- log loss;
- ROC-AUC / PR-AUC where appropriate;
- calibration slope/intercept and reliability bins;
- top/bottom probability-decile fill-rate separation;
- year-equal robustness;
- separate high-open vs low-open results;
- separate >10bp and >30bp material cohorts;
- consistency across 15m / 60m / EOD horizons.

Also report fill ratios and time-to-fill distribution as secondary outcomes.

## Evidence boundary

Research identity: `gap_fill_prediction_v2`.

- 2015-01-05 through 2025-12-31: development material; 2021-2025 remains already consumed and is not fresh;
- 2026-01-05 through 2026-08-21: already opened in prior work, forbidden for V2 feature/family/threshold design; may only become repeat evidence after an exact V2 candidate is frozen under a separate protocol;
- post-2026-08-21: unread true-fresh evidence reserved for a later challenge;
- production authority: false.

## Immediate next task

Before fitting any model, construct and audit the V2 target ledger from the existing 2015-2025 one-minute CSI1000 pack:

1. exact 15m / 60m / EOD full-fill labels;
2. fill ratios and first-fill time;
3. counts by year, gap sign, >10bp and >30bp cohorts;
4. nesting invariants (`fill_15m <= fill_60m <= fill_eod`);
5. no use of 2026 rows;
6. no feature selection or model fitting in the target-ledger phase.
