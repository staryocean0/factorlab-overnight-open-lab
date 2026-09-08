# R7 Stage-1 cloud adjudication — 2026-09-08

Research identity: `R7_directional_path_energy_asymmetry_stage1_v1`

Decision:

`R7_STAGE1_closed_cross_scale_gate_failed`

## Execution integrity

R7 executed successfully in GitHub Actions run `34185879687` at head `4ed5e2ee7f10617f77411606729969c1067f2817`.

All steps passed:

- synthetic/boundary tests;
- frozen runner;
- reserve/2026/no-auto-promotion checks;
- aggregate artifact upload.

Cloud compact receipt:

`docs/research/cloud_session_20260908_rmr_R7_stage1_action_receipt_v1.json`

Only CSI1000 rows through `2022-12-30` were read. The 2023–2025 reserve and all 2026 rows remained unopened.

## S1 result

At the fine event scale, directional energy asymmetry is genuinely incremental under the frozen screen:

- stability resolved events: `2,329`;
- severity-only Brier `0.25015489`;
- severity + directional-energy-z Brier `0.24992418`;
- Brier improvement `0.00023071`;
- log-loss improvement `0.00046197`;
- annual Brier improves in **2020, 2021 and 2022**.

Therefore the S1 local gate passes.

## S2 result

At the coarser event scale the same score reverses sign and harms prediction quality:

- stability resolved events: `831`;
- severity-only Brier `0.24906358`;
- augmented Brier `0.24936610`;
- augmented-minus-baseline Brier `+0.00030252` — worse;
- log-loss delta `+0.00060704` — worse;
- annual Brier worsens in 2020 and 2022 and improves only in 2021.

Therefore the S2 local gate fails.

The preregistered R7 gate required the **same single score** to pass at both S1 and S2. S1 cannot rescue S2.

## Statistical-state versus price-path distinction

The directional-energy score itself shows striking next-observation reversal/normalization behavior:

- S1 current/next z correlation `-0.9098`; abs-z contraction share `0.7038`;
- S2 correlation `-0.6932`; contraction share `0.7745`.

Yet only S1 translates that state behavior into improved reversal/extension probability quality; S2 does not.

This reinforces a program-level finding already seen in R5-A and R6:

> **A market statistic can strongly revert toward its own normal state without implying that the price path has a robust mean-reversion advantage.**

That distinction should remain explicit in future research.

## Overall decision

`candidate_for_program_review = false`

R7 Stage-1 v1 is closed.

Do not rescue R7 by:

- switching squared returns to absolute returns;
- changing the 240-bar window;
- adding semivariance ratios/skewness/jump counts;
- selecting only S1;
- splitting up/down waves;
- opening 2023–2025;
- tuning a z-score threshold.

A materially different asymmetry mechanism would require a new future identity, but the broad program should first review whether further shallow indicator-like lanes are scientifically justified at all.

Production authority remains `false`.
