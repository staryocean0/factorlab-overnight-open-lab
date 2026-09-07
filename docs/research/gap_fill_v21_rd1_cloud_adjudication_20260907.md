# Gap-Fill V2.1 RD1 regime diagnostic — cloud adjudication — 2026-09-07

## Decision

Research identity: `gap_fill_v2_1_regime_conditioned_successor`.

Decision: **`V21_RD1_cloud_review_passed_relative_gap_excess_only`**.

The local RD1 execution is accepted as valid. Exactly one of the five preregistered mechanism probes is admitted for later V2.1 family design:

- **admitted:** `P2_relative_gap_excess`;
- rejected: `P1_common_gap_support`;
- rejected: `P3_trend20_alignment`;
- rejected: `P4_prior_daytime_alignment`;
- rejected: `P5_relative_momentum5_alignment`.

This stage is mechanism diagnosis on already-consumed evidence only. No successor model was fitted or selected, no trading-return gate was used, and no V2.1 future outcome block was opened.

## Execution integrity

RD1 execution-freeze point:

`833db59ffd0334e6f7fcd49704e58983b5036344`.

Local result commit:

`01d5c02c5fd6e7b1fbd6dc066a1b52ca9fc23532`.

The result is exactly one commit after the frozen point and adds only:

- `docs/research/local_gap_fill_v21_regime_diagnostic_receipt_v1.json`;
- `docs/governance/local_gap_fill_v21_regime_diagnostic_data_usage_v1.json`.

No preregistered RD1 protocol, runner, tests, frozen external T2 parameter bundle or historical adjudication was changed after RD1 execution.

The data-usage receipt confirms:

- `supporting_crosscheck_2014Q4_opened=false`;
- `future_external_OHLC_read=false`;
- `future_external_gap_fill_or_model_scores_opened=false`;
- `future_external_metadata_only_scanned=true`;
- `CSI1000_post_2026_08_21_outcomes_opened=false`;
- raw rows were not written to the repository;
- production authority remains false.

The RD1 receipt additionally confirms:

- `V21_DEV_outcomes_opened=false`;
- `V21_AUDIT_A_outcomes_opened=false`;
- `V21_AUDIT_B_outcomes_opened=false`;
- `V21_EXTERNAL_RESERVE_outcomes_opened=false`;
- `successor_model_fit_performed=false`;
- `successor_model_selection_performed=false`;
- `trading_return_used=false`.

## Primary diagnostic inventory

The primary cell is CSI500 high gaps with `abs_gap > 10bp`:

- Audit A rows: 101;
- Audit B rows: 71;
- pooled consumed rows: 172.

The CSI300-high >10bp contrast has 256 pooled rows. All required diagnostic cells met the preregistered `n >= 20` rule and optimizer checks.

## Admitted mechanism: P2 relative gap excess

Frozen probe:

`sign(gap_i) * (gap_i - gap_j) / rvol20_i`

Expected beta sign: **positive**.

Interpretation: conditional on the observed target-index high gap, a larger target-specific gap excess over the other broad index is more consistent with relative opening overshoot and therefore should raise subsequent fill probability.

### CSI500-high >10bp primary cell

Pooled 2011-01-01 .. 2014-10-16:

- 15m: beta `+0.1848077840`, log-loss `0.5277820626 -> 0.5249036710`;
- 60m: beta `+0.3904606158`, log-loss `0.7007167976 -> 0.6858991675`.

Audit A 2011-2012:

- 15m: beta `+0.1766630010`, log-loss `0.4718999274 -> 0.4698166603`;
- 60m: beta `+0.5719112979`, log-loss `0.6700222373 -> 0.6416490467`.

Audit B 2013-01-01 .. 2014-10-16:

- 15m: beta `+0.1992664773`, log-loss `0.6072763675 -> 0.6031340918`;
- 60m: beta `+0.1774676763`, log-loss `0.7443808903 -> 0.7409019379`.

Thus P2 has the expected sign in both pooled primary horizons, both Audit-B primary horizons, and both Audit-A primary horizons; it improves pooled log-loss at both horizons and Audit-B log-loss at both horizons.

CSI300-high >10bp contrast does not invalidate the mechanism: pooled contrast beta is `+0.1080926178` at 15m and `-0.0561085187` at 60m, so there is no two-horizon contradiction under the frozen contrast rule.

All seven implementation/admission checks reported by the runner are true. Therefore P2 is admitted for **family design only**, not as a fitted successor coefficient.

## Rejected mechanisms

### P1 common gap support

Expected beta was negative, but the pooled CSI500-primary betas were positive (`+0.5721690886` at 15m and `+0.3097015802` at 60m). Audit A also strongly pointed positive, and the CSI300 contrast was positive at both horizons. P1 therefore fails the preregistered directional mechanism claim despite improving log-loss in several consumed cells.

### P3 trend20 alignment

Expected beta was negative, but pooled primary beta is positive at both horizons (`+0.2173197050`, `+0.0913814208`) and Audit-B primary beta is also positive at both horizons. The probe may describe a consumed-period association, but it contradicts the preregistered continuation-support sign and is rejected for family design.

### P4 prior-daytime alignment

Expected beta was negative. Pooled primary sign is mixed: 15m beta is positive (`+0.0779843963`) while 60m beta is negative (`-0.2796812257`). It therefore fails the required pooled expected-sign-both-horizons rule.

### P5 relative momentum5 alignment

Expected beta was negative. Pooled primary sign is again mixed: 15m beta is positive (`+0.0206860745`) while 60m beta is negative (`-0.3935959263`). It therefore fails the required pooled expected-sign-both-horizons rule.

## Scientific interpretation

RD1 narrows the Audit-B failure mechanism substantially.

The supported state is not a generic slow trend or prior-day continuation variable. The surviving signal is **relative cross-index opening dislocation**:

> for a CSI500 high opening, the part of the gap that is unusually large relative to the contemporaneous CSI300 opening gap is more fill-prone at 15m/60m than the frozen geometry-only model implies.

This is economically coherent with a decomposition of the observed opening gap into:

1. common-information repricing shared across broad indices; and
2. target-specific relative overshoot/dislocation.

Only the second component is supported by the preregistered RD1 evidence strongly enough to enter V2.1 family design.

This does **not** authorize simply taking the RD1 beta and attaching it to the old model. The successor must be developed under a new V2.1 identity on a new development block.

## Future external-data inventory and new blocker

The future partitions were frozen before outcome access:

- V21_DEV: 2015-01-01 .. 2018-12-31;
- V21_AUDIT_A: 2019-01-01 .. 2021-12-31;
- V21_AUDIT_B: 2022-01-01 .. 2024-12-31;
- V21_EXTERNAL_RESERVE: 2025-01-01 .. 2026-08-21.

RD1 inspected only `symbol`, `trading_day`, and `timestamp` in these future blocks. No OHLC, gap, fill target or model score was opened.

The metadata inventory reveals a material source-contract problem in the current raw canonical lake for **both CSI300 and CSI500**:

| partition | observed trading days | exact-240 days |
|---|---:|---:|
| V21_DEV 2015-2018 | 975 | 861 |
| V21_AUDIT_A 2019-2021 | 730 | **0** |
| V21_AUDIT_B 2022-2024 | 726 | **0** |
| V21_EXTERNAL_RESERVE 2025-2026-08-21 | 397 | **0** |

This is not an outcome failure; it is a source-admission / bar-support problem discovered from metadata only.

Under the existing exact-240 fail-closed target rule, the currently inventoried raw canonical source cannot supply any valid Audit-A or Audit-B day in the frozen 2019-2024 partitions. Therefore **V21_DEV outcomes must remain unopened until the future audit source contract is remediated**.

The next stage is source admission/remediation only. It must seek an authoritative or provenance-rich minute source/reconstruction that can support the frozen future partitions without using outcome information to choose the source or dates. The remedy may not silently forward-fill missing minutes or relax target validity after seeing V2.1 results.

## Next-stage authority

Authorized scientific conclusion:

`P2_relative_gap_excess` may be the sole RD1-derived state variable admitted into a later bounded V2.1 successor family.

Not yet authorized:

- opening V21_DEV outcomes;
- fitting/selecting a V2.1 successor;
- changing future partition dates;
- opening 2014Q4 supporting crosscheck;
- relaxing exact-240 target validity based on the inventory;
- using CSI1000 post-2026-08-21 outcomes.

Next action: **V21 future-audit source-admission remediation using metadata/provenance only.**

Production authority remains false.
