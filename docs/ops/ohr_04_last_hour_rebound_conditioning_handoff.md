# OHR-04 — Last-hour rebound conditioning diagnostic

Status: **local development execution recorded; waiting for cloud review**.

OHR-03 remains unopened and reserved for a future frozen successor repeat-blackbox run. This task is numbered OHR-04 deliberately.

## Objective

Explain why the rejected `weakness_last_hour_piecewise` progression candidate rescues some actual high opens but also creates too many false high-open calls. This task is diagnostic only. It does not select a successor and does not open 2026.

Cloud review of OHR-02 is recorded in:

- `docs/research/high_open_recall_phase2_cloud_review_20260906.md`

Frozen diagnostic protocol:

- `docs/governance/cloud_session_20260906_high_open_rebound_conditioning_protocol_v1.json`

Frozen diagnostic runner:

- `scripts/diagnose_last_hour_rebound_conditioning_dev.py`

## Evidence boundary

- 2015-01-05..2025-12-31: development diagnostic material.
- OOF: expanding natural years 2016..2025.
- 2026-01-05..2026-08-21: sealed repeat blackbox; **must not be loaded or read**.
- post-2026-08-21: unread true-fresh evidence; **must remain unread**.
- OHR-03: not opened.

## Fixed identities

Incumbent:

- `median_quantile_sign`
- spec SHA256 `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`

Diagnostic progression candidate only:

- `weakness_last_hour_piecewise`
- spec SHA256 `1a37a46c4c66026f6abe33b84a9d7704ab7c7513312ef15b25607dcfa694392d`
- status remains rejected as a successor.

The runner first replays both identities and verifies their development metrics against the sealed OHR-02 receipt before doing any conditioning diagnostics.

## What the diagnostic measures

Prediction disagreements are split into four exact types:

1. incumbent down -> candidate up, actual up: rescued high open;
2. incumbent down -> candidate up, actual down: new false high;
3. incumbent up -> candidate down, actual up: lost high open;
4. incumbent up -> candidate down, actual down: repaired false high.

The main question is what distinguishes type 1 from type 2.

Only preregistered causal pre-open states are inspected:

- breadth/concentration of prior China weakness;
- whether weakness is tail-only versus broad full-day/afternoon weakness;
- prior gap context;
- existing `r1`, `r20`, `rvol20`, `abs_r1` trend/risk context.

No new US interaction search is allowed in this task because the positive-US and China-weakness x US-up channels were already adjudicated in Phase 1.

## Forbidden

Do not:

- read or load 2026 data/results for this diagnostic;
- rank candidates or freeze a successor;
- search parameters, quantiles, thresholds or class weights;
- add new probe families after seeing the output;
- optimize trading returns;
- open OHR-03.

## Local execution

Run exactly:

```bash
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/diagnose_last_hour_rebound_conditioning_dev.py
```

If source paths have moved, only the already-authorized path override environment variables may be used:

- `OVERNIGHT_ANNOTATED_PANEL`
- `OVERNIGHT_DATAHUB_1M`
- `OVERNIGHT_FRED_NASDAQ`
- `OVERNIGHT_FRED_VIX`

Do not modify the protocol, runner, probes, development endpoint or OOF years to fit results.

## Expected outputs

The runner writes only aggregate evidence:

- `docs/research/cloud_session_20260906_local_last_hour_rebound_conditioning_receipt_v1.json`
- `docs/governance/local_session_20260906_last_hour_rebound_conditioning_data_usage.json`

Do not commit raw 2015+ market rows or row-level OOF predictions.

## Cloud acceptance checks

Cloud review will require at least:

- all three commands exit 0;
- development end = 2025-12-31 and OOF = 2016..2025;
- incumbent and last-hour metric replay matches the sealed OHR-02 receipt;
- 2026 rows loaded = false; 2026 blackbox opened = false; OHR-03 opened = false;
- candidate/parameter/threshold/quantile selection flags all false;
- disagreement morphology and all preregistered probe aggregates are present;
- 2015-2020 reconstruction remains exact;
- source hashes are complete;
- raw rows are not persisted to the bounded repo;
- production authority remains false.

After local execution, push only the aggregate receipt/data-usage plus a concise execution note. Cloud will review the conditioning mechanism before any later candidate family is allowed.
