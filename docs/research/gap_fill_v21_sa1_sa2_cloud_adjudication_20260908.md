# Gap-Fill V2.1 SA1/SA2 cloud adjudication — 2026-09-08

Research identity: `gap_fill_v2_1_regime_conditioned_successor`.

## Decision

Decision: **`V21_SA1_SA2_cloud_review_passed_DEV_open_may_be_authorized`**.

The cloud review accepts both compact local receipts added at commit
`2110277ff1ea569e8021edd2eb7fc86f13bf8fd8`:

- `docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json`;
- `docs/research/local_gap_fill_v21_dev_metadata_admission_receipt_v1.json`.

This review is a cloud review of the committed local evidence and the frozen
contracts. The large local parquet remains absent from the cloud checkout, so
this is **not** represented as an independent second byte-for-byte cloud hash of
the local parquet. The receipt is nevertheless cloud-verifiable as a committed,
result-bounded artifact, and the predeclared handoff explicitly allows cloud to
advance after the two receipts are internally consistent and match the frozen
contracts.

## Execution-lineage integrity

The source-to-DEV metadata controller freeze/merge point is:

`254dd461abf49f23965be557cee556001f941d85`.

The receipt commit is exactly one commit later:

`2110277ff1ea569e8021edd2eb7fc86f13bf8fd8`.

The compare `254dd46..2110277` contains exactly two added files and no modified
protocol, gate, runner, candidate family, evaluation kernel, test, or state file:

1. `local_gap_fill_v21_future_audit_source_admission_receipt_v1.json`;
2. `local_gap_fill_v21_dev_metadata_admission_receipt_v1.json`.

Both receipts report `code_commit=254dd461abf49f23965be557cee556001f941d85`.
This satisfies the result-free execution-identity requirement.

## SA1 — future-audit source admission

Task: `V21-SA1-session-complete-239`.

Frozen gate: `session_complete_239_required_v1`, defined as the legacy named
09:31..11:30 + 13:01..15:00 clock set with `14:59` optional. This remains a
named-clock gate, never a generic row-count rule.

Cloud-reviewed receipt facts:

- package rows: `695929` — matches frozen contract;
- package SHA256:
  `3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c`
  — matches frozen contract;
- parent HE-00 v8 SHA256:
  `25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`
  — matches frozen contract;
- `000300.SH`: 1456 observed / 1449 complete / 7 incomplete;
- `000905.SH`: 1456 observed / 1448 complete / 8 incomplete;
- total missing required-clock rows: `39`;
- `14:59` present days: `0`;
- no middle-clock imputation;
- `OHLC_read=false`;
- `outcome_read=false`;
- `V21_DEV_outcomes_opened=false`;
- successor fit/selection not performed.

The incomplete-day examples remain genuine required-clock holes and were not
silently repaired. Therefore SA1 passes.

## SA2 — source-to-DEV metadata admission

Task: `V21-SA2-source-to-dev-metadata`.

The controller used only `symbol`, `trading_day`, and `timestamp` for the frozen
`2015-01-01..2018-12-31` V21_DEV interval, under the same named 239-clock gate.

Cloud-reviewed receipt facts, per symbol:

- observed trading days: `975`;
- session-complete days: `944`;
- incomplete days: `31`;
- optional `14:59` present days: `884`;
- rejection reason is fail-closed required-clock incompleteness;
- metadata inventory total rows: `467094`;
- total missing required-clock rows across the two symbol inventories: `724`;
- no imputation;
- `OHLC_read=false`;
- `outcome_read=false`;
- `V21_DEV_outcomes_opened=false`;
- successor fit/selection not performed.

The controller acceptance object reports all frozen admission checks true,
including both symbols present, frozen-window-only, complete metadata inventory,
same named gate, and fail-closed rejection reporting. Therefore SA2 passes.

## Scientific/governance consequence

The historical exact-240 blocker is closed for the prospective V2.1 path. The
cloud now has the two compact receipts that the frozen handoff required before a
separate DEV-open decision.

The following may now be authorized in a new explicit authorization artifact:

- open V21_DEV `2015-01-01..2018-12-31` CSI300/CSI500 OHLC only;
- construct the frozen gap/fill targets using the 239 named-clock validity gate;
- fit the same-era geometry control inside the frozen expanding-year folds;
- fit only the frozen P2 candidate ladder;
- execute candidates in the frozen order and stop at the first eligible one;
- write aggregate DEV evidence and, if selected and full-DEV refit remains valid,
  a parameter freeze.

The following remain sealed:

- V21_AUDIT_A `2019-01-01..2021-12-31` outcomes;
- V21_AUDIT_B `2022-01-01..2024-12-31` outcomes;
- V21_EXTERNAL_RESERVE `2025-01-01..2026-08-21` outcomes;
- 2014Q4 supporting crosscheck;
- CSI1000 post-2026-08-21 true-fresh outcomes.

No production authority is granted.

## Next action

Create a separate DEV-open authorization bound to this adjudication, update the
current V21 state, and execute the already-frozen V21_DEV expanding-OOF ladder.
Because the full 2015-2018 CSI300/CSI500 OHLC source is local-only, the empirical
DEV run itself must execute on the local controller after the cloud supplies the
frozen runner and handoff. Cloud must review the resulting compact DEV receipt
before Audit A may open.
