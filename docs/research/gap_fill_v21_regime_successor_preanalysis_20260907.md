# Gap-Fill V2.1 regime-conditioned successor — preanalysis — 2026-09-07

## Research identity

New identity:

`gap_fill_v2_1_regime_conditioned_successor`

This identity is motivated by the valid but negative final Audit-B result of
`gap_fill_cross_index_transport_v1`. It does **not** modify or rescue that old
identity. All CT-DEV / Audit-A / Audit-B outcomes are consumed evidence for
V2.1 mechanism development.

The frozen CSI1000 V2-v1 identity remains unchanged. The CSI1000 2026Q4 true-
fresh block also remains unopened and scientifically independent.

## Failure that motivates the successor

Audit B showed a narrow failure rather than a general collapse:

- CSI300 high: 6/6 gates;
- CSI300 low: 6/6 gates;
- CSI500 low: 6/6 gates;
- CSI500 high: 4/6 gates.

For CSI500 high, all-gap probability quality still improved, and >30bp
non-inferiority still passed. The failure was concentrated in `abs_gap > 10bp`
and the 15m/60m horizons. The frozen T2 geometry model slightly underperformed
the fixed empirical benchmark there.

The V2.1 question is therefore not "how can we tune the old model until Audit B
passes?". It is:

> Which state observable at or before 09:31 distinguishes information-supported
> material high gaps from temporary/idiosyncratic opening dislocations, so that
> short/medium-horizon fill hazard can be conditioned without destroying the
> low-capacity geometry structure?

## Timing contract

V2.1 remains a post-open-gap prediction problem. At scoring time the current
09:31 **open** of the target index is observed by definition. The 09:31 opens of
other broad indices are also allowed because they are simultaneous opening-state
information, not post-09:31 path information.

Forbidden initial successor inputs include any target-day high/low/close after
09:31, any 09:32+ China information, or any feature whose timestamp is not known
by the 09:31 scoring instant.

## Phase V21-RD1 — consumed-evidence mechanism diagnostic

RD1 is diagnostic only. It does not select a successor model, threshold,
hyperparameter or trading rule.

Allowed outcome-bearing data are only the already-consumed external-index audit
blocks:

- Audit A: `2011-01-01 .. 2012-12-31`;
- Audit B: `2013-01-01 .. 2014-10-16`.

The already-sealed `2014-10-17 .. 2014-12-31` supporting crosscheck must remain
unopened.

Primary diagnostic cell:

- index: CSI500;
- sign: high gap;
- cohort: `abs_gap > 10bp`;
- horizons: 15m and 60m.

Secondary contrast cells:

- CSI300 high, `abs_gap > 10bp`, 15m/60m;
- CSI500 high all-gap and >30bp, descriptive only;
- low-gap heads, descriptive only.

## Frozen low-capacity mechanism probes

The probes are chosen for financial interpretation, not because of Audit-B
numerical fit.

### P1 — common-gap support

Definition for target index `i` and the other broad index `j`:

`common_gap_support = sign(gap_i) * gap_j / rvol20_j`

Interpretation: if the other broad index opens in the same direction with a
large normalized gap, the target gap is more likely to be a common information
repricing rather than an index-specific dislocation.

Preregistered direction: **higher support -> lower fill probability**.

### P2 — idiosyncratic relative-gap excess

Definition:

`relative_gap_excess = sign(gap_i) * (gap_i - gap_j) / rvol20_i`

Interpretation: a target-index gap that is unusually large relative to the other
broad index is more plausibly a target-specific opening pressure / overshoot.

Preregistered direction: **higher excess -> higher fill probability**.

### P3 — prior 20-session trend alignment

Definition using information strictly available before the current session:

`trend20_alignment = sign(gap_i) * (close_{t-1}/close_{t-21} - 1)`

Interpretation: a gap aligned with an established medium-horizon trend is more
likely to reflect persistent price discovery.

Preregistered direction: **higher alignment -> lower fill probability**.

### P4 — prior-day intraday alignment

Definition:

`prior_daytime_alignment = sign(gap_i) * (close_{t-1,15:00}/open_{t-1,09:31} - 1)`

Interpretation: a current gap aligned with the previous session's daytime move
has more continuation/information support.

Preregistered direction: **higher alignment -> lower fill probability**.

### P5 — prior 5-session relative momentum alignment

Definition:

`relative_momentum5_alignment = sign(gap_i) * [(close_i,t-1/close_i,t-6 - 1) - (close_j,t-1/close_j,t-6 - 1)]`

Interpretation: if the target index has already been outperforming the other
index in the same direction as the gap, the current opening move is more likely
to be part of a persistent relative-price regime rather than a transient
opening imbalance.

Preregistered direction: **higher alignment -> lower fill probability**.

No other RD1 probe may be added after the diagnostic outcome is opened.

## Diagnostic statistic: one-parameter probability-offset correction

For each probe and horizon, start from the already-frozen external T2
probability `p_base`. Fit only a one-dimensional diagnostic coefficient `beta`
on consumed evidence:

`logit(p_state) = logit(p_base) + beta * z(probe)`

where `z(probe)` is standardized within the evaluated cell.

This is not a candidate model and cannot be promoted directly. It is a compact
way to ask whether the state explains a systematic residual probability error
left by geometry.

Expected beta sign:

- P1, P3, P4, P5: `beta < 0`;
- P2: `beta > 0`.

Report beta, base log-loss, state-adjusted diagnostic log-loss, and delta
`base - adjusted`.

## RD1 mechanism-admission rule

A probe is `mechanism_supported_for_family_design` only if all conditions hold:

1. pooled Audit-A+Audit-B primary CSI500-high >10bp beta has the preregistered
   sign for both 15m and 60m;
2. pooled diagnostic log-loss improves for both 15m and 60m;
3. Audit-B-only beta has the preregistered sign for both horizons;
4. Audit-B-only diagnostic log-loss improves in at least one of the two
   horizons;
5. Audit-A-only beta has the preregistered sign in at least one of the two
   horizons;
6. CSI300-high >10bp pooled contrast is not directionally contradicted in both
   horizons (at least one horizon has the preregistered sign).

No p-value is used as a selection gate. Sample counts and descriptive likelihood
curvature / optimizer success must be reported.

A failed or reversed probe is excluded from the first V2.1 candidate family. Do
not flip its sign, replace it with a ratio, or rescue it by changing the cohort
or horizon after the diagnostic is opened.

## New independent external-index partitions — frozen before opening outcomes

The successor must not end with no audit data. Therefore the next unconsumed
CSI300/CSI500 history is partitioned now:

- `V21_DEV`: `2015-01-01 .. 2018-12-31`;
- `V21_AUDIT_A`: `2019-01-01 .. 2021-12-31`;
- `V21_AUDIT_B`: `2022-01-01 .. 2024-12-31`;
- `V21_EXTERNAL_RESERVE`: `2025-01-01 .. 2026-08-21`.

The sealed `2014-10-17 .. 2014-12-31` block is intentionally skipped and remains
under its prior descriptive-only supporting-crosscheck identity.

RD1 may inventory future blocks using only `symbol`, `trading_day`, `timestamp`
for coverage / exact-240 counts. RD1 must not read future-block OHLC, construct
future gaps/fill targets, or score any model on 2015+ external outcomes.

If a future partition has insufficient physical coverage, the date boundaries
must not be moved after outcomes are seen. Cloud must adjudicate the metadata
issue before any successor development outcome is opened.

## What happens after RD1

Cloud reviews the RD1 receipt and freezes a bounded V2.1 candidate family using
only admitted probes. Only after that freeze may `V21_DEV` outcomes be opened.
Candidate selection on `V21_DEV` will be followed by sealed `V21_AUDIT_A`, then
sealed `V21_AUDIT_B`; the 2025-2026 external reserve remains untouched until
needed.

Production authority remains false. Trading-return optimization is outside this
research identity.
