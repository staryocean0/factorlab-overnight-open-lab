# R1 economic translation v2 adjudication — 2026-09-08

Decision:

`VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`

Research identity:

`rmr_R1_parent_integrity_economic_translation_v2`

## Frozen change from v1

V2 kept the same R1 mechanism, next-observed-minute entry, original recovery / parent-failure exits, 1200-bar horizon and 10bp round-trip cost. The only new filter was:

1. `p_candidate > p_severity_only`; and
2. binary-boundary structural expected net return > 0,

where

`E_struct = p_candidate * recovery_gross + (1-p_candidate) * failure_gross - 0.0010`.

No probability, expectancy, cost, entry, exit, scale or horizon threshold was searched.

## Validation result

The candidate failed the unchanged v1 validation gates on both pairings.

### PAIR_A

- all-event validation n: 1,199;
- filtered candidate n: 77 versus required 400;
- candidate mean net return: approximately `-0.00011124` per trade;
- all-event baseline mean net return: approximately `-0.00132078`;
- candidate improved over the all-event baseline but remained slightly negative;
- positive annual mean return only in 2024 and 2025 (2/5 versus required 4/5).

### PAIR_B

- all-event validation n: 517;
- filtered candidate n: 50 versus required 150;
- candidate mean net return: approximately `+0.00040427` per trade;
- all-event baseline mean net return: approximately `-0.00073347`;
- positive annual mean return in 2021, 2022 and 2025 (3/5 versus required 4/5).

## Interpretation

The v2 structural-expectancy filter improves mean return relative to trading every R1 event, but it is far too selective under the unchanged sample gates and does not produce stable positive economics on both scales.

The failure is informative: a recovery-vs-failure probability model is not automatically the right model for realized economic return. The realized trade includes payoff geometry, overshoot and censored/horizon exits. Treating `1-p_recovery` as the full failure-side economic state is too coarse for a stable trading rule.

## Consequence

- v2 is closed under this identity;
- no threshold loosening or cost/entry/exit rescue is allowed;
- BLACKBOX was not queried;
- reusable blackbox ledger remains at one completed query (the parent R1 mechanism certification);
- a materially new economic identity may use DEV / VALIDATION to model realized net return directly, while BLACKBOX remains sealed until that identity passes validation.

Production authority remains false.
