# Gap-Fill V2.1 P2 overlay family preanalysis — 2026-09-07

## Status

Research identity: `gap_fill_v2_1_regime_conditioned_successor`.

This document is a **preanalysis / design precommitment only**. It does not authorize V21_DEV outcome access or model fitting. Formal family freeze remains contingent on cloud verification of the future-audit source-admission receipt/package identity under `session_complete_239_required_v1`.

The source-admission state at writing is still `gate_remediated_pending_identity_verification`; V21_DEV, V21_AUDIT_A, V21_AUDIT_B, V21_EXTERNAL_RESERVE, the 2014Q4 supporting crosscheck, and CSI1000 2026Q4 remain sealed.

## Research question

Audit B did not reject the geometry-hazard architecture globally. The failure was localized to `CSI500 high × abs_gap > 10bp × 15m/60m`: all-gap performance remained better than the frozen empirical benchmark, but the material high-gap short/medium horizons lost incremental probability skill.

RD1 then admitted exactly one state variable for family design:

`P2_relative_gap_excess = sign(gap_i) * (gap_i - gap_j) / rvol20_i`

For the primary external mechanism test, `i = CSI500`, `j = CSI300`. P2 had the preregistered positive sign and improved log-loss at 15m and 60m in pooled consumed evidence, Audit A, and Audit B. P1/P3/P4/P5 were rejected and must not re-enter this family.

The bounded successor question is therefore:

> Conditional on a material CSI500 high opening gap, does the target-specific component of that gap relative to CSI300 provide stable incremental information about 15m/60m fill hazards beyond the already-frozen geometry model?

This is deliberately narrower than “build a better gap-fill model”.

## Economic interpretation

The observed opening gap can be decomposed conceptually into:

1. a common-information repricing component shared by broad indices; and
2. a target-specific relative dislocation / overshoot component.

P2 is a low-dimensional proxy for component (2). A positive P2 means that, after orienting by the target gap sign, the target index has moved farther than the broad-index contrast relative to the target's recent daily volatility. RD1 says that this residual relative opening displacement is more fill-prone in the localized failure state.

This interpretation is consistent with several strands of market-microstructure evidence:

- Zhang, Zhang & Xue, *Applied Economics* (2025), “Overnight return reversal in the Chinese stock market”, DOI `10.1080/00036846.2024.2387365`: Chinese overnight returns predict first-half-hour reversals and the authors link the effect to the pre-open auction mechanism and T+1 trading rule.
- Chu, Goodell & Li, *Pacific-Basin Finance Journal* (2024), “Are pre-opening periods important? Evidence from Chinese market lunch breaks”: Chinese morning call-auction opening prices are more informative and adjust more rapidly to overnight information than continuous-auction afternoon reopenings.
- Qiao & Dam, *Journal of Financial Markets* (2020), “The overnight return puzzle and the T+1 trading rule in Chinese stock markets”: the T+1 rule creates a systematic opening-price effect and contributes to overnight risk.
- Da, Liu & Schaumburg, *Management Science* (2014), “A Closer Look at the Short-Term Return Reversal” / FRBNY Staff Report 513: decomposing recent returns shows that reversal is concentrated in the residual component after removing common/industry and fundamental-news components.
- Lou, Polk & Skouras, *Journal of Financial Economics* (2019), “A tug of war: Overnight versus intraday expected returns”: overnight and intraday clienteles can create temporary price pressure that reverses across trading periods.

These references motivate the decomposition; they do not determine any coefficient, threshold, or performance gate in this project.

## Why the successor is an overlay, not a full refit

Only one new mechanism survived RD1. Re-estimating the entire geometry model with P2 as an ordinary third feature would unnecessarily reopen already-supported geometry coefficients and allow P2 to proxy for general calibration drift.

The preferred successor is therefore a **two-parameter hazard-level residual overlay on a frozen base**.

Frozen base for the external mechanism program:

- CSI500 T2 parameter bundle SHA256: `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`;
- geometry features remain exactly `abs_gap`, `abs_gap_over_rvol20`;
- no geometry coefficient, scaler, intercept, low-gap head, or EOD-stage coefficient is re-estimated by this successor.

For a CSI500 high gap with `abs_gap > 0.001`, define raw state:

`z_raw = (gap_500 - gap_300) / rvol20_500`

(the high-gap sign is positive, so this is the frozen P2 formula in the primary cell).

On each training fold, fit one scalar standardization on the eligible high-gap rows:

`z = (z_raw - mean_train) / std_train`

Then modify only the frozen CSI500 high stage hazards:

`logit(h15_v21) = logit(h15_base) + beta15 * z`

`logit(h60_v21) = logit(h60_base) + beta60 * z`

with `h60` fitted/evaluated only on the stage-60 risk set (`fill15 = 0`).

Cumulative probabilities are:

`p15_v21 = h15_v21`

`p60_v21 = 1 - (1 - h15_v21) * (1 - h60_v21)`

This preserves `0 <= p15 <= p60 <= 1` by construction.

Outside `CSI500 high && abs_gap > 10bp`, V2.1 makes **no successor claim** and the frozen base remains the reference.

## Horizon scope

V2.1 family promotion is intentionally restricted to `fill15` and `fill60`.

Reason 1: the Audit-B failure and the admitted RD1 mechanism are specifically short/medium horizon phenomena.

Reason 2: the prospective future source contract `session_complete_239_required_v1` makes `14:59` structurally optional while requiring every other legacy target-session clock. This does not affect 09:31–09:45 or 09:31–10:30, but it can make an EOD label ambiguous on the rare path where the previous close is touched only during 14:59. Therefore EOD must not be a V2.1 promotion gate under this source contract.

This does not rewrite or weaken V2 v1's existing 15m/60m/EOD evidence. It defines the scope of a new successor component.

## Frozen future partitions

No dates move:

- V21_DEV: `2015-01-01 .. 2018-12-31`;
- V21_AUDIT_A: `2019-01-01 .. 2021-12-31`;
- V21_AUDIT_B: `2022-01-01 .. 2024-12-31`;
- V21_EXTERNAL_RESERVE: `2025-01-01 .. 2026-08-21`.

The 2014Q4 supporting crosscheck remains outside this successor path and cannot be used as rescue evidence.

## Planned V21_DEV estimation and OOF design

Formal execution remains blocked until source identity verification and V21_DEV metadata reinventory under the named-clock 239 gate.

Once authorized, the proposed development evaluation is expanding-year OOF with exactly two validation folds:

1. train `2015-01-01 .. 2016-12-31`, validate calendar year 2017;
2. train `2015-01-01 .. 2017-12-31`, validate calendar year 2018.

No 2019+ row may be loaded by the DEV selector.

For each fold:

- the frozen geometry base remains unchanged;
- fit only `z` mean/std on eligible training rows;
- fit only `beta15` and `beta60` by minimizing stage-specific binary log-loss with a frozen base-logit offset;
- no intercept shift;
- no probability calibration;
- no alternative optimizer/model/feature/horizon/threshold;
- no low-gap fit;
- no EOD fit.

After OOF adjudication, if the successor passes the frozen DEV gate, fit one final `(z_mean, z_std, beta15, beta60)` bundle on full V21_DEV and freeze it before Audit A.

## Proposed DEV promotion gate

The primary cell is fixed: `CSI500 high && abs_gap > 10bp`.

The candidate is compared directly with the same frozen geometry base on identical validation rows.

All conditions are intended to be required:

1. pooled 2017–2018 equal-weight integrated Brier across 15m/60m is strictly lower than base;
2. pooled 2017–2018 equal-weight integrated log-loss across 15m/60m is strictly lower than base;
3. 15m Brier is strictly lower than base;
4. 60m Brier is strictly lower than base;
5. both OOF-fold fitted `beta15` values are positive and both OOF-fold fitted `beta60` values are positive;
6. calendar-year integrated Brier is lower than base in both 2017 and 2018;
7. monotonicity violations (`p15 > p60`) equal zero.

Sample sufficiency is fail-closed. The formal family freeze should set a minimum eligible target-cell count before opening V21_DEV; if insufficient, the calendar window is not extended and the 10bp threshold is not relaxed.

These are proposed gates only until the formal post-source-verification family freeze binds them.

## Planned Audit A / Audit B role

If DEV promotes the overlay, the full-DEV overlay bundle is frozen and applied unchanged to:

- Audit A 2019–2021;
- then, only if Audit A passes, Audit B 2022–2024.

The benchmark remains the same frozen geometry base, not a re-estimated empirical benchmark and not an Audit-specific refit.

The primary audit claim remains incremental correction of the localized material-high-gap 15m/60m state. No audit outcome may change `z`, the 10bp scope, betas, base geometry, horizons, or gates.

The external reserve 2025–2026-08-21 stays sealed until both historical audits are adjudicated.

## CSI300 role

CSI300 is required contemporaneously to construct P2 for CSI500. Under this first successor family it is an **anchor / contrast market**, not a second fitted successor target.

This choice is deliberate: RD1 admitted P2 in the CSI500 primary cell, while the CSI300 contrast was required only not to contradict the mechanism at both horizons. The design therefore does not generalize the overlay to CSI300 before new development evidence.

## Path to CSI1000

No CSI1000 V2.1 parameter or feature is selected here.

If the CSI500 P2 overlay survives DEV, Audit A, Audit B, and any separately authorized external-reserve test, cloud may create a new transfer protocol asking whether the same *architecture* (target gap relative to a broad-index anchor) should be fitted for CSI1000.

A CSI500 beta must never be silently copied to CSI1000. Any CSI1000 successor requires a new parameter identity and a preregistered evaluation plan. CSI1000 2026Q4 true-fresh evidence remains sealed and independent.

## Explicitly rejected alternatives

This family must not include, unless a later new research identity is created:

- P1 common-gap support;
- P3 trend20 alignment;
- P4 prior-daytime alignment;
- P5 relative-momentum5 alignment;
- P2 interactions with gap size or volatility;
- a searched gap threshold other than the already-frozen 10bp material-gap state;
- a full three-feature geometry refit;
- intercept recalibration;
- EOD-state fitting;
- model-class or hyperparameter search;
- trading-return gates.

## Next action while source package remains unverified

Research may continue on static specification, tests, and execution scaffolding, but no V21_DEV outcome may be opened.

Before formal family freeze / DEV authorization, cloud must still:

1. verify the local future-audit source-admission receipt or package identity using metadata only;
2. reproduce required-239 coverage/provenance;
3. re-inventory V21_DEV under the same named-clock gate without reading outcomes;
4. bind the final family protocol, selector blob, tests, and source identities.

Production authority remains false.
