# High-open recall Phase-2 cloud review — 2026-09-06

## Review decision

Cloud review accepts local OHR-02 as a valid development-only selection execution and accepts its scientific result:

**`no incremental successor beyond the baseline`**.

The incumbent remains `median_quantile_sign` with spec SHA256 `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`.

No Phase-2 candidate is frozen as a successor. The 2026-01-05 through 2026-08-21 repeat blackbox must therefore remain unopened for this branch and OHR-03 must not start.

## Execution integrity

Frozen execution identity was `5c734f36f49a80dc46ebdd67b66895740c807b1e`.

Local result commits:

- first OHR-02 output: `32e976cfded98463677d2c74b09f33de9c99b761`;
- independent Codex replay note: `c29ab629ddb4c7bb0552effb5dc46f78643881b7`.

Cloud compared `5c734f36..c29ab62`. Only the allowed aggregate/result files changed: Phase-2 receipt, Phase-2 data-usage declaration, communication log and index. The frozen family, selector and boundary tests did not change.

The independent replay reports all three commands exit 0, pytest `11 passed`, family/selector/tests unchanged relative to the execution freeze, and byte-identical receipt/data-usage outputs. Receipt SHA256 was `6a65180eaef2b1ef38ed5da52504f3f11018b802cc0aee2d7b83328938c113f5`.

The receipt records:

- development end `2025-12-31`;
- OOF years 2016–2025, `n=2426`;
- `eligible_candidate_count=0`;
- `selected=null`;
- decision `retain_incumbent_do_not_open_repeat_blackbox`;
- `2026_rows_loaded=false` and `2026_blackbox_opened=false`;
- no parameter, quantile, threshold or trading-return search;
- 2015–2020 reconstruction max-abs 0 for all frozen fields;
- no raw development rows written to the bounded repository;
- production authority false.

## Candidate adjudication

Incumbent pooled development OOF:

- direction hit `0.7176422093981863`;
- balanced accuracy `0.7010188647956266`;
- high-open recall `0.6260593220338984`;
- low-open recall `0.7759784075573549`;
- >10bp high-open recall `0.6600331674958541`;
- >30bp high-open recall `0.7119205298013245`.

### `weakness_daytime_piecewise`

Rejected. High-open recall fell to `0.621822`; direction hit fell to `0.714757`; balanced accuracy fell to `0.697888`; >30bp high-open recall also fell. Only 2/10 OOF years had positive recall-up delta.

### `weakness_afternoon_piecewise`

Rejected. High-open recall fell to `0.622881`; direction hit fell to `0.713108`; balanced accuracy fell to `0.696731`. Material-high-open recall did not deteriorate, but the primary recall target and non-sacrifice gates failed. Only 3/10 years improved recall-up.

### `weakness_last_hour_piecewise`

Rejected, but retained as diagnostic progression material. It is the only one-feature candidate that improves the primary high-open recall and both material-high-open recalls:

- high-open recall `0.626059 -> 0.634534`;
- >10bp recall `0.660033 -> 0.669983`;
- >30bp recall `0.711921 -> 0.718543`.

However it buys these gains by creating too many low-open false positives:

- direction hit `0.717642 -> 0.714345`;
- balanced accuracy `0.701019 -> 0.699858`;
- low-open recall `0.775978 -> 0.765182`;
- candidate-correct/incumbent-wrong = 22 versus incumbent-correct/candidate-wrong = 30;
- positive recall-up delta in only 5/10 years, below the frozen 6/10 gate.

This is **valid progression material but not a successor**. It suggests that prior last-hour weakness contains rebound information, while an unconditional negative-part slope applies that information too broadly.

### `weakness_three_horizon_piecewise`

Rejected. High-open recall rises only slightly to `0.627119`, while direction hit and balanced accuracy fall; only 4/10 years improve and >30bp recall deteriorates.

## Scientific interpretation

Phase 1 established a stable association between prior-China weakness and incumbent high-open false negatives. Phase 2 shows that the simplest causal representation of that association — an unconditional negative-part piecewise slope — is insufficient.

This does **not** justify threshold changes, extra hinge combinations, or opening the 2026 blackbox. Nor does it prove the underlying rebound mechanism is false. The last-hour result shows a real directionally useful effect, but its false-positive cost indicates missing conditional structure.

The next legitimate research question, if this branch continues, is:

> Under what causal pre-open state does prior last-hour weakness predict a rebound high open rather than continued/low opening weakness?

A new diagnostic phase must answer that question on 2015–2025 development material before any new candidate family is frozen. It should specifically compare the additional true positives and additional false positives created by the last-hour hinge and look for a small, financially interpretable conditioning state already available before the China open. It must not use 2026.

## Evidence boundary after review

- 2015-01-05..2025-12-31: consumed development material for this research branch;
- 2026-01-05..2026-08-21: remains sealed repeat-blackbox evidence; do not open because there is no frozen successor;
- post-2026-08-21: remains unread true-fresh evidence;
- OHR-03: not opened;
- production authority: false.
