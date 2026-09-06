# CT-DEV — Gap-Fill cross-index transport local execution handoff

## Status

Cloud HE-00 source review is complete and CT-DEV is preregistered, statically tested and execution-frozen. The local Unified DataHub raw canonical lake is required for actual execution.

Research identity:

`gap_fill_cross_index_transport_v1`

Execution freeze:

`docs/governance/cloud_session_20260906_gap_fill_cross_index_ct_dev_execution_freeze_v1.json`

Protocol:

`docs/governance/cloud_session_20260906_gap_fill_cross_index_transport_protocol_v1.json`

Runner:

`scripts/run_gap_fill_cross_index_transport_dev.py`

## Authorized data open

Only these external-index development windows may be opened:

- CSI300 / `000300.SH`: `2005-04-08 .. 2010-12-31`;
- CSI500 / `000905.SH`: `2007-01-15 .. 2010-12-31`.

Do **not** open:

- CSI300/CSI500 `2011-01-01 .. 2012-12-31` Audit A;
- CSI300/CSI500 `2013-01-01 .. 2014-10-16` Audit B;
- CSI300/CSI500 `2014-10-17 .. 2014-12-31` supporting crosscheck;
- any CSI1000 post-2026-08-21 outcome or V2 score.

## Frozen source

Use the HE-00 admitted raw canonical one-minute lake, not the densified FactorLab export:

`/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`

HE-00 dataset SHA256 identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

The runner also verifies the admitted dataset-version identity in the path.

## Frozen mathematical work

### T1 exact parameter transport

Apply CSI1000 V2 v1 parameter bundle unchanged to CSI300 and CSI500. No T1 fit.

### T2 architecture transport

For each external index independently:

- same two features: `abs_gap`, `abs_gap_over_rvol20`;
- same high/low split;
- same three discrete-time hazard stages;
- same StandardScaler + LogisticRegression(C=1, L2, lbfgs);
- expanding natural-year OOF inside DEV;
- one final full-DEV index-specific fit solely to freeze the future Audit-A identity.

No model class/C/feature/threshold/calibration/horizon search is allowed.

## Target-row fail-closed rule

The first transport generation uses only target days with all exact official 240 one-minute clocks. Missing `14:59` or any other minute invalidates that target day for all three horizons. No forward fill and no missing-minute-as-non-event inference.

Previous session 15:00 close and positive complete `rvol20` are also required.

## Commands

From the current repository root at the execution-freeze commit or a descendant that has not modified the frozen protocol/runner/tests/CSI1000 parameter artifact:

```bash
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE='/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824'

python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/run_gap_fill_cross_index_transport_dev.py
```

Do not run any Audit-A/B evaluator after CT-DEV. None is authorized yet.

## Expected outputs

Commit only the three aggregate outputs:

- `docs/research/local_gap_fill_cross_index_transport_dev_receipt_v1.json`
- `docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json`
- `docs/governance/local_gap_fill_cross_index_transport_dev_data_usage_v1.json`

Do not commit raw historical index minutes or daily/row-level predictions.

## Return to cloud

Report/commit:

1. execution commit SHA;
2. validator exit code;
3. pytest exit code and passed count;
4. runner exit code;
5. source path used;
6. CSI300/CSI500 loaded trading-day counts, exact-240 counts and final target-valid counts;
7. T1 high/low all/>10bp/>30bp integrated Brier/log-loss and AUC/PR-AUC summary;
8. T2 expanding-OOF model versus training-fold empirical benchmark for the same cohorts;
9. annual T2/benchmark summaries;
10. final CSI300 and CSI500 T2 parameter-bundle SHA256 values;
11. confirmation `audit_a_opened=false`, `audit_b_opened=false`, `supporting_crosscheck_opened=false`, `csi1000_post_2026_08_21_outcomes_opened=false`;
12. confirmation no feature/model/hyperparameter/threshold/calibration search occurred.

Cloud will independently review CT-DEV before deciding whether to open Audit A and before using cross-index DEV as V2.1 mechanism-development evidence.
