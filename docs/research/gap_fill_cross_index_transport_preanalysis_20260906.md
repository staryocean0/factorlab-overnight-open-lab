# Gap-Fill cross-index transport v1 — preanalysis — 2026-09-06

## Purpose

Use newly admitted long-history CSI300 and CSI500 one-minute data to test whether the Gap-Fill V2 geometry structure transports beyond CSI1000, without mutating frozen CSI1000 V2 v1 and without opening CSI1000 2026Q4 prospective fresh evidence.

Research identity:

`gap_fill_cross_index_transport_v1`

Source adjudication:

`docs/research/gap_fill_v2_he00_cloud_source_adjudication_20260906.md`

## Two transport questions; no winner selection

This study has two distinct estimands and does **not** choose between them as competing candidates.

### T1 — exact-parameter transport

Apply the frozen CSI1000 V2 v1 parameter bundle unchanged to CSI300 and CSI500.

This tests whether the exact scaling, intercepts and geometry slopes learned on CSI1000 are portable to other China equity indices.

No fitting occurs in T1.

### T2 — architecture transport

Keep the architecture exactly fixed but allow each external index to fit its own parameters on its own development history:

- separate high-gap and low-gap heads;
- three discrete-time stages: 15m, 15→60m, 60m→EOD;
- runtime features exactly `abs_gap`, `abs_gap_over_rvol20`;
- `StandardScaler(with_mean=true, with_std=true)`;
- `LogisticRegression(C=1, penalty=l2, solver=lbfgs, class_weight=None, fit_intercept=true, max_iter=1000)`;
- no probability calibration;
- no binary threshold.

This tests whether the financial/mathematical relation `gap geometry -> gap-fill hazard` is transportable even if index-specific probability levels differ.

No alternative model class, C, feature set, threshold, gap threshold, horizon or interaction is tested in this route.

## Fixed index windows

### CSI300 / 000300.SH

- DEV: `2005-04-08 .. 2010-12-31`;
- Audit A: `2011-01-01 .. 2012-12-31` — sealed now;
- Audit B: `2013-01-01 .. 2014-10-16` — sealed now;
- supporting crosscheck: `2014-10-17 .. 2014-12-31` — sealed now.

### CSI500 / 000905.SH

- DEV: `2007-01-15 .. 2010-12-31`;
- Audit A: `2011-01-01 .. 2012-12-31` — sealed now;
- Audit B: `2013-01-01 .. 2014-10-16` — sealed now;
- supporting crosscheck: `2014-10-17 .. 2014-12-31` — sealed now.

Only DEV outcomes may be opened in CT-DEV. Audit A/B/crosscheck must not be touched.

## Clock and row-validity contract

Use the admitted raw canonical one-minute lake, not the 2015+ densified FactorLab export.

For a target day to enter the first transport generation:

1. current day must contain exactly the complete official 240 clocks from 09:31 through 15:00 with no duplicates;
2. current 09:31 open must exist;
3. previous China trading day's 15:00 close must exist;
4. prior-20-session `rvol20` must be computable from 15:00 closes using the same frozen formula and no fill;
5. no missing minute may be inferred, forward-filled or treated as a non-event.

Using common complete-240-clock target rows intentionally sacrifices sample size to remove ambiguity from missing 14:59 or other source minutes.

## Target contract

For target day D and previous China session P:

`gap_D = open_09:31(D) / close_15:00(P) - 1`

High gap fully fills when a later low touches/crosses `close_15:00(P)`.
Low gap fully fills when a later high touches/crosses `close_15:00(P)`.

Horizons:

- 15m: 09:31..09:45 inclusive;
- 60m: 09:31..10:30 inclusive;
- EOD: all 240 target-day minutes.

Targets must satisfy `fill_15m <= fill_60m <= fill_eod`.

## Runtime features

- `abs_gap = abs(gap)`;
- `rvol20 = close_1500.pct_change(fill_method=None).shift(1).rolling(20,min_periods=20).std()`;
- `abs_gap_over_rvol20 = abs_gap / rvol20`.

## T2 development evaluation

T2 is evaluated by expanding natural-year OOF inside DEV before the final external-index parameter fit.

CSI300:

- minimum training: 2005-04-08..2006-12-31;
- OOF validation years: 2007, 2008, 2009, 2010.

CSI500:

- minimum training: 2007-01-15..2008-12-31;
- OOF validation years: 2009, 2010.

For each fold, the benchmark is the training-fold empirical high/low stage hazards. It is transformed into cumulative 15m/60m/EOD probabilities with the same hazard formula as the model.

After OOF reporting, one final T2 parameter bundle per index is fit on the full admitted DEV window solely to freeze the future Audit-A identity. The final DEV fit is not used to claim OOF skill.

## Mandatory CT-DEV reporting

For each index and each transport mode report:

- total / high / low target-valid rows;
- >10bp and >30bp counts by sign;
- Brier, log-loss, ROC-AUC, PR-AUC at 15m/60m/EOD;
- equal-weight integrated Brier/log-loss;
- monotonicity violations;
- annual summaries.

For T2 expanding OOF also report benchmark metrics and improvements.

T1 DEV results are descriptive external-parameter transport evidence only. T2 OOF results are development mechanism evidence only. Neither is fresh evidence.

## No Audit A opening in this step

CT-DEV ends after:

- T1 DEV report;
- T2 expanding OOF report;
- final index-specific T2 parameter freeze.

Cloud must review those artifacts before separately authorizing Audit A.

Audit B remains sealed even after Audit A is later opened.

## Relationship to V2.1

Cross-index DEV outcomes may later be used as development evidence for a distinct V2.1 mechanism/family protocol. They cannot modify frozen V2 v1 under the same identity and cannot inherit V2 v1 repeat/fresh labels.

CSI1000 2026-08-24..2026-12-31 remains sealed.

Production authority remains false.
