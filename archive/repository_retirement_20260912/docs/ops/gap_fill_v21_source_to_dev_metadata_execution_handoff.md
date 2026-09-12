# V21 source verification -> DEV metadata admission handoff

Task ID: `V21-SA2-source-to-dev-metadata`

Status: **cloud controller prepared; empirical execution requires local parquet/DataHub visibility; DEV outcomes remain sealed.**

## Goal

Execute the two mandatory pre-outcome stages in one local command:

1. verify the frozen 2019-2024 audit package identity under `session_complete_239_required_v1`;
2. only if step 1 passes, inventory frozen V21_DEV `2015-01-01..2018-12-31` using only `symbol`, `trading_day`, `timestamp` under the same named-clock gate.

The controller then **must stop**. It does not open OHLC, build fill targets, fit a geometry control, fit P2 beta, or select a candidate.

## Cloud code

Use latest `main` after this handoff is merged, or branch:

`codex/v21-source-to-dev-metadata-controller`

Controller:

`scripts/run_v21_source_to_dev_metadata_controller.py`

Protocol:

`docs/governance/cloud_session_20260907_gap_fill_v21_source_to_dev_metadata_controller_v1.json`

## Required local inputs

### Audit package

Expected path by default:

`data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet`

Frozen expected identity:

- SHA256: `3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c`
- rows: `695929`
- parent HE-00 v8 identity: `25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`
- `000300.SH`: 1456 observed / 1449 complete / 7 incomplete
- `000905.SH`: 1456 observed / 1448 complete / 8 incomplete
- total missing required-clock rows: `39`

### DEV metadata source

Provide the authoritative local parquet file or partitioned parquet dataset that contains CSI300/CSI500 minute metadata for the frozen window:

`2015-01-01 .. 2018-12-31`

The controller reads only:

- `symbol`
- `trading_day`
- `timestamp`

It may point at the full parent HE-00 v8 lake because the controller filters the frozen date window after reading the metadata columns.

## Command

From repository root:

```bash
python3 scripts/run_v21_source_to_dev_metadata_controller.py \
  --audit-parquet data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet \
  --dev-source '<LOCAL_HE00_V8_OR_DEV_PARQUET_PATH>' \
  --parent-source-sha256 25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0
```

Expected terminal marker:

`V21_SOURCE_TO_DEV_METADATA_RESULT`

with:

- `source_verification_passed=true`
- `dev_metadata_inventory_passed=true`
- `V21_DEV_outcomes_opened=false`
- `hard_stop_before_DEV_outcomes=true`

## Outputs to commit/push

Only the two compact receipts:

- `docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json`
- `docs/research/local_gap_fill_v21_dev_metadata_admission_receipt_v1.json`

Do not push the large parquet unless explicitly requested.

## Fail-closed rules

The command must stop before DEV metadata if any of these fail:

- audit package SHA;
- audit package rows;
- parent HE-00 identity;
- reported per-symbol audit coverage;
- reported total of 39 missing required clocks.

The DEV metadata inventory itself keeps incomplete symbol-days fail-closed. Missing `14:59` alone is allowed; missing any other required clock, duplicate target-session clock, or unexpected target-session clock is recorded as an incomplete day. No minute is synthesized.

## Local feedback required

Push the two receipts and report:

1. execution commit SHA;
2. controller exit code;
3. actual audit package SHA/rows;
4. source verification pass/fail;
5. DEV per-symbol observed / complete / incomplete day counts;
6. DEV rejection reason counts and incomplete-day details;
7. confirmation `OHLC_read=false`;
8. confirmation `outcome_read=false`;
9. confirmation `V21_DEV_outcomes_opened=false`;
10. receipt commit SHA.

## What cloud will do immediately after receipt appears

Cloud will review both receipts. If and only if they are internally consistent and match the frozen contracts, cloud will:

1. mark source identity verified;
2. mark V21_DEV metadata admitted;
3. explicitly update state to authorize the frozen DEV outcome open;
4. execute the already-frozen V2.1 DEV expanding-OOF candidate ladder;
5. stop at the first eligible candidate, or close the P2 family if none is eligible.

Audit A/B and the external reserve stay sealed throughout DEV selection.
