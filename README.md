# FactorLab Reversal / Mean-Reversion Research

This is the **single canonical repository** for the project formerly split across `factorlab-overnight-open-lab` and the temporary `factorlab-overnight-gap-fill-repeat-2026` input-pack repository.

## Current scientific status

The broad Stage-1 direction-discovery round is closed. The strongest mechanism is the R1 specialist:

`rmr_cross_scale_pullback_parent_integrity_v2`

The selected parent-state representation is the low-capacity composite:

`parent_integrity = (z(abs_drift) - z(overlap) + z(parent_eff)) / 3`

with counter-move severity kept exactly as in the promoted broad R1 screen:

`severity = abs(counter_move) / DEV_median_rvol20`.

The representation was selected on consumed 2015–2022 evidence, frozen without using 2023–2025, and then confirmed without refitting on the independent within-program 2023–2025 mechanism holdout:

- PAIR_A (S1 inside S2): Brier `0.18919349 -> 0.17919907`, 792 resolved events;
- PAIR_B (S2 inside S3): Brier `0.18028120 -> 0.16985390`, 322 resolved events;
- annual Brier improvement was positive in all six year × pairing cells for 2023/2024/2025.

This is strong mechanism confirmation, but **not scientifically fresh**, because 2023–2025 market history had been consumed elsewhere in the wider research history.

R5-C event density remains a weaker Priority-B secondary mechanism. R2 is on hold; R3, R4/V2.1-P2, R5-A, R5-B, R6 and R7 are closed under their tested identities.

## Next scientific gate

The next allowed R1 test is the preregistered **complete 2026Q4 true-fresh challenge**:

- window: `2026-10-01 .. 2026-12-31`;
- partial October or October–November scoring is forbidden;
- earliest execution date in China: `2027-01-01`;
- future source admission must be completed without reading outcomes first;
- the frozen R1 parameter bundle may not be refit or changed;
- both scale pairings must pass their sample and Brier/log-loss gates.

No PnL/entry/stop/holding-period optimization is authorized before that true-fresh gate passes. Production authority is false.

## Read first

1. `CONTINUE_HERE.md` — exact current action and prohibitions.
2. `docs/governance/reversal_mean_reversion_program_state_v1.json` — repository-wide machine-readable state.
3. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json` — R1 specialist state.
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json` — frozen next gate.
5. `docs/INDEX.md` — compact map of current evidence and history.

## Repository layout

- `docs/governance/` — only current/frozen governance required for R1 and the project state.
- `docs/research/` — current R1 evidence plus compact program closeouts/background.
- `docs/ops/` — only the queued R5-C secondary handoff.
- `scripts/` and `tests/` — the minimal R1 reproduction surface used for selection/holdout reconstruction.
- `data/high_open_dev_2015_2025/` — the frozen CSI1000 one-minute source used by the R1 development/holdout evidence.
- `archive/data/gap_fill_repeat_2026/` — the legacy repeat-only pack consolidated from the retired temporary repository.
- `docs/archive/README.md` — immutable history anchors for everything removed from the current worktree.

## Repository consolidation

On 2026-09-08 the temporary repository `staryocean0/factorlab-overnight-gap-fill-repeat-2026` was consolidated into this repository. Its two parquet files were already byte-identical Git blobs in this repository. No second data copy was needed. The canonical manifest here contains the later user-authorized placement metadata.

The pre-cleanup full research tree remains permanently available in Git history at commit `21ddcceb79929f5cd318ac5b8aa4579539f70dd7`; the temporary repository's original one-commit data pack is anchored at `e160390c8f9b700227b0c0203926c04bdce9f602`.

Historical files may contain old `current_status` or `next_action` fields. They are evidence for their own frozen experiments only and **never override the current authority files listed above**.
