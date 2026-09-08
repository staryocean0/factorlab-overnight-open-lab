# R1 parent-integrity v2 — representation-selection cloud adjudication — 2026-09-08

Decision:

`R1_PARENT_INTEGRITY_V2_selection_pass_composite_1D_selected_holdout_may_be_authorized`

## Integrity

GitHub Actions run `34186521059` completed successfully at `05dc17690c9fec9d7babecd80bde334e41b77d8e`.

Synthetic/boundary tests, the frozen selection runner, holdout-seal checks and artifact upload all passed. The runner read CSI1000 only through `2022-12-30`. The 2023–2025 mechanism holdout and all 2026 rows remained unopened.

## Complexity-ladder result

The first and simplest candidate, `R1_PARENT_COMPOSITE_1D`, passed every frozen gate at both mandatory pairings. Therefore the second candidate `R1_PARENT_ORIGINAL_3D` was not evaluated for selection.

PAIR_A S1-inside-S2:

- stability n = 763;
- severity-only Brier `0.180902`;
- composite Brier `0.172233`;
- improvement `0.008669`;
- log-loss improvement `0.019039`;
- annual Brier improvement positive in 2020, 2021 and 2022.

PAIR_B S2-inside-S3:

- stability n = 291;
- severity-only Brier `0.162848`;
- composite Brier `0.156632`;
- improvement `0.006216`;
- log-loss improvement `0.012504`;
- annual Brier improvement positive in 2020, 2021 and 2022.

This is stronger stability than the broad 3D evidence at the coarse pairing, while using a lower-capacity scalar representation.

## Mechanistic interpretation

After full 2015–2022 refit, the frozen parent-integrity coefficient is positive at both scales:

- PAIR_A: `+0.457797`;
- PAIR_B: `+0.375419`.

Thus, holding counter-move severity fixed, higher preregistered parent integrity is associated with higher recovery-before-parent-failure probability in the consumed evidence.

The overlap input has zero variance in these pairing samples; after frozen standardization it contributes zero. The selected scalar is therefore effectively carried by absolute parent drift and parent path efficiency under the preregistered orientation. This is reported as a property of the consumed data, not used to redesign the formula.

## Parameter freeze

Frozen bundle:

`docs/governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json`

Bundle SHA256:

`e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c`

The severity baseline and selected composite models are frozen separately for both scale pairings using all consumed 2015–2022 resolved events.

## Authorization consequence

The prerequisites for a one-time 2023–2025 mechanism-holdout evaluation are satisfied, subject to a separate holdout protocol/execution freeze that must:

- use only the frozen selected candidate and frozen models;
- perform no refit;
- preserve both scale pairings;
- apply the already-frozen holdout sample/performance gates exactly;
- keep all 2026 rows sealed;
- make no fresh, PnL or production claim.

The holdout may not alter the candidate family regardless of result.

Production authority remains false.
