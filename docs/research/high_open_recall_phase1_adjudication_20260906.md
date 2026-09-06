# High-open recall Phase-1 mechanism adjudication — 2026-09-06

## Evidence accepted

Cloud review accepts local OHR-01 commit `cfadb9c0d106952a4915c125bf1b6fee4d72e846` as a valid development-only diagnostic execution.

Integrity checks:

- the local writeback changed only aggregate receipt/governance/communication/index files; it did not modify the frozen diagnostic runner, protocol, or tests after observing results;
- development ended at `2025-12-31` and expanding OOF covered only natural years 2016–2025 (`n=2426`);
- `2026_rows_loaded=false` and `2026_blackbox_opened=false`;
- no candidate selection, parameter search, threshold search, or trading-return optimization occurred;
- the 2015–2020 reconstruction matched the bounded frozen package field-for-field with maximum absolute difference 0;
- the market/FRED source hashes match the previously used local source identities;
- raw development rows and row-level OOF predictions were not committed.

Primary receipt:
`docs/research/cloud_session_20260906_local_high_open_recall_diagnostic_receipt_v1.json`.

The incumbent expanding-OOF direction metrics over 2016–2025 are:

- direction hit `0.717642`;
- balanced accuracy `0.701019`;
- high-open recall `0.626059`;
- low-open recall `0.775978`;
- ROC AUC `0.766960`;
- predicted-up share `0.380462` vs actual-up share `0.389118`;
- TP/FN/TN/FP = `591/353/1150/332`.

## H1 — boundary noise: partial, not the primary explanation

High-open recall increases with realized positive-gap magnitude:

- `0–10bp`: `0.5676`, 147 misses / 340 events;
- `10–30bp`: `0.6080`, 118 misses / 301 events;
- `>30bp`: `0.7119`, 87 misses / 302 events.

However, 205 of the 353 false negatives are larger than 10bp and 87 are larger than 30bp. Only 26.6% of false negatives lie within 5bp of the score boundary; 34.6% are 5–15bp below zero and 38.8% are more than 15bp below zero. Median false-negative score margin is 10.88bp.

Verdict: `partial_support_not_primary`. The weakness is not mainly a zero-threshold labeling artifact. A threshold patch is therefore not admitted as the scientific successor mechanism.

## H2 — slow opening regime: not supported strongly enough

Prior-only 20/60-day high-open shares and mean/median gap states show small FN-vs-TP standardized differences and mixed annual signs. Representative results:

- `gap_up_share_20`: `-0.044`, 5 positive / 5 negative annual FN-TP signs;
- `gap_up_share_60`: `+0.037`, 6 / 4;
- `gap_mean_20`: `-0.152`, 6 / 4;
- `gap_mean_60`: `-0.031`, 6 / 4;
- incumbent `overnight_trend_5`: `-0.125`, 4 / 6.

Verdict: `not_admitted`. No slow-state feature is allowed into Phase 2.

## H3 — missing positive overseas pass-through: rejected as the residual mechanism

The incumbent already captures completed-US-session direction information strongly:

- `us_nasdaq_interval` FN-minus-TP standardized difference `-0.867`, same sign in 10/10 years;
- positive NASDAQ interval part: `-1.053`, same sign in 10/10 years;
- VIX drop: `-0.864`, same sign in 10/10 years;
- joint NASDAQ-up × VIX-down risk-on probe: `-0.609`, same sign in 10/10 years.

Most importantly, in the top NASDAQ-interval quartile the actual high-open share is `0.699` and incumbent high-open recall is already `0.884`. In the bottom quartile the actual high-open share is only `0.168` and recall is `0.137`.

Interpretation: strong positive US risk-on is already a region where the incumbent performs very well. The remaining misses are disproportionately high opens that occur despite weak/non-positive global information. Adding more positive-US terms would reinforce an already-successful channel rather than explain the residual error.

Verdict: `not_admitted_for_phase2`.

## H4 — China weakness × positive-US catch-up: rejected in its preregistered form

The preregistered interaction probes are not development-stable:

- full-day weakness × US-up: 3 positive / 7 negative annual FN-TP signs;
- afternoon weakness × US-up: 3 / 7;
- last-hour weakness × US-up: 3 / 7.

Verdict: `rejected_as_risk_on_interaction`. The positive-US interaction terms are not allowed into Phase 2.

## H5 — exceptional clock accumulation: not supported as a direction-recall mechanism

`us_session_count` has only a small standardized FN-TP difference (`-0.099`) with mixed annual signs (3 positive / 7 negative). `holiday_reopen` has insufficient variation for this diagnostic.

Verdict: `not_admitted_for_direction_successor`.

## H6 — prior-China-weakness nonlinear rebound: supported

A stronger mechanism emerged from the preregistered marginal China-weakness probes inside H4. False-negative actual-high-open days are consistently preceded by materially weaker China intraday paths than correctly detected high-open days:

- `prev_daytime_weakness = max(-prev_daytime, 0)`: standardized FN-minus-TP difference `+0.480`, positive in 10/10 years;
- `prev_afternoon_weakness = max(-prev_afternoon, 0)`: `+0.325`, positive in 10/10 years;
- `prev_last_hour_weakness = max(-prev_last_hour, 0)`: `+0.412`, positive in 10/10 years.

In the strongest-weakness quartile, incumbent high-open recall falls to:

- full-day weakness: `0.425`;
- afternoon weakness: `0.510`;
- last-hour weakness: `0.441`.

The raw signed versions of these returns already exist in the incumbent feature set. Therefore the evidence does **not** justify adding a new information source. It justifies testing whether the current single linear slope is misspecified on the negative-return side.

Financial interpretation: after a weak China session, part of the next opening process behaves like an asymmetric rebound/auction reset. A linear term forces the response to be the mirror image of the positive-return side. A negative-part basis term allows a separate slope only when the prior China path is weak, without changing causal timing or introducing a calendar route.

Mathematically, retaining raw return `x` and adding `w=max(-x,0)` gives a continuous piecewise-linear effect:

- for `x >= 0`: contribution remains `βx`;
- for `x < 0`: contribution becomes `(β-γ)x`.

This is the minimum-capacity representation of the supported asymmetry.

Verdict: `supported_and_admitted_to_phase2`.

## Phase-2 scope decision

Only H6 may generate new candidates. Phase 2 must keep fixed:

- `StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver=highs)`;
- the 13 incumbent direction features;
- target `gap`;
- decision rule `prediction >= 0`;
- 2016–2025 expanding natural-year OOF selection;
- no 2026 access.

The bounded candidate family is frozen separately in `docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json`.

`2026-01-05..2026-08-21` remains sealed repeat-blackbox evidence only. Post-2026-08-21 remains unread true-fresh evidence. Production authority remains false.
