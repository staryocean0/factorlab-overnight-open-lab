# V21 future-audit source admission — cloud/local handoff

Task ID: `V21-SA1-session-complete-239`

Status: **cloud gate frozen; local receipt/package identity still needs cloud-verifiable feedback; V21_DEV remains sealed.**

## Goal

Complete the source-admission evidence for the reported CSI300/CSI500 2019–2024 minute package without opening any V21 future outcome.

The cloud has already frozen the prospective gate as:

`required_239 = (09:31..11:30 + 13:01..15:00) - {14:59}`

This is a named-clock gate, not a generic row-count rule. All 239 required clocks must exist. `14:59` is optional and must never be synthesized. Any other missing clock remains fail-closed.

Cloud branch:

`codex/v21-session-complete-239-source-admission`

Cloud PR:

`#4 — V2.1: replace future exact-240 gate with session-complete 239 contract`

Gate implementation:

`scripts/v21_session_complete_239_gate.py`

Cloud contract:

`docs/governance/cloud_session_20260907_gap_fill_v21_future_audit_source_admission_v1.json`

Cloud adjudication:

`docs/research/gap_fill_v21_future_audit_source_admission_cloud_adjudication_20260907.md`

## Owner-reported local package

Expected local path:

`data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet`

Reported identity:

- rows: `695929`
- SHA256: `3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c`
- parent HE-00 v8 SHA256: `25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`
- calendar/trading days per symbol: `1456`
- `000300.SH`: `1449` session-complete, `7` incomplete
- `000905.SH`: `1448` session-complete, `8` incomplete
- audited days containing `14:59`: `0`
- genuine incomplete examples include `13:22`, `10:39–10:44`, `09:31–09:34`; those days remain invalid and were not filled.

Expected local receipt:

`docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json`

At cloud freeze time this receipt and the parquet are not visible in the GitHub checkout, so the above identity is recorded as owner-reported, not cloud file-verified.

## Local work required

Do **not** modify the historical RD1 runner and do **not** open V21_DEV.

On a local checkout containing the parquet:

1. fetch/check out the cloud branch `codex/v21-session-complete-239-source-admission` or otherwise use the exact gate module from that branch;
2. run the gate against the local parquet using metadata only;
3. verify the file SHA equals the reported SHA;
4. verify per-symbol complete/incomplete counts reproduce the reported values;
5. verify every rejected day is rejected for a required-clock hole/duplicate/unexpected target-session clock, not merely because `14:59` is absent;
6. do not read OHLC, gaps, fill targets, predictions or model scores during this admission check;
7. write/update the small receipt `docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json` with actual command, exit code, code SHA, package SHA, parent-source identity, row/day counts and gate result;
8. push the receipt only (the large parquet may remain local) to a branch accessible to cloud, or return the exact receipt file to the user for upload.

Suggested command, from repository root:

```bash
python3 scripts/v21_session_complete_239_gate.py \
  --parquet data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet \
  --expected-sha256 3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c \
  --output /tmp/v21_session_complete_239_metadata_audit.json
```

Then compare the generated metadata audit to the local admission receipt and the cloud contract.

## Expected local feedback

Return/commit only the compact evidence needed by cloud:

- local execution code/branch/commit SHA;
- command and exit code;
- actual parquet SHA256;
- actual row count;
- actual parent-source identity/provenance statement;
- `000300.SH` observed / complete / incomplete counts;
- `000905.SH` observed / complete / incomplete counts;
- total missing required-clock count;
- rejection reason counts;
- confirmation `OHLC_read=false` and `outcome_read=false`;
- confirmation no imputation/fill was performed;
- receipt path/commit SHA.

Do not upload raw per-minute rows merely to satisfy this handoff unless the user explicitly chooses to do so.

## Cloud acceptance criteria after local feedback

Cloud will distinguish `local_reported` from `cloud_reviewed`.

Source admission can move from `pending identity verification` to `verified` only if:

1. package SHA matches `3088ff...777c`;
2. parent HE-00 v8 identity matches `25f4...11f0`;
3. required-239 gate semantics are unchanged;
4. reported coverage/rejection counts reproduce or any discrepancy is explicitly adjudicated before outcome access;
5. future outcome fields remained unopened;
6. no missing middle clock was imputed.

After that, **V21_DEV is still not automatically open**. Cloud must first perform a metadata-only re-inventory of the 2015–2018 DEV source under the same named-clock gate and issue a separate authorization before any DEV OHLC/outcome/model work.

## Cloud execution evidence already completed

GitHub Actions run `34114270196` executed only static/source-gate checks and no future market data:

- gate self-test: passed;
- dedicated tests: `6 passed`;
- historical RD1 runner boundary check: passed;
- expected local admission receipt visibility in cloud checkout: `false`.

This CI result validates the gate implementation only. It is **not** a validation of the local parquet or its SHA.
