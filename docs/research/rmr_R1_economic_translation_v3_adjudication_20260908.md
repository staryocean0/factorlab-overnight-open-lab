# R1 economic translation v3 adjudication — 2026-09-08

Decision:

`VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`

Research identity:

`rmr_R1_parent_integrity_economic_translation_v3`

## Frozen design

V3 stopped using recovery probability as the economic target. It directly modeled realized net return on DEV using one fixed low-capacity family:

- baseline features: `severity + recovery_gross + failure_gross`;
- candidate: baseline + `parent_integrity`;
- `StandardScaler + Ridge(alpha=1.0)`;
- trade only if candidate-predicted net return > 0 and > baseline-predicted net return;
- same next-minute entry, original R1 recovery/failure exits, 1200-bar horizon and 10bp round-trip cost;
- no alpha/feature/threshold/cost/entry/exit search.

## Validation result

### PAIR_A

- all-event validation n: 1,199;
- filtered candidate n: 3 versus required 400;
- candidate mean net return: approximately `-0.00360722` per trade;
- all-event baseline mean net return: approximately `-0.00132078`;
- only 2022 had positive annual candidate mean among years with any selected trades.

Every primary validation gate failed.

### PAIR_B

- all-event validation n: 517;
- filtered candidate n: 227 versus required 150;
- candidate mean net return: approximately `-0.00192866` per trade;
- all-event baseline mean net return: approximately `-0.00073347`;
- only 2025 had positive annual candidate mean.

The sample gate passed, but the mean-return, relative-to-baseline and annual-stability gates failed.

## Interpretation

Directly aligning the model target with realized net return did not rescue the economics. The candidate became extremely selective on PAIR_A and economically worse than the all-event baseline on both scales.

Together with v1 and v2, this is sufficient evidence that the current economic translation family — next-minute entry, original R1 structural exits and fixed 10bp cost — does not support a robust trading claim, despite the parent R1 mechanism itself being statistically strong.

## Consequence

- v3 is closed;
- no economic v4 is authorized from this validation evidence;
- no second BLACKBOX query occurred;
- the reusable BLACKBOX remains closed with exactly one completed query, the R1 mechanism certification;
- R1 remains a validated/certified mechanism, not a validated trading strategy;
- project research budget should move to the queued R5-C event-density mechanism rather than continue translating R1 economics post hoc.

Production authority remains false.
