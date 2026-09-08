# R1 economic translation v1 — VALIDATION adjudication — 2026-09-08

Identity:

`rmr_R1_parent_integrity_economic_translation_v1`

Decision:

`VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`

The strategy candidate was frozen before opening economic results:

`R1_EDGE_POSITIVE_NEXT_BAR_10BP`

It traded only when the R1 parent-integrity model raised recovery probability above the severity-only baseline, entered at the next observed one-minute close, used the original R1 recovery/failure boundaries, and deducted a fixed 10bp round-trip cost.

## PAIR_A

Detailed VALIDATION `2021-2025` results are allowed to be inspected under the reusable data policy.

All-event baseline:

- trades: 1,199;
- mean net return: `-0.0013207841`;
- median net return: `+0.0011541196`;
- win rate: `61.97%`.

Edge-positive candidate:

- trades: 454;
- mean net return: `-0.0010878576`;
- median net return: `+0.0016234669`;
- win rate: `68.06%`;
- mean holding bars: `166.43`.

Annual candidate mean net return:

- 2021: `-0.0031000528`;
- 2022: `+0.0000717780`;
- 2023: `-0.0011480306`;
- 2024: `-0.0011278502`;
- 2025: `-0.0012516603`.

The candidate improved on the all-event baseline but failed the positive pooled return and annual-stability gates.

## PAIR_B

All-event baseline:

- trades: 517;
- mean net return: `-0.0007334725`;
- median net return: `+0.0021092151`;
- win rate: `64.41%`.

Edge-positive candidate:

- trades: 193;
- mean net return: `+0.0002307577`;
- median net return: `+0.0031758623`;
- win rate: `75.65%`;
- mean holding bars: `267.01`.

Annual candidate mean net return:

- 2021: `-0.0047695219`;
- 2022: `+0.0025331156`;
- 2023: `-0.0046531398`;
- 2024: `-0.0002982375`;
- 2025: `+0.0036131397`.

PAIR_B passed pooled positive-return and baseline-improvement gates, but only 2/5 validation years were positive, so it failed the frozen annual-stability gate.

## Mechanistic diagnosis

The key reusable-validation finding is not that the R1 mechanism failed. The probability mechanism had already passed detailed validation and reusable blackbox certification.

Economic v1 failed because **probability edge alone does not account for asymmetric payoff geometry**. Both pairings show high win rates and positive median trade returns, while mean return is much weaker or negative. This is consistent with a minority of large structural-failure losses dominating many smaller recoveries.

A new economic identity may therefore use only causally observable entry-time recovery/failure distances to convert recovery probability into a structural expected-return test. It must not tune a probability threshold, cost, stop, target or time filter from these results.

## Blackbox boundary

The economic v1 blackbox step was skipped automatically because VALIDATION failed. Therefore:

- reusable blackbox query count remains `1`;
- there was no economic query #2;
- no blackbox metric, count or detail was opened.

Production authority remains false.
