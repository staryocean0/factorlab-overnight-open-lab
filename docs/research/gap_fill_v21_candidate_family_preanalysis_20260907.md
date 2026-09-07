# Gap-Fill V2.1 P2 candidate-family preanalysis — 2026-09-07

## Why this stage exists

The predecessor cross-index transport identity failed narrowly rather than globally. The unresolved state was CSI500 high gaps above 10bp, where 15m/60m probability quality stopped reliably beating the frozen empirical benchmark while all-gap and EOD behavior remained materially healthier.

RD1 then tested five preregistered state mechanisms on already-consumed evidence. Only `P2_relative_gap_excess` survived the frozen admission rule. The supported interpretation is that the target-specific component of the observed opening gap, relative to the other broad index, contains information about whether the opening move is a transient dislocation rather than common-information repricing.

That evidence is mechanism evidence only. The RD1 beta cannot be copied into a successor, and no future V21 outcome has been opened.

## The key confound to control

A new 2015–2018 development block is much later than the old 2005–2010 cross-index training period. A simple refit of the original geometry model could improve merely because parameters drifted over time.

Therefore V2.1 must not ask only whether a model containing P2 looks better than the old frozen model. It must ask whether P2 adds value beyond a **same-era geometry refit trained on exactly the same folds**.

This same-era geometry refit is a control, not a promotable V2.1 successor by itself.

## Frozen low-capacity ladder

The candidate family contains only three P2 overlays. All preserve the original geometry hazards and add P2 as a residual logit offset to the 15m and 60m high-gap hazards.

### 1. `P2_XI_SHARED_1B`

One beta is shared across:

- CSI300 high 15m;
- CSI300 high 60m;
- CSI500 high 15m;
- CSI500 high 60m.

This is the strongest transport hypothesis and the lowest-capacity general statement: the same relative-dislocation mechanism operates across both broad indices and both short/medium horizons.

### 2. `P2_CSI500_SHARED_1B`

If the cross-index shared form fails, one beta is allowed to be CSI500-specific while remaining shared across 15m/60m.

This tests whether the mechanism is real but index-local.

### 3. `P2_CSI500_STAGE_2B`

Only if both one-beta candidates fail, CSI500 may use separate 15m and 60m betas.

This is the maximum complexity permitted in the first V2.1 family. It tests horizon heterogeneity without opening the door to feature, threshold, model-class or interaction search.

The ladder stops at the first eligible candidate. A later, more flexible model cannot replace an earlier eligible model merely because its DEV score is numerically better.

## Candidate math

For an affected hazard stage:

`h_candidate = expit(logit(h_geometry_control) + beta * z(P2))`

where:

`P2 = sign(gap_i) * (gap_i - gap_j) / rvol20_i`

and `z(P2)` is standardized only from the training portion of the relevant index-high rows. Validation rows use the frozen training mean and scale.

The beta optimizer is allowed to search `[-6, 6]`; its sign is **not** constrained during fitting. Positive beta is instead an eligibility condition. This preserves the possibility that new DEV evidence genuinely contradicts the RD1 direction.

The EOD stage hazard remains the geometry-control EOD hazard. Earlier hazard changes naturally propagate into cumulative EOD probability through the discrete-time hazard identity, so EOD is still reported, but it is not a primary V2.1 selection or confirmation horizon.

## Why EOD is descriptive rather than primary

There are two independent reasons.

First, the predecessor failure and RD1 mechanism evidence were localized to 15m/60m. The EOD score was not the unresolved scientific problem.

Second, the newly admitted future source contract treats 14:59 as a source-specific optional observation. No missing bar is synthesized. This has no effect on the 15m or 60m targets, but it makes EOD slightly more source-contract dependent. V2.1 therefore keeps EOD visible while refusing to let that source quirk become a primary selection axis.

## DEV design

V21_DEV remains frozen at 2015–2018. The candidate family will use expanding natural-year OOF validation:

- train 2015 -> validate 2016;
- train 2015–2016 -> validate 2017;
- train 2015–2017 -> validate 2018.

Within every fold, the geometry control and P2 candidate use identical target-valid rows. The control is refit only on the fold training period. P2 is then fitted as a residual offset on that training control.

The primary cell is inherited from the observed predecessor failure rather than searched on DEV:

`CSI500 high, abs_gap > 10bp, 15m/60m`.

Each validation year must contain at least 20 primary rows and the pooled OOF primary cell at least 60 rows. Otherwise the family is evidence-insufficient rather than rescued by changing dates or thresholds.

## What an eligible candidate must demonstrate

An eligible candidate must, before any audit is opened:

1. improve CSI500-high >10bp 15m Brier versus the same-fold geometry control;
2. improve the corresponding 60m Brier;
3. improve the two-horizon mean log-loss;
4. not worsen all-gap two-horizon mean Brier;
5. beat the expanding empirical benchmark on primary two-horizon mean Brier;
6. improve primary two-horizon mean Brier in at least two of the three validation years, with positive median annual improvement;
7. retain the positive P2 direction in at least two of three expanding fits, with positive median beta for every beta component;
8. preserve probability nesting.

The cross-index-shared candidate has an additional requirement: it may not worsen CSI300-high all-gap or >10bp two-horizon mean Brier relative to the same geometry control.

If no candidate passes, V2.1 does not promote a P2 successor. The geometry refit remains only a diagnostic drift control. A new mechanism family, if any, must then be separately motivated and preregistered.

## Audit gates are frozen before DEV

The main purpose of this document is not just to freeze the DEV family. The primary Audit-A and Audit-B gates are also frozen now, before DEV outcomes are opened.

For the selected frozen candidate, both future audits must independently show in CSI500-high >10bp:

- lower 15m Brier than the frozen geometry control;
- lower 60m Brier;
- lower two-horizon mean log-loss;
- no worsening of all-gap two-horizon mean Brier;
- lower primary two-horizon mean Brier than the frozen full-DEV empirical benchmark;
- positive primary two-horizon Brier improvement in at least two of the three full calendar years;
- zero probability-nesting violations.

Audit A cannot alter the candidate, beta, scaler, control, benchmark or gates before Audit B. Audit A and Audit B cannot rescue each other by pooling. The 2025–2026 external reserve cannot replace either audit.

## Current authority boundary

This candidate family is frozen now, but execution is not authorized yet.

Before any V21_DEV OHLC or target is opened, cloud still requires:

1. verification of the new future-source admission receipt or data package identity;
2. metadata-only re-inventory of V21_DEV under `session_complete_239_required_v1`;
3. explicit update of V21 state authorizing DEV open.

Until then:

- V21_DEV remains sealed;
- Audit A/B remain sealed;
- External Reserve remains sealed;
- no successor fit or selection is authorized;
- CSI1000 post-2026-08-21 fresh outcomes remain sealed;
- production authority remains false.
