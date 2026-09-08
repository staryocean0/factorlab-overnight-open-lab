# CONTINUE HERE — Reversal & Mean-Reversion Discovery Program

**This file is the first authority for deciding what this repository should do next.**

The repository slug `factorlab-overnight-open-lab` is historical. As of 2026-09-08, the active program is a **broad reversal / mean-reversion discovery program** whose job is to identify, compare, and graduate promising mechanism families.

## Mission

The central question is:

> **Given the current scale and market state, has price temporarily deviated from an intact normal state, or has the normal state itself changed?**

A “mean” may be a line, band, trajectory, distribution, cross-asset relationship, wave structure, or state-conditioned statistical expectation.

The most important discrimination problem is:

> **temporary lower-scale deviation within an intact parent state vs. true change of the parent state.**

## Active research lanes

Keep the three primary lanes on an equal shallow budget until all three have one comparable Stage-1 result.

1. **R1 — Cross-scale pullback inside an intact parent trend**
   - Can a lower-scale counter-move be distinguished from a true parent-state failure before the outcome?

2. **R2 — Range-boundary / failed-breakout reversion**
   - Can a causal range excursion be distinguished from a genuine new-state breakout before the outcome?

3. **R3 — Regime-conditioned residual reversion**
   - Is deviation from a state-conditioned normal path more stably mean-reverting than deviation from one unconditional mean?

Secondary lanes:

4. **R4 — Relative-value / cross-asset dislocation** — legacy Gap-Fill / cross-index work.
5. **R5 — Statistical-state extremes** — future exploratory source, not a first deep target.

## Current scientific state — 2026-09-08

The broad program has already completed the results-blind design work that older versions of this file listed as “next action”:

- common scale / parent-state / deviation / recovery vocabulary: **frozen**;
- broad literature constraints: **mapped**;
- R1 preanalysis: **frozen**;
- R2 preanalysis: **frozen**;
- R3 preanalysis: **frozen**;
- equal-budget Stage-1 screening plan: **frozen**;
- common Stage-1 dataset and evidence roles: **frozen**;
- two causal directional-change scale pairings: **frozen**;
- exact R1/R2/R3 event and first-passage semantics: **frozen**;
- parallel Stage-1 runner and fail-closed tests: **implemented and execution-frozen**.

Current program stage:

`stage1_parallel_empirical_execution_frozen_pending_receipt`

## Frozen common Stage-1 data

Use exactly:

`data/high_open_dev_2015_2025/1m_official.parquet`

- instrument: `000852.SH` / CSI1000;
- window: `2015-01-05 .. 2025-12-31`;
- SHA256: `11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce`;
- role: **development material only**;
- scientific fresh-OOS label: **false**.

This interval was already consumed by prior legacy work. It is valid for broad mechanism discovery, but never becomes fresh again.

Forbidden to broad Stage 1:

- `2026-01-05 .. 2026-08-21`;
- `2026-08-24 .. 2026-12-31`;
- any future broad audit reserve.

A later deep identity must freeze its own genuinely unseen challenge.

## Frozen Stage-1 measurement scales

Both must run; neither may be selected after seeing outcomes:

- `PAIR_A`: lower directional-change threshold `0.50 × prior sigma20`; parent `1.50 × prior sigma20`;
- `PAIR_B`: lower `0.75 × prior sigma20`; parent `2.25 × prior sigma20`.

The common volatility unit is the 20 completed-session close-to-close log-return standard deviation available strictly before the current session.

Completed pivots are causal: a provisional extreme becomes available only after the predeclared reversal confirmation. Future turning points are forbidden.

## Current next action

Execute exactly one equal-budget parallel Stage-1 screen:

Task ID: `RMR-STAGE1-PARALLEL-01`

Runner:

`scripts/run_rmr_stage1_parallel_screen.py`

Execution handoff:

`docs/ops/rmr_stage1_parallel_screen_execution_handoff.md`

Execution freeze:

`docs/governance/reversal_mean_reversion_stage1_execution_freeze_v1.json`

The run must execute **R1, R2, and R3 together** on the same source and both scale pairings. Do not run one lane, inspect it, then tune that lane before the others finish.

After the two compact local receipts appear, the cloud controller must compare all three lanes together on:

- effect direction;
- chronological stability;
- PAIR_A / PAIR_B consistency;
- event supply and censoring;
- incremental information beyond each lane’s simple baseline;
- definition/data complexity;
- independence from legacy R4.

At most two lanes may be promoted without a new program-level review. Promotion at this stage means only “worthy of a new deep research identity,” not validated trading alpha.

## Legacy R4 / Gap-Fill status

All prior V1, Gap-Fill V2, V2.1, cross-index, and source-admission artifacts remain immutable evidence for their own identities.

The bounded V21 P2 successor family is now formally closed:

`V21_DEV_no_P2_successor`

Reason: the preregistered CSI500-high `abs_gap > 10bp` primary sample had `68 / 15 / 52` rows in validation years `2016 / 2017 / 2018`; the frozen per-year minimum was `20`, so 2017 was evidence-insufficient. The rule may not be relaxed after seeing the result.

V21 Audit A, Audit B, external reserve, and supporting crosscheck remain sealed. Geometry control is not a V2.1 successor. R4 does not block the broad program.

Cloud adjudication:

`docs/research/gap_fill_v21_dev_cloud_adjudication_20260908.md`

## Research style

The program is a **direction finder**, not a single-strategy optimizer.

Default behavior:

- keep 2–3 active mechanisms alive in parallel;
- spend a small, comparable research budget on each;
- first establish phenomenon → causal/pre-event observability → stability;
- do not optimize thresholds, model classes, trading PnL, or execution in Stage 1;
- a failed lane is a useful closure, not something to rescue with post-hoc conditions;
- promote only the strongest lanes to dedicated deep research identities.

## Authority order

For repository-wide direction and next action, read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_charter_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/research/reversal_mean_reversion_program_whitepaper_v1.md`
5. `docs/governance/reversal_mean_reversion_common_measurement_contract_v1.json`
6. `docs/governance/reversal_mean_reversion_stage1_screening_plan_v1.json`
7. `docs/governance/reversal_mean_reversion_stage1_common_data_role_v1.json`
8. `docs/governance/reversal_mean_reversion_stage1_execution_protocol_v1.json`
9. `docs/governance/reversal_mean_reversion_stage1_execution_freeze_v1.json`
10. `AGENTS.md`
11. legacy overnight/gap-fill documents, which have authority only inside their historical identities.

If an older file says this repository has one bounded overnight-open task, that statement is superseded for repository-wide scope. Historical results remain unchanged.

Production authority remains `false`.
