# CT-AUDIT-B — Gap-Fill cross-index final backward-historical confirmation handoff

## Status

Cloud Audit-A review passed. Audit B is now preregistered, statically tested and execution-frozen. The local Unified DataHub raw canonical one-minute lake is required for actual execution.

Research identity:

`gap_fill_cross_index_transport_v1`

Audit-B protocol:

`docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_b_protocol_v1.json`

Execution freeze:

`docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_b_execution_freeze_v1.json`

Evaluator:

`scripts/evaluate_gap_fill_cross_index_audit_b.py`

## Authorized open

Only these target windows may be opened:

- CSI300 / `000300.SH`: `2013-01-01 .. 2014-10-16`;
- CSI500 / `000905.SH`: `2013-01-01 .. 2014-10-16`.

`2012-10-01 .. 2012-12-31` may be loaded only as feature history for previous close / frozen `rvol20` construction.

Do **not** open in the same execution:

- CSI300/CSI500 `2014-10-17 .. 2014-12-31` supporting crosscheck;
- any CSI1000 post-2026-08-21 outcome or V2 score.

## Frozen model identities

T2 primary confirmation uses the exact external-index full-DEV bundles frozen before Audit A:

- CSI300 bundle SHA256: `87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb`;
- CSI500 bundle SHA256: `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`.

They were trained only through `2010-12-31`. Do not refit them on Audit A or Audit B.

T1 still applies the frozen CSI1000 V2-v1 bundle only as descriptive transport. T1 never controls the Audit-B decision.

## Fixed benchmark

For each external index and sign, use the full-DEV empirical stage event rates stored in the frozen external parameter artifact. Do not estimate a new empirical benchmark from 2011-2012 or Audit-B rows.

## Target-row rule

A target day is valid only when the day has all exact 240 official one-minute clocks. Missing minutes invalidate the day for all three horizons. No forward-fill and no missing-minute-as-non-event inference.

Previous session 15:00 close, current 09:31 open, nonzero gap and positive complete prior-20-session `rvol20` are required.

## Frozen confirmation rule

Each of the four `index × sign` T2 heads must be sample-sufficient:

- all nonzero gaps >= 25;
- `abs_gap > 10bp` >= 20;
- `abs_gap > 30bp` >= 12.

Each sufficient head must pass all six gates:

1. pooled all-gap integrated Brier < frozen DEV empirical benchmark;
2. pooled all-gap integrated log-loss < benchmark;
3. pooled >10bp integrated Brier < benchmark;
4. pooled >30bp integrated Brier <= benchmark;
5. >10bp at least 2/3 horizon Briers < benchmark;
6. monotonicity violations = 0.

Overall labels are already frozen:

- all four sufficient + all four 6/6 pass -> `CT_AUDIT_B_final_backward_external_robustly_confirmed`;
- all four sufficient but at least one gate failure -> `CT_AUDIT_B_final_backward_external_not_confirmed`;
- any head insufficient -> `CT_AUDIT_B_evidence_insufficient`.

The 2014 supporting crosscheck cannot replace or rescue a failed Audit B.

## Source

Use the admitted raw canonical market-index parquet partition:

`/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index`

Dataset identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

## Commands

From current `main` at the execution-freeze commit or a descendant that has not modified the frozen protocol/evaluator/tests/parameter artifacts:

```bash
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE='/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index'

python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/evaluate_gap_fill_cross_index_audit_b.py
```

Do not run a supporting-crosscheck evaluator after this command chain.

## Expected outputs

Commit only:

- `docs/research/local_gap_fill_cross_index_transport_audit_b_receipt_v1.json`
- `docs/governance/local_gap_fill_cross_index_transport_audit_b_data_usage_v1.json`

Do not commit raw historical minutes or daily prediction rows.

## Return to cloud

Report/commit:

1. execution commit SHA;
2. validator exit code;
3. pytest exit code and passed count;
4. evaluator exit code;
5. source path used;
6. CSI300/CSI500 Audit-B loaded days, exact-240 days and target-valid counts;
7. each T2 head's all/>10bp/>30bp counts and six gates;
8. pooled model vs frozen-benchmark Brier/log-loss;
9. 2013 and 2014-through-Oct16 descriptive all-gap summaries;
10. T1 descriptive results;
11. final `decision` emitted by the frozen evaluator;
12. confirmation `supporting_crosscheck_opened=false`, `csi1000_post_2026_08_21_outcomes_opened=false`, and no refit/search/calibration occurred.

Cloud will independently adjudicate Audit B. Do not interpret or modify the frozen model locally after seeing the result.
