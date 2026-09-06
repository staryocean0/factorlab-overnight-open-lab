# Local controller handoff — frozen direction-head objective experiment

## Why this handoff exists

The cloud direction-head workflow failed twice before any job step or research code executed. The candidate family itself is already frozen and must not be changed during local recovery.

Authoritative family:

`docs/governance/cloud_session_20260906_direction_head_family_v1.json`

Pre-analysis:

`docs/research/direction_head_preanalysis_20260906.md`

Execution incident:

`docs/governance/cloud_session_20260906_direction_head_execution_incident_v1.json`

## Scientific boundary

This is a **development-only** experiment.

- Use only the bounded repository panel through 2020-12-31.
- Do not read, join, inspect, score, rank, or summarize 2021-2025 for this experiment.
- Do not open 2026+.
- Do not optimize trading return.

The objective is only to test whether changing the direction loss/objective improves high-open/low-open prediction while keeping the exact same 13 causal features.

## Frozen candidates

Comparator:

- `ridge_mean_sign`: `StandardScaler + Ridge(alpha=1.0)`, target `gap`, decision `prediction >= 0`.

Candidate A:

- `median_quantile_sign`: `StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")`, target `gap`, decision `prediction >= 0`.

Candidate B:

- `logistic_sign`: `StandardScaler + LogisticRegression(C=1.0, penalty="l2", solver="lbfgs")`, target `gap >= 0`, decision `P(up) >= 0.5`.

No feature changes, hyperparameter search, quantile search, class weighting, or threshold search are permitted.

## Exact execution

From repository root:

```bash
python scripts/validate_theme_package.py
pytest -q
python scripts/select_direction_head_dev.py
```

Do not edit `scripts/select_direction_head_dev.py` or the frozen family before execution unless there is a genuine compatibility error that prevents code execution. If a compatibility repair is necessary, record it as an infrastructure incident and preserve all model semantics exactly.

## OOF design

The script must execute exactly these expanding natural-year tests:

- train 2015 -> test 2016;
- train 2015-2016 -> test 2017;
- train 2015-2017 -> test 2018;
- train 2015-2018 -> test 2019;
- train 2015-2019 -> test 2020.

All candidates use the same complete-row mask.

## Frozen admission gate

A candidate is admitted only if all are true versus `ridge_mean_sign`:

1. year-equal mean direction hit is strictly higher;
2. total correct-count increment across the five OOF years is positive;
3. at least 3 of 5 annual hit-rate deltas are strictly positive;
4. median annual hit-rate delta is nonnegative.

If neither candidate passes, verdict is:

`no_incremental_direction_successor_retain_ridge`

If one candidate passes and uniquely wins the frozen ranking rule, verdict is:

`retrospective_direction_candidate_waiting_new_unseen_local_challenge`

This development result is not fresh OOS and cannot grant production authority.

## Return receipt

Capture the complete JSON printed after the prefix:

`DIRECTION_HEAD_DEV_SELECTION_RESULT`

Persist a machine-readable receipt containing at minimum:

- family SHA256;
- panel SHA256;
- all five fold metrics for all three models;
- year-equal baseline and candidate direction hit;
- annual hit deltas;
- positive-year count;
- median annual delta;
- total correct-count increment;
- pooled direction hit / balanced accuracy / AUC;
- selected candidate or `null`;
- final scientific status;
- `holdout_2021_2025_used=false`;
- `fresh_oos=false`;
- `production_authority=false`.

Do not open 2026 for a challenge until the development verdict has been reviewed and a separate challenge protocol is frozen.
