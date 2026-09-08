# Broad reversal / mean-reversion Stage-1 lane comparison — cloud adjudication — 2026-09-08

## Decision

Program identity: `broad_reversal_mean_reversion_discovery_program_v1`.

This is the first equal-budget empirical comparison after the repository-wide authority reset.

Lane decisions:

- **R1 cross-scale pullback:** `progression_worthy — hand off to a dedicated deeper identity`.
- **R2 range-boundary / failed-breakout reversion:** `hold — mixed evidence, no promotion and no rescue tuning`.
- **R3 regime-conditioned residual reversion:** `close Stage1 v1 — not supported; no HMM/Koopman/deep-model escalation`.

No trading strategy is approved. No result is fresh. The unopened 2023–2025 program reserve remains unopened and cannot rescue a failed lane.

## Evidence boundary

Common source:

`data/high_open_dev_2015_2025/1m_official.parquet`

SHA256:

`11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce`

The source was already consumed by older specialist identities, so the broad program deliberately labels all of this evidence **not fresh**.

Frozen roles before this run:

- Stage1 DEV: `2015-01-05 .. 2019-12-31`;
- chronological stability: `2020-01-01 .. 2022-12-31`, explicitly not fresh;
- internal reserve: `2023-01-01 .. 2025-12-31`, unopened.

The empirical runner loaded only through `2022-12-30` (`466,961` one-minute rows). The reserve-boundary assertion passed.

Execution location was GitHub Actions only because the current cloud runtime actually attempted direct repository/data access and failed DNS resolution, while no directly invokable local-model channel was available in-session. Run `34182643377`, job `101924658265`, completed successfully. Synthetic/boundary tests, empirical execution, reserve-boundary verification and aggregate-receipt upload all passed.

This is Actions execution evidence, not direct cloud-local execution.

## Common scale definition

Scale was frozen from the **DEV volatility distribution, not the outcomes**.

Median lagged 20-session close-to-close volatility over 2015–2019:

`1.3783%`

Directional-change measurement scales:

- S1 ≈ `0.3446%`;
- S2 ≈ `0.6892%`;
- S3 ≈ `1.3783%`.

Two scale pairings were examined without selecting one after results:

- S1 lower move inside S2 parent structure;
- S2 lower move inside S3 parent structure.

Completed-wave counts through 2022 were approximately `11,389 / 4,358 / 1,512` for S1/S2/S3.

## R1 — Cross-scale pullback

### Question tested

Given a causally completed counter-move against the net drift of the last two completed parent waves, does parent-state information improve the ability to distinguish:

`recovery to the counter-wave origin first`

from

`break of the latest causal parent structural trough/peak first`?

The key comparator was deliberately simple:

- baseline: counter-move severity only;
- candidate: the same severity plus parent two-wave drift/overlap/path-efficiency measurements.

### Fine pairing: S1 inside S2

DEV events: `1,457`.

2020–2022 stability events: `763`.

Observed recovery-first share in stability: `71.43%`.

Pooled Brier:

- severity only: `0.18090`;
- parent state + severity: `0.17229`;
- improvement: `0.00862`.

Pooled log loss:

- severity only: `0.53941`;
- parent state + severity: `0.52070`.

Annual Brier improvement was positive in **all three** stability years:

- 2020: `+0.00882`;
- 2021: `+0.00606`;
- 2022: `+0.00996`.

### Coarser pairing: S2 inside S3

DEV events: `589`.

2020–2022 stability events: `291`.

Observed recovery-first share: `73.88%`.

Pooled Brier:

- severity only: `0.16285`;
- parent state + severity: `0.15601`;
- improvement: `0.00684`.

Pooled log loss:

- severity only: `0.49683`;
- parent state + severity: `0.48281`.

Annual Brier improvement was positive in 2020 and 2022 but slightly negative in 2021: **2 of 3 years**.

### R1 interpretation

This is the strongest finding of the first broad screen.

It supports the user-level hypothesis in a bounded form:

> The size of a sudden counter-move is not the whole story. Information about the already-completed parent structure adds held-forward information about whether the move recovers before the parent structure fails.

This does **not** yet establish a trading entry, an optimal wave scale, a universal trend definition, or fresh alpha. Parent-state-only models are not enough by themselves; the useful evidence is that adding parent context to the same counter-move severity baseline improves prediction.

Therefore R1 is progression-worthy, but the broad discovery repo should hand it off rather than spend many additional rounds optimizing it here.

## R2 — Range-boundary / failed-breakout reversion

### Fine pairing: S1 outside S2

DEV events: `2,002`.

Stability events: `1,198`.

Reentry-first share: `23.46%`.

Pooled Brier:

- excursion size only: `0.17796`;
- parent state + excursion-state measures: `0.17759`;
- improvement: only `0.00037`.

Annual improvement was negative in 2020 and 2021, positive only in 2022.

### Coarser pairing: S2 outside S3

DEV events: `975`.

Stability events: `583`.

Reentry-first share: `19.21%`.

Pooled Brier:

- excursion size only: `0.15099`;
- combined model: `0.14774`;
- improvement: `0.00325`.

The improvement was positive in all three stability years.

### Why R2 is not promoted

The combined coarse-scale result is interesting, but the scientific question was specifically whether a **range-like parent state** helps distinguish failed from true breakout.

Parent-range-state-only models were worse than the excursion-size baseline at both pairings. The combined model also includes breakout speed and local volatility change. Therefore the observed coarse-scale gain cannot cleanly be attributed to the parent range state itself.

The correct outcome is **hold**, not “tune until it works.”

R2 may be reconsidered later under a new bounded identity if an independent argument gives a cleaner causal range-state measurement. The current identity receives no second parameter/feature search round.

## R3 — Regime-conditioned residual

R3 asked whether a low-capacity state-conditioned normal return would produce a residual that mean-reverts more cleanly than an unconditional deviation.

At both parent scales, the predeclared reversion score had a **negative** pooled correlation with the next-session return:

- S2 conditional residual reversion correlation: about `-0.0717`;
- S3 conditional residual reversion correlation: about `-0.0725`;
- unconditional comparator: about `-0.0715`.

Thus this first-pass residual behaves slightly more like **continuation** than reversion, and state conditioning changes very little. Linear-prediction MSE is also essentially unchanged.

The Stage1 hypotheses are not supported.

The escalation rule was frozen before results: complex hidden-state, Koopman or deep latent-dynamics models are allowed only if the simple state-conditioned residual first demonstrates the phenomenon. It did not.

Therefore `R3_regime_conditioned_residual_stage1_v1` is **closed**. Do not introduce HMM/Koopman/deep models to rescue it under this identity.

This closure is about the specific low-capacity next-session residual formulation, not a universal theorem that every possible regime-conditioned residual can never revert.

## Cross-lane comparison

| Lane | first-pass evidence | stability | mechanism cleanliness | decision |
|---|---|---|---|---|
| R1 cross-scale pullback | clear incremental value beyond move severity | strong at fine scale; 2/3 years coarse | good enough for deeper dedicated work | **progress** |
| R2 range-boundary reversion | small gain only in combined coarse model | mixed across scales | parent-range mechanism not isolated | **hold** |
| R3 state-conditioned residual | no reversion; conditioning adds almost nothing | consistently unsupportive | clear negative first pass | **close v1** |

## Program consequence

The broad repo has now performed what the new authority asked it to do: several mechanisms received comparable shallow research budgets before any one was taken deep.

Next program behavior should be:

1. create a dedicated R1 promotion/handoff identity with the current evidence and untouched 2023–2025 internal reserve;
2. do not optimize R1 further in the broad direction-finder before that handoff;
3. leave R2 on hold without rescue tuning;
4. close R3 v1 and explicitly forbid complex-model escalation as a rescue;
5. activate the next broad exploratory lane (R5 statistical-state extremes is the current reserve candidate) so the direction-finder continues discovering rather than becoming an R1-only project.

Production authority remains false.
