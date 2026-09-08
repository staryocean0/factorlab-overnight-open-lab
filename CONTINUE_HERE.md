# CONTINUE HERE — Reversal & Mean-Reversion Discovery Program

**This file is the first authority for deciding what this repository should do next.**

The repository slug `factorlab-overnight-open-lab` is historical. As of 2026-09-08, the active program is no longer a single overnight-open or gap-fill strategy project. It is a **broad reversal / mean-reversion discovery program** whose job is to identify, compare, and graduate promising mechanism families.

## Mission

The central question is not “is price far from a moving average?” It is:

> **Given the current scale and market state, has price temporarily deviated from an intact normal state, or has the normal state itself changed?**

A “mean” may be a line, band, trajectory, distribution, cross-asset relationship, wave structure, or state-conditioned statistical expectation.

## Active research lanes

Research several lanes shallowly before taking any one lane deep.

1. **R1 — Cross-scale pullback inside an intact parent trend**
   - Example: a larger-scale uptrend is intact while a lower-scale sharp decline appears.
   - Main question: can we identify in advance when the decline is only a lower-scale fluctuation rather than the start of a same-scale reversal?

2. **R2 — Range-boundary / failed-breakout reversion**
   - Parent state is oscillatory/range-like rather than trending.
   - Main question: when is an excursion outside the normal range a temporary overshoot versus a genuine state transition/breakout?

3. **R3 — Regime-conditioned residual reversion**
   - Estimate the normal path/distribution conditional on the current regime, then study the residual from that normal state.
   - Main question: which residual extremes revert without assuming one stationary mean across all market regimes?

### Secondary lanes

4. **R4 — Relative-value / cross-asset dislocation**
   - Includes the existing overnight-gap / cross-index gap-fill work.
   - It remains valid historical evidence and a useful case study, but another specialized line already covers it. **Do not make it the main program unless the user explicitly reassigns it here.**

5. **R5 — Statistical-state extremes**
   - Path efficiency, volatility, frequency-band amplitude, clustering, asymmetry, wave duration, and similar market properties may themselves have state-dependent “means.”
   - Keep as an exploratory source of future lanes, not the first deep target.

## Research style

The program is a **direction finder**, not a single-strategy optimizer.

Default behavior:

- keep 2–3 active mechanisms alive in parallel;
- spend a small, comparable research budget on each;
- first establish phenomenon → causal/pre-event observability → stability;
- do not immediately optimize thresholds, model classes, trading PnL, or execution;
- promote only the strongest lanes to dedicated deep research identities/repositories;
- a failed lane is a useful closure, not something to rescue with post-hoc conditions.

## Common coordinate system

Every reversal hypothesis must state four things:

1. **Scale:** lower/current/parent scale.
2. **Parent state:** trend, range, transition, or unknown.
3. **Deviation object:** what is abnormal—price, path, wave, distribution, relative relationship, or statistical property?
4. **Recovery criterion:** what observable event counts as reversion, and over what causal horizon?

The most important discrimination problem is always:

> **temporary lower-scale deviation within an intact parent state vs. true change of the parent state.**

## Legacy overnight-open work

All prior V1, Gap-Fill V2, V2.1, cross-index, and source-admission artifacts remain immutable evidence for their own identities. They are **not deleted, rewritten, or called invalid**.

They are now classified as:

`legacy_specialist_case_study / delegated_subprogram`

Their sealed data boundaries and evidence labels remain binding if that specialist identity is resumed. However, an outstanding receipt, data blocker, or next action inside that legacy subprogram **does not block the broad program**.

## Authority order

For repository-wide direction and next action, read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_charter_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/research/reversal_mean_reversion_program_whitepaper_v1.md`
5. `AGENTS.md`
6. lane-specific protocols created after the authority reset
7. legacy overnight/gap-fill documents, which have authority only inside their historical identities

If an older file says this repository has one bounded overnight-open task, that statement is **superseded for repository-wide scope** by this authority reset. Historical results remain unchanged.

## Current stage and next action

Current stage: **Stage 0/1 — broad mechanism definition and shallow parallel screening.**

Next action:

1. freeze a common measurement vocabulary for scale / parent regime / deviation / reversion;
2. create shallow, bounded preanalysis for R1, R2, and R3;
3. identify the smallest data requirement and simplest falsifiable test for each;
4. compare evidence across lanes before selecting any deep research target.

Do **not** return to prolonged Gap-Fill V2.1 execution merely because its historical state files contain an unfinished next action.

Production authority remains `false`.
