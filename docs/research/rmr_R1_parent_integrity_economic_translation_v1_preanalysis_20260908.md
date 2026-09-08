# R1 parent-integrity economic translation v1 — preanalysis

Research identity:

`rmr_R1_parent_integrity_economic_translation_v1`

This stage asks whether the already blackbox-certified R1 mechanism can be translated into a simple implementable index-return rule without inventing a new indicator family.

## Fixed trading interpretation

At a causally confirmed lower-scale R1 counter-move:

1. reconstruct the same parent state and severity used by `rmr_cross_scale_pullback_parent_integrity_v2`;
2. compute the DEV-frozen severity-only recovery probability and parent-integrity augmented recovery probability;
3. trade only when the augmented probability is strictly greater than the severity-only probability;
4. direction is the parent-state direction;
5. enter at the **next observed one-minute close after event confirmation**;
6. skip the event if recovery or parent-failure boundary has already been crossed before that next-close entry;
7. exit at the first subsequent observed close that crosses the original R1 recovery boundary or parent-failure boundary;
8. if neither boundary resolves by the frozen 1200-bar horizon / available data boundary, exit at the censor close;
9. no same-pair overlapping trade until the prior event resolves/censors, inherited from R1 event geometry.

This creates one strategy candidate:

`R1_EDGE_POSITIVE_NEXT_BAR_10BP`

There is no probability threshold search. The mechanism filter is exactly:

`p_candidate - p_severity > 0`.

## Cost model

Primary gate uses a fixed **10 basis-point round-trip cost** subtracted from signed index return per trade.

No transaction-cost search, instrument-specific multiplier, leverage, financing, slippage optimization or position sizing is allowed in v1.

The strategy is an economic translation on CSI1000 index returns, not yet an executable IM/MO/ETF implementation.

## Data roles

Use repository-wide reusable roles:

- DEV: 2015-01-05 .. 2020-12-31;
- VALIDATION: 2021-01-01 .. 2025-12-31;
- BLACKBOX: 2026-01-05 .. 2026-08-21.

DEV and VALIDATION are detailed reusable research pools. BLACKBOX remains three-state only.

## Model use

For VALIDATION, fit severity baseline, parent-feature scaler and augmented model on DEV only. Do not refit using validation before scoring validation.

If both pairings pass all validation gates, perform one predeclared final refit on DEV+VALIDATION through 2025-12-31 using the unchanged strategy rule. Freeze that final bundle before blackbox.

## Detailed validation gates

For each pairing:

- minimum filtered trades: PAIR_A 400, PAIR_B 150;
- pooled mean net signed return after 10bp > 0;
- pooled candidate mean net return > the same-pair all-R1-events mean net return after 10bp;
- annual candidate mean net return positive in at least 4 of 5 validation years (2021–2025).

Both pairings must pass.

Validation may report detailed counts, annual returns, mean/median returns, win rate and holding duration.

## Reusable blackbox gate

Only after validation PASS and final refit freeze:

- minimum filtered trades: PAIR_A 40, PAIR_B 15;
- pooled mean net signed return after 10bp > 0;
- candidate mean net return > same-pair all-events mean net return after 10bp;
- both pairings required.

Blackbox output is only:

`PASS / FAIL / INSUFFICIENT`.

No blackbox count, mean return, year/month, win rate, holding time, event example or error analysis may be released.

## Forbidden rescue

- search probability thresholds;
- change entry delay after seeing validation;
- search stop/target/horizon;
- choose cost assumption from results;
- add parent-integrity cutoffs;
- add time-of-day/regime filters;
- combine PAIR_A and PAIR_B into a weighted portfolio to rescue one failing pairing;
- inspect blackbox details after certification.

Production authority remains false.
