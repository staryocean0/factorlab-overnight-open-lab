# R5 Stage-1 cloud adjudication — 2026-09-08

Research identity: `R5_statistical_state_extremes_stage1_v1`

Decision:

`R5_STAGE1_progress_event_density_only_close_path_efficiency_and_volatility_displacement`

## Execution integrity

The frozen R5 Stage-1 screen executed in GitHub Actions run `34184683011` at head `b6ef18c31ceb89dbbcf69961c252ec6af9e1ce80`.

All execution steps passed:

- R5 synthetic/boundary tests;
- frozen runner execution;
- exact candidate/scale budget verification;
- reserve and 2026 boundary verification;
- aggregate artifact upload.

The action artifact is `rmr-r5-stage1-receipts`, artifact id `10040095965`, digest `sha256:fd35494c51429da4b63ad105221a6b0c893d7cb9a259983d314a601f8aabed0d`.

The compact cloud receipt is:

`docs/research/cloud_session_20260908_rmr_R5_stage1_action_receipt_v1.json`

## Data boundary

The screen loaded CSI1000 1m rows only through `2022-12-30`:

- source rows loaded: `466,961`;
- DEV: 2015–2019;
- chronological stability: 2020–2022, explicitly not fresh;
- 2023–2025 internal reserve: unopened;
- all 2026 rows: unopened.

No scale/window/threshold/interaction/model search, calibration, trading-return selection or deep/frequency model was used.

## R5-A — path efficiency

### Statistical property itself

Path efficiency clearly tends to move back toward its own rolling normal region:

- S1: `share(|z_next| < |z_current|) = 0.8891`;
- S2: `0.8353`.

So the statistic itself is mean-reverting in this descriptive sense.

### Price-path information

That reversion does **not** translate into stable incremental information about subsequent price reversal versus extension.

- S1 pooled augmented-minus-baseline Brier: `-0.0000308` — essentially flat/slightly better;
- S1 annual Brier improves in 2021/2022 but is slightly worse in 2020;
- S2 pooled Brier: `+0.0000076` — slightly worse;
- S2 annual Brier improves only in 2020 and worsens in 2021/2022.

Decision:

`close_property_under_R5_stage1_v1`

Reason: strong reversion of the statistic itself is insufficient under the preregistered contract because cross-scale price-path incremental information is not stable.

## R5-B — volatility-state displacement

### Statistical property itself

The volatility ratio also shows own-state reversion:

- S1: `share(|z_next| < |z_current|) = 0.6382`;
- S2: `0.8086`.

### Price-path information

The price-path relation is scale-dependent rather than stable:

- S1 pooled Brier worsens by `+0.0008431`, and worsens in all three stability years;
- S2 pooled Brier improves by `-0.0003051`, improves in 2020/2021, then reverses sign in 2022.

Decision:

`close_property_under_R5_stage1_v1`

Reason: no consistent cross-scale incremental relation beyond severity. Do not rescue by changing volatility windows or adding clustering filters.

## R5-C — event density

R5-C is qualitatively different from A/B.

### Property persistence/reversion

Event density is highly persistent rather than mechanically strongly mean-reverting:

- S1 current/next z correlation: `0.9383`; `share(|z_next| < |z_current|) = 0.5079`;
- S2 correlation: `0.8669`; share = `0.5246`.

This matters because its price-path improvement cannot be dismissed as merely the statistic mechanically snapping back to its median.

### Incremental price-path information

**S1**

- stability resolved events: `2,329`;
- baseline Brier `0.2501610` → augmented `0.2494158`;
- delta `-0.0007452`;
- log-loss delta `-0.0015003`;
- Brier improves in all three years: 2020, 2021, 2022.

**S2**

- stability resolved events: `831`;
- baseline Brier `0.2489933` → augmented `0.2489006`;
- delta `-0.00009275`;
- log-loss delta `-0.0001870`;
- annual Brier improves in 2020 and 2022, with a small deterioration in 2021.

This satisfies the Stage-1 progression logic:

- event supply is nontrivial;
- pooled improvement is in the same direction at both predeclared scales;
- annual direction is stable in 5 of 6 scale×year cells;
- no threshold or scale was selected from results;
- the effect is not explained by strong mechanical own-property mean reversion.

However, the incremental effect size is small, especially at S2. The correct claim is therefore:

`weak_but_consistent_incremental_state_information`

—not strong alpha, not production readiness, and not evidence for a trading rule.

Decision:

`progress_property`

R5-C is the **only** R5 property allowed to progress from Stage-1 v1.

## Overall R5 decision

Exactly one property progresses, respecting the frozen maximum of one:

- R5-A path efficiency: **close**;
- R5-B volatility displacement: **close**;
- R5-C event density: **progress**.

The 2023–2025 reserve remains unopened. It may not be used to redesign the event-density identity.

A dedicated successor must freeze its representation, baseline, candidate budget, gates and reserve usage before any 2023–2025 outcome is opened.

Production authority remains `false`.
