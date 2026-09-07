# Gap-Fill cross-index transport Audit B — cloud adjudication — 2026-09-07

## Decision

Research identity: `gap_fill_cross_index_transport_v1`.

Decision: **`CT_AUDIT_B_final_backward_external_not_confirmed`**.

The sealed `2013-01-01 .. 2014-10-16` Audit B is accepted as validly executed, but the preregistered final backward-historical robust-confirmation rule is **not** satisfied. All four T2 heads are sample-sufficient; three heads pass all six gates, while `CSI500 high` passes only 4/6 because the `>10bp` material-gap probability-quality conditions fail.

This is a scientific failure under the frozen gate, not an execution failure and not evidence insufficiency.

The already-sealed `2014-10-17 .. 2014-12-31` supporting crosscheck remains unopened and, by preregistration, **cannot replace or rescue Audit B**. CSI1000 `2026Q4` true-fresh evidence also remains sealed. Production authority remains false.

## Execution integrity

Audit-B execution-freeze / handoff point:

`09dc3677352d9def9e24371604d294a8b4b37a99`.

Local result commit:

`17ee944478188bf9a7834205d8cd44a8e7e10572`.

The result commit is exactly one commit after the frozen point and changes only:

- `docs/research/local_gap_fill_cross_index_transport_audit_b_receipt_v1.json`;
- `docs/governance/local_gap_fill_cross_index_transport_audit_b_data_usage_v1.json`.

No Audit-B protocol, evaluator, tests, external T2 parameter bundle, CSI1000 parameter artifact, feature set, model class, hyperparameter, threshold, calibration, horizon definition or gate changed after Audit-B outcomes were opened.

The receipt records:

- `T1_refit_performed=false`;
- `T2_refit_performed=false`;
- `scaler_refit_performed=false`;
- `feature_search_performed=false`;
- `model_class_search_performed=false`;
- `hyperparameter_search_performed=false`;
- `threshold_search_performed=false`;
- `probability_calibration_performed=false`;
- `supporting_crosscheck_opened=false`;
- `csi1000_post_2026_08_21_outcomes_opened=false`;
- `production_authority=false`.

## Source and target inventory

Source identity remains the HE-00 admitted raw canonical one-minute dataset:

`bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`

Dataset SHA256 identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`.

`2012-10-01 .. 2012-12-31` was loaded only as feature history for previous close / `rvol20`. Audit-B targets are strictly `2013-01-01 .. 2014-10-16`.

| index | Audit trading days | exact-240 days | target-valid rows | high | low |
|---|---:|---:|---:|---:|---:|
| CSI300 | 429 | 410 | 408 | 179 | 229 |
| CSI500 | 429 | 410 | 410 | 154 | 256 |

All four heads satisfy the frozen sample minimums. Per-head counts (`all / >10bp / >30bp`):

- CSI300 high: `179 / 126 / 51`;
- CSI300 low: `229 / 163 / 85`;
- CSI500 high: `154 / 71 / 14`;
- CSI500 low: `256 / 165 / 56`.

Missing one-minute clocks remain fail-closed. No missing minute was forward-filled or interpreted as a non-event.

## Gate result

Frozen T2 parameter identities remain:

- CSI300: `87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb`;
- CSI500: `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`.

Per-head Audit-B result:

| head | sample sufficient | gates passed | decision |
|---|---|---:|---|
| CSI300 high | yes | 6/6 | pass |
| CSI300 low | yes | 6/6 | pass |
| CSI500 high | yes | **4/6** | **fail** |
| CSI500 low | yes | 6/6 | pass |

Therefore `all_four_T2_heads_sample_sufficient=true`, but `all_four_T2_heads_pass_all_six_gates=false`.

## The precise failure: CSI500 high, material gaps >10bp

CSI500-high **all-gap** probability quality still beats the frozen DEV empirical benchmark:

- all-gap integrated Brier: model `0.2173971742` vs benchmark `0.2341294475`;
- all-gap integrated log-loss: model `0.6273291276` vs benchmark `0.6608214672`.

Its `>30bp` non-inferiority gate also passes, and monotonicity violations are zero.

The failure is concentrated in the preregistered `abs_gap > 10bp` cohort:

- `>10bp` integrated Brier: model `0.2483906346` vs benchmark `0.2481740400` — model is worse by about `0.0002166`;
- 15m Brier: model `0.2062714551` vs benchmark `0.2014065608` — worse;
- 60m Brier: model `0.2720094856` vs benchmark `0.2677073307` — worse;
- EOD Brier: model `0.2668909633` vs benchmark `0.2754082284` — better.

So only `1/3` `>10bp` horizons beat benchmark, whereas the frozen rule requires at least `2/3`. The two failed gates are exactly:

1. `gt10_integrated_brier_better=false`;
2. `gt10_at_least_2_of_3_horizon_brier_better=false`.

No post-hoc reweighting, alternative gap threshold, recalibration or exclusion of this head is allowed under this identity.

## Calendar interpretation

The CSI500-high failure is **not** a complete collapse of the architecture. The all-gap T2 score remains better than benchmark, and the failure is localized to material high gaps at the 15m/60m horizons. Descriptive calendar summaries also show that all-gap performance remains competitive across the Audit-B period.

The correct bounded interpretation is therefore:

> The geometry-hazard architecture has substantial cross-index transportability and passed the sealed 2011-2012 Audit A, but it did **not** achieve the preregistered stronger claim of robust final backward-historical confirmation across every index/sign/material-gap state through 2014-10-16. The specific unresolved state is CSI500 high-open material gaps, where short/medium-horizon fill probabilities no longer consistently improve on the fixed empirical benchmark.

This does not erase prior positive evidence. It does block the stronger `robustly_confirmed` label.

## Supporting crosscheck boundary

The `2014-10-17 .. 2014-12-31` supporting crosscheck remains sealed. The Audit-B protocol explicitly states that it may not substitute for or rescue a failed Audit B. Therefore this adjudication does **not** authorize opening it as a promotion rescue.

If that short post-launch block is ever opened, it must be under a separate descriptive-only protocol whose result cannot change the Audit-B decision.

## Scientific next step

Do **not** retune the current `gap_fill_cross_index_transport_v1` identity on consumed Audit-B outcomes.

The failure is useful for a successor research question: whether the material high-gap hazard requires a state/regime term that distinguishes periods in which short/medium-horizon gap absorption weakens. Any such work must use a **new V2.1 successor identity**, treat CT-DEV/Audit-A/Audit-B as consumed evidence, and reserve a new independent audit source/block.

The frozen CSI1000 V2-v1 prospective `2026Q4` true-fresh challenge remains scientifically independent and unopened.

Production authority remains false.
