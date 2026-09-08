# RMR Stage-1 parallel screen — cloud/local execution handoff

Task ID: `RMR-STAGE1-PARALLEL-01`

Status: **common data role, two scale pairings, R1/R2/R3 event semantics, runner, tests, and execution identity are frozen before empirical screening. Local empirical execution is now authorized.**

## Goal

Run exactly one equal-budget shallow mechanism screen for all three primary lanes:

- R1 — cross-scale pullback inside an intact parent trend;
- R2 — range-boundary / failed-breakout reversion;
- R3 — regime-conditioned residual reversion.

This is development-only mechanism research. It is not a trading backtest and must not rank lanes by PnL.

## Frozen identity

Execution freeze:

`docs/governance/reversal_mean_reversion_stage1_execution_freeze_v1.json`

Implementation freeze commit:

`3d6ea62062168374650254aa9aa9df706815ec34`

Frozen runner blob:

`5dadd2be97ad9e6ab14c166bb09145f347a9a5e8`

Runner:

`scripts/run_rmr_stage1_parallel_screen.py`

Tests:

`tests/test_rmr_stage1_parallel_screen.py`

Common data role:

`docs/governance/reversal_mean_reversion_stage1_common_data_role_v1.json`

Execution protocol:

`docs/governance/reversal_mean_reversion_stage1_execution_protocol_v1.json`

## Common data

Use exactly:

`data/high_open_dev_2015_2025/1m_official.parquet`

Expected SHA256:

`11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce`

Frozen role:

- instrument: `000852.SH` / CSI1000;
- window: `2015-01-05 .. 2025-12-31`;
- evidence label: **development material only**;
- 2026 rows: forbidden.

The entire 2015-2025 interval was already consumed by prior legacy research, so this Stage-1 screen may use it for discovery but must never call the result fresh OOS.

## Frozen measurement scales

Both pairings must run and both must be reported:

- `PAIR_A`: lower directional-change reversal = `0.50 × prior sigma20`; parent = `1.50 × prior sigma20`;
- `PAIR_B`: lower = `0.75 × prior sigma20`; parent = `2.25 × prior sigma20`.

The volatility unit is the 20 completed-session close-to-close log-return standard deviation available strictly before the current session.

Do not add a third scale, delete a scale, or pick whichever scale looks better after results.

## Frozen lane semantics

### R1

Event: a causally completed lower wave moving against the sign of the parent two-wave drift snapshot available at the lower-wave start information time.

Outcome: lower counter-wave origin recovery first vs parent structural-anchor failure first, maximum five trading sessions.

Exactly three objects:

1. severity only;
2. parent state only;
3. parent state + severity.

### R2

Event: first 1m close at least `0.10 × parent range width` outside the causal two-parent-wave envelope.

Outcome: old range-edge reentry first vs symmetric further extension first, maximum five sessions.

No hard post-hoc range label is allowed; range character remains continuous through drift/overlap/path-efficiency measurements.

Exactly three objects:

1. excursion size only;
2. parent range state only;
3. parent range + state-change measurements.

### R3

Sample unit: causally completed lower wave.

Conditional normal path: low-capacity `StandardScaler + Ridge(alpha=1)` on the frozen parent-state vector, trained only on earlier chronological development blocks.

Compare state-conditioned residual with unconditional deviation on paired events where both absolute deviations are at least `0.50 sigma`.

Reversion/extension use symmetric first-passage distance equal to `0.50 × abs(residual) × event sigma`, maximum five sessions.

No HMM, Koopman, deep autoencoder, regime-count search, or latent-dimension search is allowed in Stage 1.

## Commands

From repository root after pulling the cloud commits:

```bash
python3 -m pytest -q tests/test_rmr_stage1_parallel_screen.py
python3 -m pytest -q
python3 scripts/run_rmr_stage1_parallel_screen.py
```

The runner uses the repository common-data path by default. Do not replace the dataset with another index/file merely to make a lane look stronger.

## Fail-closed rules

Before opening the empirical Stage-1 result, the dedicated test file must pass.

The runner itself must fail if:

- source SHA is not the frozen SHA;
- any row lies after `2025-12-31`;
- the common data role is not `development_material_only`;
- R2 trigger is not exactly `0.10` range width;
- R3 residual threshold is not exactly `0.50 sigma`;
- frozen protocol stage/identity drifted.

If tests or runner fail because of implementation defects, stop and report the defect. Do not edit thresholds, pairings, event definitions, features, or horizons after seeing partial empirical output.

## Expected outputs

Only compact aggregate evidence:

- `docs/research/local_rmr_stage1_parallel_screen_receipt_v1.json`
- `docs/governance/local_rmr_stage1_parallel_screen_data_usage_v1.json`

Do not commit raw events, row-level labels, charts keyed by date, model predictions, or derived minute datasets in this step.

## Required feedback

Commit/push the two compact outputs and report:

1. execution commit SHA;
2. dedicated-test exit code / count;
3. full-pytest exit code / count;
4. runner exit code;
5. source SHA and source inventory;
6. per pairing: lower/parent completed-wave counts;
7. R1 event/resolved/censored counts and the two chronological model-score folds for all three frozen objects;
8. R2 event/resolved/censored counts and the same object comparison;
9. R3 completed-wave samples, paired event supply, conditional vs unconditional reversion share in DEV_B and DEV_C;
10. confirmation both `PAIR_A` and `PAIR_B` were executed;
11. confirmation `2026_rows_loaded=false`;
12. confirmation no scale/horizon/parameter search and no trading return/PnL was used;
13. receipt commit SHA.

## What cloud will do after receipt appears

Cloud will review all three lanes **together**. Only after R1, R2, and R3 have the same first-pass evidence budget will cloud compare:

- effect direction;
- chronological stability;
- scale consistency;
- sample supply/censoring;
- whether conditioning adds beyond the simple baseline;
- definition/data complexity;
- independence from closed legacy R4.

At most two lanes may progress without a new program-level review. A lane may instead be held for better data or closed. No lane receives production or fresh-OOS authority from this Stage-1 screen.
