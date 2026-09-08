# R1 parent-integrity v2 — 2023–2025 mechanism-holdout cloud adjudication — 2026-09-08

Decision:

`R1_PARENT_INTEGRITY_V2_holdout_confirmed_not_fresh`

## Execution integrity

GitHub Actions run `34186751735` completed successfully at `23ec8e6550814fe81fb148f9d8c382d5f41b8c43`.

The holdout evaluator passed its frozen tests, then replayed the selected candidate and severity baseline without fitting. Boundary checks confirmed:

- parameter bundle unchanged: `e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c`;
- no refit;
- no candidate change;
- no scale/threshold search;
- no calibration or binary threshold;
- no trading-return use;
- no 2026 rows read.

The opened window was exactly the pre-authorized within-program mechanism holdout `2023-01-01 .. 2025-12-31`.

## PAIR_A — S1 counter-move inside S2 parent

Holdout resolved events: `792`.

Year counts:

- 2023: 175;
- 2024: 371;
- 2025: 246.

Frozen severity baseline versus frozen 1D parent-integrity candidate:

- Brier `0.18919349 -> 0.17919907`, improvement `0.00999443`;
- log-loss `0.55999226 -> 0.53753870`, improvement `0.02245356`.

Annual Brier improvement is positive in **2023, 2024 and 2025**.

All preregistered PAIR_A gates pass.

## PAIR_B — S2 counter-move inside S3 parent

Holdout resolved events: `322`.

Year counts:

- 2023: 64;
- 2024: 158;
- 2025: 100.

Frozen severity baseline versus frozen 1D parent-integrity candidate:

- Brier `0.18028120 -> 0.16985390`, improvement `0.01042730`;
- log-loss `0.53822697 -> 0.51210924`, improvement `0.02611772`.

Annual Brier improvement is positive in **2023, 2024 and 2025**.

All preregistered PAIR_B gates pass.

## Scientific conclusion

The specialist result is stronger than a one-period discovery:

1. broad held-forward evidence in 2020–2022 showed parent context adding beyond counter-move severity;
2. a lower-capacity 1D integrity score was selected before holdout access;
3. its full 2015–2022 parameters were frozen;
4. the untouched within-program 2023–2025 mechanism holdout then improved both Brier and log-loss at both scale pairings, with annual Brier improvement positive in all six year×pairing cells.

This supports the mechanism:

> Conditional on counter-move severity, a stronger causally available parent state raises the probability that the lower-scale counter-move recovers before the parent structure fails.

The evidence is **not scientifically fresh**, because 2023–2025 raw market history has been consumed elsewhere in the wider research program. It is nevertheless an independent within-program mechanism holdout because those outcomes were not used to design/select this R1 specialist representation.

## What this does not authorize

This result does not authorize:

- PnL optimization;
- entry/stop/holding-period search;
- changing the parent-integrity formula;
- adding filters or indicators;
- production use;
- calling 2023–2025 fresh OOS.

The next scientific gate is a separately preregistered **truly future** complete-window challenge using the already frozen R1 identity and parameters.

Production authority remains false.
