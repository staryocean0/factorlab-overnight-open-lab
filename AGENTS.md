# AGENTS.md — repository operating rules

## 1. One project, one canonical repository

`staryocean0/factorlab-overnight-open-lab` is the only active repository for this research project.

`staryocean0/factorlab-overnight-gap-fill-repeat-2026` was a temporary input-pack repository and is retired. Do not recreate a second active research authority for the same project.

## 2. Authority

For current work, read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_state_v1.json`
3. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
4. `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json`
5. `docs/INDEX.md`

Historical files and old commits are immutable evidence, not current instructions. An old `current_status`, `next_action`, handoff or workflow must never override the authority list above.

## 3. Current scientific boundary

The active mechanism is `rmr_cross_scale_pullback_parent_integrity_v2` with frozen candidate `R1_PARENT_COMPOSITE_1D` and parameter bundle SHA256:

`e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c`

The 2023–2025 within-program mechanism holdout passed without refit. It is not scientifically fresh.

The next scientific gate is the complete 2026Q4 challenge. Until the complete block exists:

- do not inspect partial Q4 R1 outcomes;
- do not refit or tune the model;
- do not optimize PnL;
- do not manufacture a new broad lane merely to keep the project busy.

## 4. Research governance

- Freeze hypotheses, measurement rules, candidate budgets and gates before opening the corresponding outcome block.
- A failed frozen identity is closed unless a materially new identity is separately preregistered.
- Statistical-state reversion is not evidence of price-path mean reversion by itself.
- Keep development, consumed stability, mechanism holdout and truly fresh evidence labels explicit.
- Never call 2023–2025 fresh OOS for R1.
- Production authority is false until separately granted after future evidence and economic validation.

## 5. Repository hygiene

- Keep current authority concise and non-duplicative.
- Current tree should contain only active governance, compact decisive evidence, required data, and minimal reproduction code.
- Completed experimental workflows and closed-lane runners/tests belong in Git history, not the active surface.
- Do not copy the same raw data into multiple repositories or multiple active paths.
- Before adding a new file, check whether an existing current artifact already carries the same authority or evidence.

## 6. Historical recovery

The full pre-consolidation research tree is preserved at commit:

`21ddcceb79929f5cd318ac5b8aa4579539f70dd7`

The temporary repeat-pack repository's original state is preserved at commit:

`e160390c8f9b700227b0c0203926c04bdce9f602`

See `docs/archive/README.md` before restoring anything from history.
