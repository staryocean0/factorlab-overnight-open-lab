# Gap-Fill cross-index transport Audit A — cloud adjudication — 2026-09-07

## Decision

Research identity: `gap_fill_cross_index_transport_v1`.

Decision: **`CT_AUDIT_A_cloud_review_passed_all_four_heads_Audit_B_eligible`**.

The sealed 2011-01-01 .. 2012-12-31 Audit A is accepted. All four preregistered T2 heads (CSI300 high/low, CSI500 high/low) are sample-sufficient and pass all six preregistered probability-quality gates. Under the frozen rule, Audit B is eligible to be opened only after a separately frozen Audit-B execution protocol. Audit B remains unopened by this adjudication.

This is sealed backward historical external validation. It is not CSI1000 prospective fresh evidence and does not grant production authority.

## Execution integrity

Audit-A execution freeze / handoff point:

`54307bee2b864f666c3facbd033e336e03a1d0a9`.

Local result commit:

`74798483716040e7d8949ec7381d4f90dcac3430`.

The local result is exactly one commit after the frozen point. The commit changes only:

- `docs/research/local_gap_fill_cross_index_transport_audit_a_receipt_v1.json`;
- `docs/governance/local_gap_fill_cross_index_transport_audit_a_data_usage_v1.json`.

No Audit-A protocol, evaluator, tests, CSI300/CSI500 T2 parameter bundle, CSI1000 V2-v1 parameter artifact, feature set, model class, hyperparameter, threshold, calibration or horizon definition changed after Audit-A outcomes were opened.

The receipt records:

- `T1_refit_performed=false`;
- `T2_refit_performed=false`;
- `scaler_refit_performed=false`;
- `feature_search_performed=false`;
- `model_class_search_performed=false`;
- `hyperparameter_search_performed=false`;
- `threshold_search_performed=false`;
- `probability_calibration_performed=false`;
- `audit_b_opened=false`;
- `supporting_crosscheck_opened=false`;
- `csi1000_post_2026_08_21_outcomes_opened=false`;
- `production_authority=false`.

## Source and target inventory

Source identity remains the HE-00 admitted raw canonical one-minute dataset:

`bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`

Dataset SHA256 identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`.

The evaluator loaded 2010-10-01 .. 2010-12-31 only as feature history for previous close / rvol20. Audit targets are strictly 2011-01-01 .. 2012-12-31.

| index | Audit trading days | exact-240 days | target-valid rows | high | low | >10bp | >30bp |
|---|---:|---:|---:|---:|---:|---:|---:|
| CSI300 | 487 | 480 | 457 | 188 | 269 | 350 | 179 |
| CSI500 | 487 | 480 | 458 | 137 | 321 | 341 | 156 |

Per-head cohort counts are all above the frozen sufficiency minimums (25 all, 20 >10bp, 12 >30bp):

- CSI300 high: 188 / 130 / 62;
- CSI300 low: 269 / 220 / 117;
- CSI500 high: 137 / 101 / 40;
- CSI500 low: 321 / 240 / 116.

Missing one-minute clocks remain fail-closed. No missing minute was forward-filled or interpreted as a non-event.

## T2 primary Audit-A result

T2 uses the frozen index-specific full-DEV parameter bundles without refit:

- CSI300: `87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb`;
- CSI500: `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`.

The fixed comparator is each index/sign full-DEV empirical three-stage hazard benchmark stored before Audit A. It is not re-estimated on Audit A.

### Pooled all-gap probability quality

| index | sign | n | frozen benchmark Brier | T2 Brier | relative Brier reduction | benchmark log-loss | T2 log-loss |
|---|---|---:|---:|---:|---:|---:|---:|
| CSI300 | high | 188 | 0.217235 | 0.163059 | 24.9% | 0.625203 | 0.495904 |
| CSI300 | low | 269 | 0.228606 | 0.176159 | 22.9% | 0.649399 | 0.527503 |
| CSI500 | high | 137 | 0.221456 | 0.191997 | 13.3% | 0.634443 | 0.565987 |
| CSI500 | low | 321 | 0.228724 | 0.195837 | 14.4% | 0.650592 | 0.573876 |

### Material-gap robustness

Integrated Brier, model versus fixed benchmark:

| index | sign | >10bp model / benchmark | >30bp model / benchmark |
|---|---|---:|---:|
| CSI300 | high | 0.174489 / 0.222367 | 0.154490 / 0.248994 |
| CSI300 | low | 0.191547 / 0.237343 | 0.190896 / 0.260603 |
| CSI500 | high | 0.200806 / 0.222588 | 0.163826 / 0.237551 |
| CSI500 | low | 0.226122 / 0.250898 | 0.251491 / 0.298390 |

For every index/sign head:

1. all-gap integrated Brier is strictly better;
2. all-gap integrated log-loss is strictly better;
3. >10bp integrated Brier is strictly better;
4. >30bp integrated Brier is not worse (in fact strictly better for all four heads);
5. >10bp at least two of three horizon Brier scores are strictly better;
6. monotonicity violations equal zero.

Therefore every head passes 6/6 gates.

## Annual robustness

All-gap integrated Brier, model versus benchmark:

- CSI300 high 2011: 0.144106 vs 0.219376;
- CSI300 high 2012: 0.182835 vs 0.215001;
- CSI300 low 2011: 0.176635 vs 0.229411;
- CSI300 low 2012: 0.175765 vs 0.227938;
- CSI500 high 2011: 0.163886 vs 0.222272;
- CSI500 high 2012: 0.224061 vs 0.220525 (model worse by about 0.00354);
- CSI500 low 2011: 0.207491 vs 0.246301;
- CSI500 low 2012: 0.186235 vs 0.214243.

Thus 7 of 8 index × sign × year comparisons improve. The CSI500-high 2012 exception is retained and is not reweighted or removed. Annual performance was descriptive, not an Audit-A gate.

## T1 descriptive transport

The frozen CSI1000 V2-v1 exact parameter bundle is also reported on Audit A, with no refit. T1 remains descriptive and cannot rescue any T2 gate. The Audit-A promotion decision is based only on the preregistered T2 gate.

## Scientific interpretation

Audit A materially upgrades the cross-index evidence:

> The low-capacity relationship between opening-gap geometry (`abs_gap`, `abs_gap / rvol20`) and 15m/60m/EOD fill hazard survives a sealed later historical block on both CSI300 and CSI500, for both high and low gaps, including >10bp and >30bp cohorts.

This is no longer only a development-window cross-index observation. It is now sealed backward-historical external confirmation of the architecture on 2011-2012.

The correct bounded claim remains structural: it supports transportability of the geometry-hazard architecture. It does not prove that one universal coefficient vector is optimal across indices, does not make the result CSI1000 prospective fresh evidence, and does not authorize trading/production.

## Next-stage authority

The frozen Audit-A rule requires all four heads to be sample-sufficient and pass all six gates. That condition is satisfied.

Therefore **Audit B (2013-01-01 .. 2014-10-16) is eligible for a separate preregistered/frozen execution**.

Audit B remains unopened at the time of this adjudication. The 2014-10-17 .. 2014-12-31 supporting crosscheck and CSI1000 2026Q4 true-fresh block also remain sealed.

Production authority remains false.
