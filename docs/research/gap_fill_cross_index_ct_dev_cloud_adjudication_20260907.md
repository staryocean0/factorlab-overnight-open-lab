# Gap-Fill cross-index transport CT-DEV — cloud adjudication — 2026-09-07

## Decision

Research identity: `gap_fill_cross_index_transport_v1`.

Decision: **`CT_DEV_cloud_review_passed_architecture_transport_supported`**.

CT-DEV is accepted as development evidence and is eligible to proceed to a separately frozen Audit A. Audit A remains unopened by this adjudication.

This decision does **not** select or modify CSI1000 V2 v1, does not create fresh-OOS authority, and does not authorize production.

## Execution integrity

Frozen execution point: `59d9c7b0b8975f5658ab1a6dbf51500a79b9701d`.

Local result commit: `1a4338ce05de90d64267770ded9db0d80203d0d0`.

The local-result commit is exactly one commit after the frozen point. Its changes are limited to:

- `docs/research/local_gap_fill_cross_index_transport_dev_receipt_v1.json`;
- `docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json`;
- `docs/governance/local_gap_fill_cross_index_transport_dev_data_usage_v1.json`;
- an append-only CT-DEV execution report in `docs/ops/cloud_local_communication.md`.

Frozen protocol / runner / tests / CSI1000 parameter artifact were not changed after outcomes were opened.

The execution report records:

- `validate_theme_package.py`: exit 0;
- full pytest: 72 passed;
- CT-DEV runner: exit 0;
- T1 refit: false;
- T2 refit only on external-index DEV: true;
- feature search: false;
- model-class search: false;
- hyperparameter search: false;
- threshold search: false;
- probability calibration: false;
- Audit A opened: false;
- Audit B opened: false;
- supporting crosscheck opened: false;
- CSI1000 post-2026-08-21 outcomes opened: false;
- raw rows written to repo: false;
- production authority: false.

## Source / target inventory

The source identity matches the HE-00 admitted raw canonical one-minute lake:

`bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`

HE-00 dataset SHA256 identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`.

The runner used the `instrument_type=market_index` parquet partition under the same admitted dataset because the dataset root also contains non-parquet metadata files. This is an execution-path adaptation only; the frozen runner itself was not changed.

Inventory accepted:

| index | trading days loaded | exact-240 days | target-valid geometry-complete | high | low |
|---|---:|---:|---:|---:|---:|
| CSI300 | 1396 | 1283 | 1113 | 543 | 570 |
| CSI500 | 967 | 911 | 799 | 388 | 411 |

These loaded-day and exact-240 counts match the HE-00 inventory exactly. Target-valid counts are smaller only because previous 15:00, positive complete `rvol20`, nonzero gap and the exact target contract are additionally required.

Invalid counts:

- CSI300: `not_exact_complete_240_clocks=113`, `incomplete_gap_or_rvol20=117`, `zero_gap=53`;
- CSI500: `not_exact_complete_240_clocks=56`, `incomplete_gap_or_rvol20=70`, `zero_gap=42`.

No missing minute was forward-filled or treated as a non-event.

## T1 — exact CSI1000 parameter transport

T1 is descriptive external parameter transport only. No T1 model was fitted and T1 does not control promotion.

The frozen CSI1000 parameters nevertheless retain substantial discrimination on both external indices. Pooled all-gap integrated metrics are:

| index | sign | n | integrated Brier | integrated log-loss | AUC 15m / 60m / EOD |
|---|---|---:|---:|---:|---|
| CSI300 | high | 543 | 0.175537 | 0.529540 | 0.823 / 0.810 / 0.716 |
| CSI300 | low | 570 | 0.188542 | 0.557380 | 0.759 / 0.758 / 0.696 |
| CSI500 | high | 388 | 0.175076 | 0.525833 | 0.824 / 0.797 / 0.749 |
| CSI500 | low | 411 | 0.167933 | 0.509032 | 0.800 / 0.770 / 0.730 |

The same qualitative discrimination remains visible in the >10bp and >30bp cohorts. T1 monotonicity violations are zero.

Interpretation: exact coefficients are not purely CSI1000-specific, but this is development evidence and not a promotion gate.

## T2 — architecture transport, expanding-year OOF

T2 is the primary CT-DEV scientific question: does the same two-feature, high/low, three-stage discrete-time hazard architecture retain probability skill when refitted separately on another index's own historical DEV data?

OOF inventory:

- CSI300: validation years 2007-2010, total OOF n=814;
- CSI500: validation years 2009-2010, total OOF n=354.

Benchmark: the empirical three-stage hazards estimated only from each expanding training fold, split by sign.

Across **all 12 pooled index × sign × cohort cells** (`all`, `>10bp`, `>30bp`), T2 integrated Brier is lower than the expanding-fold empirical benchmark.

| index | sign | cohort | n | T2 integrated Brier | benchmark | absolute improvement |
|---|---|---|---:|---:|---:|---:|
| CSI300 | high | all | 405 | 0.172946 | 0.236076 | 0.063130 |
| CSI300 | high | >10bp | 363 | 0.179080 | 0.240270 | 0.061190 |
| CSI300 | high | >30bp | 240 | 0.183047 | 0.264761 | 0.081713 |
| CSI300 | low | all | 409 | 0.202764 | 0.228569 | 0.025805 |
| CSI300 | low | >10bp | 350 | 0.212146 | 0.235612 | 0.023466 |
| CSI300 | low | >30bp | 283 | 0.223969 | 0.245655 | 0.021686 |
| CSI500 | high | all | 167 | 0.182081 | 0.235546 | 0.053465 |
| CSI500 | high | >10bp | 130 | 0.194518 | 0.239581 | 0.045062 |
| CSI500 | high | >30bp | 69 | 0.193739 | 0.255808 | 0.062069 |
| CSI500 | low | all | 187 | 0.162749 | 0.198962 | 0.036213 |
| CSI500 | low | >10bp | 140 | 0.172205 | 0.204638 | 0.032433 |
| CSI500 | low | >30bp | 89 | 0.206608 | 0.225257 | 0.018648 |

T2 and benchmark cumulative-probability monotonicity violations are zero.

Annual all-gap integrated Brier is better for T2 in every reported year × sign comparison except CSI300 2007 low, where T2 is worse by about 0.0260. This single development-year exception is retained as evidence and is not removed or reweighted.

## Frozen external parameter identities

The full-DEV fits are identity freezes for future Audit A only; they are not used to claim OOF ability.

- CSI300 T2 parameter bundle SHA256: `87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb`;
- CSI500 T2 parameter bundle SHA256: `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`.

Both use exactly `abs_gap` and `abs_gap_over_rvol20`, separate high/low heads and the three frozen hazard stages with StandardScaler + LogisticRegression(C=1, L2, lbfgs), with no calibration or binary threshold.

## Scientific adjudication

CT-DEV supports the following bounded statement:

> The relationship between opening-gap geometry (`abs_gap`, `abs_gap / rvol20`) and subsequent 15m/60m/EOD gap-fill hazard is not confined to CSI1000 development data. The same low-capacity hazard architecture shows broad expanding-year OOF probability skill on historical CSI300 and CSI500 development windows.

This is **development-level external mechanism evidence**, not independent sealed confirmation yet.

The exact CSI1000 coefficient transport also performs credibly, which strengthens the structural interpretation, but T1 is not used as a model-selection or promotion criterion.

## Next-stage authority

CT-DEV passes cloud review and may proceed to a separately frozen **Audit A (2011-01-01..2012-12-31)**.

Audit A must evaluate only the already-frozen CSI300 and CSI500 T2 parameter bundles. It must not refit, recalibrate, change features, change gap cohorts or open Audit B.

Audit A outcome is still unopened at the time of this adjudication.

Audit B (`2013-01-01..2014-10-16`), the 2014 post-launch supporting crosscheck and CSI1000 2026Q4 true-fresh evidence remain sealed.

Production authority remains false.
