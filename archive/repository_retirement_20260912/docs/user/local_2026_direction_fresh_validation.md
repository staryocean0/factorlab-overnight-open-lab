# Local controller handoff — frozen 2026 direction fresh challenge

## Execution status

This window was opened once on 2026-09-06 by the local controller because the
cloud package has no raw 2021+ rows.

- fit freeze: `docs/research/cloud_session_20260906_local_2026_direction_fit_freeze_v1.json`
- receipt: `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`
- result: `docs/research/cloud_session_20260906_local_2026_direction_result.md`
- decision: `direction_candidate_2026_robustly_confirmed`
- `fresh_oos=true` for that receipt only
- `production_authority=false`

Do not retune features, alphas, quantile, threshold, class weights, calendar
exceptions or the 2026 endpoint on this window. A later run may only reproduce
the frozen receipt. Post-2026-08-21 remains unread for this identity.

## Mission

Run exactly one fresh 2026 challenge of the frozen direction-head successor candidate.

Authoritative protocol:

`docs/governance/cloud_session_20260906_direction_2026_fresh_protocol_v1.json`

Frozen candidate:

`docs/governance/cloud_session_20260906_direction_head_selected_v1.json`

Candidate spec SHA256:

`9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`

Runner:

`scripts/evaluate_local_2026_direction_head.py`

## Scientific boundary

- Fit window: 2015-01-05 through 2025-12-31.
- Fresh challenge: 2026-01-05 through 2026-08-21, fixed before opening candidate scores.
- Do not use any 2026 row for fitting, calibration, feature selection, threshold selection, quantile selection or class weighting.
- Do not extend or shorten the 2026 endpoint after seeing candidate results.
- Do not use trading return as a gate.
- Do not write raw 2026 rows into the bounded repository.

## Frozen models

Comparator:

`StandardScaler + Ridge(alpha=1.0)`, target `gap`, high-open decision `prediction >= 0`.

Candidate:

`StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")`, target `gap`, high-open decision `prediction >= 0`.

Both use exactly the same 13 causal features:

- `r1`
- `r20`
- `abs_r1`
- `prev_gap`
- `overnight_trend_5`
- `prev_daytime`
- `prev_last_hour`
- `prev_afternoon`
- `rvol20`
- `weekend`
- `holiday_reopen`
- `us_nasdaq`
- `us_vix_chg`

## Exact execution

From repository root:

```bash
python scripts/validate_theme_package.py
pytest -q
python scripts/evaluate_local_2026_direction_head.py
```

The runner first reconstructs/audits the frozen 2015-2020 identity, then loads only 2015-2025 for fitting and writes a fit-freeze receipt. Only after both model objects are fitted does it load/score the frozen 2026 challenge.

Default local source paths are inherited from the prior successful local 2021-2025 controller. If paths have moved, override only the file locations — never model semantics — with:

```bash
export OVERNIGHT_ANNOTATED_PANEL=/path/to/annotated_panel.parquet
export OVERNIGHT_DATAHUB_1M=/path/to/1m_official.parquet
export OVERNIGHT_FRED_NASDAQ=/path/to/fred_nasdaq.csv
export OVERNIGHT_FRED_VIX=/path/to/fred_vix.csv
```

Changing a path is infrastructure recovery, not model tuning. The source hashes are written into the receipt.

## Decision levels

### Raw-hit confirmation

Both must hold:

1. candidate direction hit is strictly greater than Ridge;
2. candidate correct-count increment is positive.

### Robust confirmation

All raw-hit conditions plus:

1. candidate balanced accuracy is at least Ridge balanced accuracy;
2. candidate recall on actual high-open observations is > 0.5;
3. candidate recall on actual low-open observations is > 0.5.

The robust layer exists because development diagnostics showed the Median candidate improved raw hit while pooled balanced accuracy did not improve. It prevents a regime/base-rate shift from being mistaken for a universally better direction model.

The exact McNemar/binomial test on disagreement days is reported for uncertainty, but it is not allowed to override the frozen pass/fail rules.

## Required return files

The runner writes:

- `docs/research/cloud_session_20260906_local_2026_direction_fit_freeze_v1.json`
- `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`
- `docs/governance/local_session_20260906_2026_direction_data_usage.json`

Commit those receipts and governance declarations only. Do not commit local raw market data.

Return the complete line prefixed:

`DIRECTION_2026_FRESH_RESULT`

## Decision semantics

- `direction_candidate_2026_robustly_confirmed`: candidate may enter a separate research-baseline review as the direction head paired with the already confirmed clock magnitude head. Production authority still remains false.
- `direction_candidate_2026_raw_hit_only_retain_ridge`: candidate beats raw hit but the base-rate/regime concern remains unresolved, so Ridge stays as the operational research direction head.
- `direction_candidate_2026_not_confirmed_retain_ridge`: retain Ridge and do not retune on this 2026 window in the same evidence cycle.

Do not open post-2026-08-21 data for this candidate identity during the same challenge cycle.
