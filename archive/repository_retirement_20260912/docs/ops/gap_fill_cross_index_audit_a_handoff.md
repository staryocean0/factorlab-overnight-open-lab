# CT-AUDIT-A — local execution handoff

## Status

Cloud review of CT-DEV is complete. Audit A is preregistered, statically validated, and execution-frozen. The local Unified DataHub raw canonical lake is required for actual execution.

Research identity:

`gap_fill_cross_index_transport_v1`

Execution freeze:

`docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_a_execution_freeze_v1.json`

Protocol:

`docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_a_protocol_v1.json`

Evaluator:

`scripts/evaluate_gap_fill_cross_index_audit_a.py`

## Authorized open

Only:

- CSI300 / `000300.SH`: `2011-01-01 .. 2012-12-31`;
- CSI500 / `000905.SH`: `2011-01-01 .. 2012-12-31`.

The evaluator may load `2010-10-01 .. 2010-12-31` solely as feature history for previous close and the frozen `rvol20` formula.

Do **not** open:

- Audit B: `2013-01-01 .. 2014-10-16`;
- supporting crosscheck: `2014-10-17 .. 2014-12-31`;
- any CSI1000 post-2026-08-21 outcome or score.

## Frozen source

Use the same HE-00 admitted raw canonical dataset. The dataset root contains JSON metadata files, so point pandas at the parquet partition root:

`/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index`

Dataset SHA256 identity:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

## Frozen model identities

T2 primary Audit-A heads, no refit:

- CSI300 bundle SHA256 `87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb`;
- CSI500 bundle SHA256 `6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957`.

T1 descriptive-only CSI1000 reference:

- architecture SHA256 `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`;
- parameter bundle SHA256 `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`.

T1 cannot rescue a failed T2 gate.

## Audit-A gate

For each of the four heads independently (`CSI300 high`, `CSI300 low`, `CSI500 high`, `CSI500 low`), first require at least:

- 25 all-gap rows;
- 20 rows with `abs_gap > 10bp`;
- 12 rows with `abs_gap > 30bp`.

If sufficient, all six T2 gates must pass:

1. all-gap integrated Brier < frozen DEV empirical benchmark;
2. all-gap integrated log-loss < benchmark;
3. >10bp integrated Brier < benchmark;
4. >30bp integrated Brier <= benchmark;
5. >10bp at least 2/3 horizon Brier scores < benchmark;
6. monotonicity violations = 0.

Only if all four heads are sufficient and 6/6 pass does the receipt mark Audit-B eligibility. **Do not run Audit B locally even if eligible.** Return to cloud first.

## Target validity

A target day is valid only if all exact 240 official one-minute clocks are present. No forward fill. Missing minutes cannot be treated as non-events. Previous 15:00, current 09:31 and positive `rvol20` are also required.

## Commands

```bash
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE='/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824/instrument_type=market_index'

python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/evaluate_gap_fill_cross_index_audit_a.py
```

## Expected outputs

Commit only:

- `docs/research/local_gap_fill_cross_index_transport_audit_a_receipt_v1.json`
- `docs/governance/local_gap_fill_cross_index_transport_audit_a_data_usage_v1.json`

You may append the execution report to `docs/ops/cloud_local_communication.md`.

Do not commit raw historical minutes or row-level predictions.

## Return to cloud

Report:

1. execution HEAD;
2. validator / pytest / evaluator exit codes and pytest pass count;
3. source path used;
4. CSI300/CSI500 Audit-A loaded days, exact-240 days and target-valid counts;
5. each of the four T2 head sample counts, six gates and pass/fail;
6. pooled all/>10bp/>30bp T2 vs frozen DEV benchmark Brier/log-loss and horizon Brier summaries;
7. annual 2011/2012 all-gap T2 vs benchmark summaries;
8. T1 descriptive metrics;
9. `audit_b_eligibility_under_frozen_rule`;
10. confirmations `audit_b_opened=false`, `supporting_crosscheck_opened=false`, `csi1000_post_2026_08_21_outcomes_opened=false`;
11. confirmations no refit, calibration, feature/model/C/threshold/horizon search occurred.

Cloud will independently adjudicate Audit A before any Audit B open.
