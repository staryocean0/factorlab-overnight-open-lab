# Local 2026 Direction-Head Fresh Challenge

Status: `direction_candidate_2026_robustly_confirmed`

Production authority: `false`

This is the one-shot local fresh challenge required by
`docs/governance/cloud_session_20260906_direction_2026_fresh_protocol_v1.json`.
Both frozen direction heads were fitted on 2015-01-05 through 2025-12-31 before
any 2026 target was scored. Features, alphas, quantile, threshold, class
weights, calendar exceptions and the 2026 endpoint were not changed after the
window opened. Trading return was not used in the gate. Raw 2026 rows were not
written into this bounded repository.

## Infrastructure recovery before execution

The cloud workspace could not open this step because the bounded package still
contains no raw 2021+ market rows. Local execution reused the same controller
paths as the prior 2021-2025 confirmation:

- annotated panel `timing_layer2_overnight_gap_ledger_v1_2`
- DataHub export `factorlab_unified_index_kline_v3_20260824/1m_official.parquet`
- FRED NASDAQ and VIX prints

Those local files already end at the frozen challenge endpoint `2026-08-21`.
Path overrides were not required.

The frozen runner also contained JSON literals `true`/`false` inside a Python
dict. That is an infrastructure defect, not a model choice. The literals were
converted to Python booleans before the one-shot run. No feature, loss,
quantile, solver, threshold or endpoint changed.

## Fit freeze

- candidate spec SHA256: `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`
- comparator: `StandardScaler + Ridge(alpha=1.0)`, target `gap`, decision `prediction >= 0`
- candidate: `StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver=highs)`, target `gap`, decision `prediction >= 0`
- same 13 causal features as the frozen direction family
- n_fit_rows = 2674; n_fit_complete = 2649
- 2015-2020 reconstruction versus the frozen package panel had maximum absolute error 0 on every contracted column
- freeze file: `docs/research/cloud_session_20260906_local_2026_direction_fit_freeze_v1.json`

## Fresh window

- protocol window: 2026-01-05 through 2026-08-21
- actual trading days: 2026-01-05 through 2026-08-21
- n_validation_rows = n_validation_complete = 154
- dropped missing = 0
- post-2026-08-21 remains unread for this candidate identity

## Primary gate

| Metric | Ridge comparator | Median candidate | gate |
|---|---:|---:|---|
| direction hit | 0.642857 | 0.720779 | candidate higher |
| correct count | 99 | 111 | +12 |
| balanced accuracy | 0.646160 | 0.725148 | candidate at least Ridge |
| recall_up | 0.518987 | 0.556962 | candidate > 0.5 |
| recall_down | 0.773333 | 0.893333 | candidate > 0.5 |

Both the raw-hit layer and the robust layer pass. Decision:
`direction_candidate_2026_robustly_confirmed`.

## Secondary reporting only

These numbers do not authorize retuning, endpoint changes, or production.

- actual high-open share = 0.512987
- Ridge predicted-up share = 0.376623; Median predicted-up share = 0.337662
- ROC AUC: Ridge 0.728439, Median 0.776540
- disagreements = 20; Median-only-correct = 16; Ridge-only-correct = 4
- two-sided exact McNemar/binomial p = 0.011818

Monthly direction hit is reporting-only:

| Month | n | Ridge hit | Median hit |
|---|---:|---:|---:|
| 2026-01 | 20 | 0.800000 | 0.950000 |
| 2026-02 | 14 | 0.785714 | 0.714286 |
| 2026-03 | 22 | 0.727273 | 0.772727 |
| 2026-04 | 21 | 0.476190 | 0.619048 |
| 2026-05 | 18 | 0.722222 | 0.777778 |
| 2026-06 | 21 | 0.714286 | 0.666667 |
| 2026-07 | 23 | 0.521739 | 0.652174 |
| 2026-08 | 15 | 0.400000 | 0.600000 |

February and June do not beat Ridge on raw hit. They are not a license to add
calendar exceptions.

## Authority

- `fresh_oos=true` for this receipt only
- `production_authority=false`
- this 2026-01-05_to_2026-08-21 window is now consumed for the frozen Median
  direction identity and may not be used to retune it in the same evidence cycle
- the candidate is eligible for a separate research-baseline review as the
  direction head paired with the already confirmed clock-aware magnitude head
- no FactorLab live registry, pointer, account or production state was changed
