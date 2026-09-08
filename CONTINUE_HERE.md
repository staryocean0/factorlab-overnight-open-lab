# CONTINUE HERE — Reversal & Mean-Reversion Discovery Program

**This file is the first authority for deciding what this repository should do next.**

The repository slug `factorlab-overnight-open-lab` is historical. The active repository-wide mission is broad **reversal / mean-reversion mechanism discovery**: distinguish a temporary deviation inside an intact state from a genuine state change, compare several mechanisms shallowly, and hand strong directions to dedicated identities rather than turning this repo into one strategy optimizer.

## Common scientific coordinate system

Every new reversal hypothesis must declare before outcome inspection:

1. **Scale:** lower / current / parent.
2. **Parent state:** trend / range / transition / unknown.
3. **Deviation object:** price / path / wave / distribution / relative relationship / statistical property.
4. **Recovery criterion:** reversion boundary, state-change/failure boundary, causal horizon and censoring rule.

Do not reduce mean reversion to “price moved far from a moving average.”

## Frozen evidence roles used by the broad Stage-1 screens

Common CSI1000 source:

`data/high_open_dev_2015_2025/1m_official.parquet`

- DEV: `2015-01-05 .. 2019-12-31`;
- chronological stability: `2020-01-01 .. 2022-12-31`, explicitly **not fresh**;
- internal program reserve: `2023-01-01 .. 2025-12-31`, **still unopened and not fresh**;
- all 2026 rows remain outside the broad Stage-1 program.

No broad Stage-1 result is production evidence.

## Current lane decisions

### R1 — Cross-scale pullback / parent integrity

Status: **progressed — Priority A specialist**.

The first equal-budget screen found that parent-state context adds held-forward information beyond counter-move severity at both frozen scale pairings.

Fine S1-inside-S2:

- stability events: 763;
- severity-only Brier `0.18090`;
- parent+severity Brier `0.17229`;
- annual improvement in 2020, 2021, 2022.

Coarse S2-inside-S3:

- stability events: 291;
- severity-only Brier `0.16285`;
- parent+severity Brier `0.15601`;
- annual improvement in 2020 and 2022; slightly negative in 2021.

Promotion handoff:

`docs/ops/rmr_R1_cross_scale_pullback_promotion_handoff_20260908.md`

Do not optimize R1 inside this broad repo. Dedicated work must first compress/interpret the parent-integrity representation, freeze a tiny family, and only then consider the untouched 2023–2025 mechanism holdout.

### R2 — Range-boundary / failed-breakout reversion

Status: **hold, not promoted**.

Fine-scale evidence was unstable. Coarse combined evidence was mildly positive, but parent range-state alone did not isolate the mechanism beyond excursion severity.

Do not rescue R2 by changing range algorithms, adding filters or tuning thresholds under the current identity.

### R3 — Regime-conditioned residual reversion

Status: **Stage-1 v1 closed**.

The frozen next-session residual screen did not show stable residual mean reversion or material advantage over unconditional deviation.

Do not escalate to HMM, Koopman or deep latent dynamics as a rescue under this identity.

### R4 — Legacy relative-value / Gap-Fill specialist

Status: **V21 P2 successor family closed**.

The authorized 2015–2018 DEV run found no eligible P2 successor because the preregistered annual sample-sufficiency gate failed in 2017. Audit A/B and future reserves remain sealed.

Cloud closeout:

`docs/research/gap_fill_v21_dev_cloud_adjudication_20260908.md`

R4 does not control the broad-program next action.

### R5 — Statistical-state extremes

Stage-1 v1 is complete.

Three preregistered properties were tested at frozen S1/S2 scales in GitHub Actions run `34184683011`; tests, runner and sealed-boundary checks all passed. The 2023–2025 reserve remained unopened.

#### R5-A path efficiency

**Closed.** The statistic itself strongly reverts toward its rolling normal region, but its incremental price-path information is not stable across both scales.

#### R5-B volatility-state displacement

**Closed.** S1 worsened the severity baseline; S2 improved only locally and reversed sign in 2022. Cross-scale evidence is not stable.

#### R5-C event density

**Progressed — Priority B specialist.**

S1:

- stability events: 2,329;
- Brier `0.2501610 → 0.2494158`;
- log-loss `0.6934787 → 0.6919783`;
- annual Brier improvement in 2020, 2021, 2022.

S2:

- stability events: 831;
- Brier `0.2489933 → 0.2489006`;
- log-loss `0.6911356 → 0.6909486`;
- improvement in 2020 and 2022; small deterioration in 2021.

The effect is **weak but consistent incremental state information**, not strong alpha. Event density itself is highly persistent, so the price-path increment is not simply mechanical reversion of the statistic.

R5 adjudication:

`docs/research/reversal_mean_reversion_R5_stage1_adjudication_20260908.md`

Promotion handoff:

`docs/ops/rmr_R5C_event_density_promotion_handoff_20260908.md`

## Two-promotion program review — completed

R1 and R5-C are the two progressed mechanisms. The required cross-lane review is complete:

`docs/research/reversal_mean_reversion_two_promotion_program_review_20260908.md`

Program priority:

1. **R1 = Priority A** — much larger held-forward effect and clearer structural interpretation;
2. **R5-C = Priority B** — larger sample supply and simpler scalar state, but much smaller incremental effect.

The broad repo remains a direction finder; neither specialist is authorized for prolonged optimization here.

## Current next action

The two-promotion review resets the broad discovery budget for **one new shallow results-blind lane definition**.

Next action order:

1. define and freeze one new shallow mechanism **before opening any new outcomes**;
2. prefer an unexplored multi-scale / frequency-band statistical-state mechanism rather than adding a fourth property post hoc to R5 v1;
3. keep 2023–2025 unopened while designing that lane;
4. do not promote a third mechanism without another explicit cross-lane review;
5. do not tune R2, rescue R3, or reopen V21 P2 under their closed identities.

A natural next definition candidate is a **frequency-band / multi-scale amplitude-state displacement** identity, but it must receive its own bounded preanalysis, exact causal measurement contract and tiny candidate budget before empirical screening.

## Authority order

For repository-wide direction and next action, read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_charter_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/research/reversal_mean_reversion_program_whitepaper_v1.md`
5. `AGENTS.md`
6. lane-specific protocols created after the authority reset
7. legacy overnight/gap-fill documents, authoritative only inside their historical identities

Production authority remains `false`.
