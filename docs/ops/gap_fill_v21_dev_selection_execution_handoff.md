# V21 DEV expanding-OOF P2 selection — cloud/local handoff

Task ID: `V21-DEV1-expanding-oof-P2`

Status: **SA1/SA2 cloud review passed; V21_DEV open is explicitly authorized; code and gates are frozen; empirical execution requires the local full-OHLC HE-00 v8 source. Audit A/B remain sealed.**

## Cloud decision already completed

Cloud adjudication:

`docs/research/gap_fill_v21_sa1_sa2_cloud_adjudication_20260908.md`

DEV-open authorization:

`docs/governance/cloud_session_20260908_gap_fill_v21_dev_open_authorization_v1.json`

Execution freeze:

`docs/governance/cloud_session_20260908_gap_fill_v21_dev_execution_freeze_v1.json`

Execution-freeze commit:

`2ec24962b592d93025a15a7251712ebe163ef21f`

The historical 2026-09-07 family/protocol/evaluation-kernel files were not rewritten. Their `DEV unopened` flags remain freeze-time facts; the 2026-09-08 authorization plus current state provide the separate authority to open DEV now.

## Goal

Execute exactly one frozen V21_DEV selection pass on CSI300/CSI500 `2015-01-01..2018-12-31`:

1. metadata-only preflight must reproduce the cloud-admitted SA2 counts under `session_complete_239_required_v1`;
2. only after that passes, read DEV OHLC;
3. construct the frozen 09:31 gap and 15m/60m/EOD fill targets;
4. fit same-era geometry controls inside the frozen expanding-year folds;
5. evaluate the P2 ladder in exact complexity order;
6. stop at the first eligible candidate;
7. if selected, refit that exact candidate on full DEV and require every selected beta component to be strictly positive;
8. write compact aggregate evidence only.

Do not open Audit A/B or any other sealed block.

## Frozen scientific identity

Only new state variable:

`P2_relative_gap_excess = sign(gap_i) * (gap_i-gap_j) / rvol20_i`

Candidate order:

1. `P2_XI_SHARED_1B`
2. `P2_CSI500_SHARED_1B`
3. `P2_CSI500_STAGE_2B`

Rule: **first eligible wins; later candidates are not evaluated after an earlier eligible candidate.**

OOF folds:

- train 2015 -> validate 2016;
- train 2015-2016 -> validate 2017;
- train 2015-2017 -> validate 2018.

Primary cell: CSI500 high `abs_gap > 10bp`.

Primary horizons: 15m and 60m. EOD is mandatory descriptive reporting only.

No candidate addition/reordering, model-class search, hyperparameter search, beta-bound/regularizer search, calibration, binary threshold selection, or trading-return selection is allowed.

## Source contract

Use the authoritative full-OHLC HE-00 v8 parent lake or an equivalent CSI300/CSI500 full-OHLC extract whose provenance is bound to parent SHA256:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

The authorized entry point accepts a full parent lake containing additional indices, but it metadata-filters to only:

- `000300.SH`;
- `000905.SH`;
- `2015-01-01..2018-12-31`.

Before OHLC access it must reproduce, for each authorized symbol:

- observed days = `975`;
- session-complete days = `944`;
- incomplete days = `31`.

Target validity uses the same named-clock gate as SA1/SA2:

- required clocks = legacy session 240 minus optional `14:59`;
- `14:59` is used only if actually present;
- it is never synthesized;
- any other missing/duplicate/unexpected target-session clock fails closed.

## Local commands

From repository root, first check out the execution freeze or a later `main` that preserves the frozen blob identities:

```bash
git fetch origin
git checkout 2ec24962b592d93025a15a7251712ebe163ef21f
```

Run static checks first:

```bash
python3 -m py_compile \
  scripts/run_gap_fill_v21_dev_selection.py \
  scripts/run_gap_fill_v21_dev_selection_authorized.py

python3 -m pytest -q \
  tests/test_gap_fill_v21_candidate_family.py \
  tests/test_gap_fill_v21_evaluation_kernel.py \
  tests/test_gap_fill_v21_dev_runner.py \
  tests/test_v21_session_complete_239_gate.py
```

If any static check fails, stop without opening DEV OHLC and report the failure.

If static checks pass, execute:

```bash
python3 scripts/run_gap_fill_v21_dev_selection_authorized.py \
  --source '<LOCAL_FULL_HE00_V8_OR_EQUIVALENT_CSI300_CSI500_OHLC_PARQUET>' \
  --parent-source-sha256 25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0
```

The source may also be supplied through `OVERNIGHT_HISTORICAL_INDEX_1M_LAKE`.

Expected terminal marker:

`V21_DEV_SELECTION_RESULT`

## Allowed outputs to commit/push

Always, after a successful runner exit:

- `docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`
- `docs/governance/local_gap_fill_v21_dev_data_usage_v1.json`

Only if the first eligible candidate is selected and the full-DEV positive-beta gate passes:

- `docs/governance/local_gap_fill_v21_dev_parameter_freeze_v1.json`

Do not push raw minute rows, target-level rows, OOF daily predictions, or the large source parquet.

Commit only the compact outputs using `[skip ci]` and push them to an accessible branch or `main` if the local controller is authorized to do so.

## Fail-closed conditions

Stop before/while execution if any of these occur:

- source parent identity does not match the frozen HE-00 v8 provenance;
- metadata preflight does not reproduce SA2 counts;
- the frozen 2015-2018 window drifts;
- the two authorized symbols are missing;
- session-complete-239 semantics drift;
- a geometry risk set lacks required classes;
- P2 training values are non-finite or have zero scale;
- beta optimizer fails;
- probability monotonicity is violated;
- candidate order changes;
- any future partition is read;
- a selected candidate's full-DEV beta component is not strictly positive.

No date extension or post-hoc rescue is permitted.

## Required local feedback

Return/commit and report:

1. execution commit SHA;
2. `py_compile` exit code;
3. pytest exit code and pass count;
4. DEV runner exit code;
5. actual source path and parent-provenance assertion;
6. metadata preflight per-symbol observed / complete / incomplete counts;
7. target-valid inventory for CSI300 and CSI500;
8. geometry-control OOF inventory;
9. each attempted candidate, beta history, eligibility gates and candidate-specific extra gate;
10. attempted candidate count;
11. selected candidate or null;
12. if selected, full-DEV parameter bundle SHA256 and all full-DEV beta values;
13. confirmations `Audit_A_outcomes_opened=false`, `Audit_B_outcomes_opened=false`, `External_Reserve_outcomes_opened=false`, `supporting_crosscheck_2014Q4_opened=false`, `CSI1000_post_2026_08_21_outcomes_opened=false`;
14. receipt/data-usage/parameter-freeze paths and output commit SHA.

## What cloud will do after the receipt appears

Cloud will compare the result commit against this execution freeze, verify that only allowed compact outputs were added, recompute the frozen eligibility decision from the receipt, and then issue exactly one next decision:

- if a candidate is validly selected: freeze/accept the selected V21 identity and create a **separate** Audit-A open authorization;
- if no candidate is eligible: close the P2 family as `V21_DEV_no_P2_successor`; Audit A remains sealed;
- if execution or evidence is invalid: fail closed and do not open Audit A.

Audit B can never open directly from this DEV result. Production authority remains false.
