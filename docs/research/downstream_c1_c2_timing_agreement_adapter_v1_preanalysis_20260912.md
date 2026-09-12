# OFP-E1 v2 C1/C2 timing-agreement adapter — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_c1_c2_timing_agreement_adapter_v1`

## Motivation

This is a new downstream adapter identity enabled by a new upstream authority that did not exist when E1 v1 was frozen: C2 60m prior-volatility context has since passed reusable BLACKBOX validation (`a1068de9321c04632aad`).

The mechanism is fixed before opening this adapter's outcomes. C1 remains the only direction source for the 15-minute target. C2 is not allowed to reverse direction, set a magnitude, or create a threshold; it may only abstain when its frozen continuous directional implication disagrees with C1 at the natural zero boundary.

This identity is not a rescue of the failed C1+B4 E1 v1 identity. B4 is excluded. No E1 query-6 hidden behavior is used.

## Frozen upstream coordinates

C1 validated continuous interaction:

`trend_gap_interaction = (gap / rvol20) * (r20 / (sqrt(20) * rvol20))`

C1 frozen negative direction implies:

`c1_direction_score = -trend_gap_interaction`

C2 validated continuous interaction:

`vol_gap_interaction = (gap / rvol20) * log(rvol20)`

C2 frozen negative direction implies:

`c2_direction_score = -vol_gap_interaction`

## Frozen adapter

`c1_action = sign(c1_direction_score)`

`c2_action = sign(c2_direction_score)`

Comparator:

`comparator_action = c1_action`

Candidate:

`candidate_action = c1_action if c1_action * c2_action > 0 else 0`

Thus C2 can only abstain; it cannot reverse C1.

Zero is the only boundary. There are no fitted weights, magnitude thresholds, quantiles, volatility buckets, trend buckets, or interaction searches.

## Frozen target

`ret_0935_0950 = close_0950 / close_0935 - 1`

The target stays at 15 minutes because C1 is the direction source and its validated consumer horizon is 09:35→09:50. No 30m/60m target search is allowed under this identity.

## Evidence boundary

Development material only: `2015-01-05..2020-12-31`, reported pooled and by natural year 2015..2020.

The 2021–2025 reusable block is not opened by this preanalysis. If Development progresses, reusable validation requires a separately frozen compact identity/protocol. Reuse of 2021–2025 is not independent OOS.

No account PnL, costs, instrument mapping, position sizing or production claim is part of this phase.

## Frozen diagnostics

For each natural year and pooled:

- complete-case count;
- comparator active days;
- candidate active days / coverage;
- comparator hit rate;
- candidate active hit rate;
- mean comparator signed utility;
- mean candidate signed utility;
- delta mean signed utility.

Signed utility is `action * ret_0935_0950`.

## Sufficiency

Each year must have at least 150 complete cases and at least 30 candidate-active days.

## Progression gates

Progression requires all of:

- pooled delta mean signed utility > 0;
- at least 4 of 6 annual deltas > 0;
- median annual delta >= 0;
- all annual sufficiency gates pass.

Passing grants only `retrospective_factor_utility_adapter_candidate_only` and does not grant a validated adapter or executable strategy.

## Forbidden post-result actions

Do not search nonzero C1/C2 thresholds, magnitude buckets, fitted weights, alternate sign conventions, alternate horizons, or extra upstream products. Do not use hidden reusable-BLACKBOX behavior from any prior query to rescue this identity.

`production_authority=false`.
