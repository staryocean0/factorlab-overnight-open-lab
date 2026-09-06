# 2026-09-06 Cloud Research Summary — CSI1000 Overnight Open

## Executive status

This session continued the bounded next-session CSI1000 overnight-open research under the repository's `strategy-slice-rebuild` evidence discipline.

The original frozen baseline remains the operational research baseline. A globally replaced clock-aware signed-gap model is **not promoted**, because its 2019-2020 repeat-audit improved IC and magnitude error but reduced sign hit. Root-cause diagnostics show that the clock-aware model is primarily a **magnitude / shock-intensity estimator**, especially when China reopens after multiple completed US sessions, rather than a uniformly better direction estimator.

A new **two-head direction/magnitude candidate** has therefore been frozen for fresh local validation only:

- direction head: original frozen baseline Ridge, alpha = 1.0;
- magnitude head: absolute value of the frozen clock-aware signed-gap Ridge, alpha = 100.0;
- recombination for secondary signed-gap reporting: baseline direction sign × clock magnitude;
- selected candidate SHA256: `76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f`;
- 2019-2020 is already consumed and must not be used to promote or retune this architecture;
- only local 2021-2025 can provide fresh confirmation.

Production authority remains `false`.

## 1. Frozen baseline reproduced

The historical baseline uses 2015-2018 for fitting and 2019-2020 as the frozen holdout.

Baseline holdout receipt:

- `n_train = 952`
- `n_test = 485`
- Ridge IC = `0.4569824814721589`
- sign hit = `0.7195876288659794`
- R2 = `0.16075322424988725`
- historical `us_nasdaq_ic = 0.484159954330252`

The repository validator and existing tests passed during all successful research workflows.

## 2. Causal US-clock repair

The key mechanism correction was to stop treating the last US daily return as if it always represented the complete information interval between two China opens.

For China session `D` with previous China session `P`, the clock-aware features use all completed US sessions between the two China information sets:

- `us_nasdaq_interval = last_US_close_strictly_before_D / last_US_close_strictly_before_P - 1`
- analogous VIX interval change;
- `us_session_count` = number of intervening completed US sessions.

This implements two important causal cases:

1. zero new US sessions: interval return is zero, so stale US news is not repeated;
2. multiple new US sessions: the full cumulative move is used instead of only the last US daily return.

On 2015-2018 development data:

- zero-new-US-session share ≈ `6.46%`;
- more-than-one-US-session share ≈ `2.15%`;
- original `us_nasdaq` correlation with gap ≈ `0.4233`;
- clock interval NASDAQ correlation with gap ≈ `0.4601`.

## 3. Frozen clock-aware signed-gap candidate

A bounded family of 24 attempts was preregistered before opening the 2019-2020 holdout: six feature sets × four Ridge alphas.

The selected development candidate was:

- feature set: `clock_holiday_interaction`;
- Ridge alpha = `100.0`;
- 16 frozen features;
- SHA256: `c2df5d9acdd9d970288ae8f990834d8b91495695b4e95bde0b82f88b160da12e`.

2015-2018 time-ordered CV:

| Metric | baseline | clock candidate |
|---|---:|---:|
| year-equal mean IC | 0.5155 | 0.5734 |
| year-equal mean sign hit | 0.6845 | 0.6873 |
| pooled OOF IC | 0.4896 | 0.5906 |
| worst-year IC | 0.4230 | 0.4839 |

A more complex piecewise candidate had a higher IC but failed the preregistered sign-quality gate and was correctly rejected.

## 4. 2019-2020 repeat-audit result: no global promotion

The first holdout execution encountered comparator-contract assertions after the holdout had already been programmatically opened. The holdout was therefore marked consumed. Subsequent successful execution was explicitly classified as a **repeat audit**, with the frozen candidate unchanged.

Successful repeat-audit result, 2019-2020:

| Metric | frozen baseline | clock candidate | delta |
|---|---:|---:|---:|
| IC | 0.45698 | 0.53164 | +0.07466 |
| sign hit | 71.96% | 71.13% | -0.82 pp |
| R2 | 0.16075 | 0.25465 | +0.09390 |
| MAE | 0.003949 | 0.003889 | -0.000061 |
| RMSE | 0.007950 | 0.007492 | -0.000458 |

The preregistered joint promotion gate required both IC and sign hit to beat the frozen baseline. Therefore `strict_baseline_win = false` and the global signed-gap replacement is not promoted.

The historical `majority_down_hit` field was also reconciled: there is one exact-zero gap in the 485-row holdout. The historical field equals the `gap <= 0` share, while a strict `gap < 0` calculation is lower by one sample. The legacy field is not corrupt.

## 5. Root cause of the sign / magnitude conflict

Fixed post-hoc slices were used only for diagnosis, never for promotion or parameter selection.

### Ordinary opens: |gap| <= 30 bp, n = 296

- baseline sign hit = `66.22%`
- clock sign hit = `64.86%` → `-1.35 pp`
- baseline IC = `0.3861`
- clock IC = `0.3885` → almost no gain

The overall sign loss is concentrated here.

### Tail opens: |gap| > 30 bp, n = 189

- baseline sign hit = `80.95%`
- clock sign hit = `80.95%` → no loss
- baseline IC = `0.4912`
- clock IC = `0.5770`
- RMSE: `0.01209 -> 0.01128`

The clock mechanism materially improves magnitude/ranking where the overnight ledger actually cares about large high/low opens.

### Exactly one new US session, n = 441

- baseline IC = `0.5184`
- clock IC = `0.5167`
- baseline sign hit = `72.34%`
- clock sign hit = `70.75%`

There is no reason to globally replace the baseline in the ordinary one-US-session regime.

### Multiple new US sessions / holiday reopen, n = 12

- baseline IC = `0.4114`
- clock IC = `0.7177`
- baseline sign hit = `75.00%`
- clock sign hit = `83.33%`
- RMSE: `0.02806 -> 0.02249`

This is the most mechanism-consistent improvement, although sample size is small.

## 6. Simple clock-state gate was tested and rejected

A causal gate was frozen without a grid search:

- `us_session_count == 1` → baseline;
- otherwise → clock model.

It was retrospectively checked on 2016-2018 time-ordered OOF only.

Result: **not corroborated**.

Year-equal means:

- baseline: IC `0.5155`, sign `0.6845`;
- clock model: IC `0.5734`, sign `0.6873`;
- gate: IC `0.5719`, sign `0.6735`.

On the 64 exceptional-clock OOF observations (`us_session_count != 1`):

- baseline IC = `0.0294`, sign = `65.63%`;
- clock IC = `0.7147`, sign = `53.13%`.

This is the decisive structural finding: exceptional-clock information contains very strong **shock magnitude/ranking information**, but its direction is not stable enough to replace the direction model.

## 7. Two-head direction / magnitude architecture

The next architecture therefore separates the two statistical tasks.

Direction is kept fixed to the original baseline. Only magnitude is allowed to use clock-aware information.

A bounded two-candidate family was tested on 2015-2018 time-ordered OOF only:

1. `abs_frozen_clock_signed_prediction` — reuse the frozen clock signed-gap model and take `abs(prediction)` as magnitude;
2. direct Ridge(alpha=100) fit on `abs(gap)` using the same clock features.

Candidate 1 passed; candidate 2 failed the preregistered magnitude-error gate.

### Selected two-head candidate

SHA256: `76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f`

2015-2018 year-equal OOF:

| Primary task metric | baseline | selected two-head |
|---|---:|---:|
| direction hit | 0.684512 | 0.684512 |
| corr(|gap|) | 0.443940 | 0.526659 |
| MAE(|gap|) | 0.002926 | 0.002591 |
| RMSE(|gap|) | 0.004323 | 0.003835 |
| worst-year corr(|gap|) | 0.385046 | 0.429486 |

Direction hit is identical by construction. Magnitude MAE and RMSE improve in each of 2016, 2017 and 2018.

Pooled OOF magnitude:

- baseline corr(|gap|) = `0.46859`;
- selected = `0.57254`;
- baseline MAE(|gap|) = `0.002923`;
- selected = `0.002588`;
- baseline RMSE(|gap|) = `0.004515`;
- selected = `0.003947`.

Secondary recombined signed-gap IC is slightly lower (`0.4896 -> 0.4794`) while signed MAE/RMSE improve. This reinforces why direction and magnitude should be evaluated as separate primary tasks rather than forcing one signed-gap statistic to represent both.

## 8. Fresh-validation boundary

The two-head architecture was motivated by diagnostics performed after the 2019-2020 holdout had already been consumed. Therefore it cannot obtain fresh-OOS authority from any 2015-2020 result.

The next valid evidence step is fixed:

- refit both fixed heads on 2015-2020 **before opening any 2021+ validation target**;
- validate exactly once on local 2021-2025;
- no feature, alpha, threshold, calendar-rule or magnitude-head search after opening 2021-2025;
- primary gate is direction hit plus magnitude correlation / MAE / RMSE, not trading return;
- passing local confirmation still does not grant production authority automatically.

See `docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json`.

## 9. Repository governance gap

`docs/governance/package_scope.json` requires a private repository. The cloud
session observed `visibility=public` and recorded it as a governance gap. The
local controller restored `visibility=private` on 2026-09-06 before writing the
2021-2025 receipt. That closes the live mismatch; it does not rewrite the
historical cloud-session observation.

## 10. Local 2021-2025 confirmation

The frozen two-head candidate was refit on 2015-2020 and then opened once on
2021-2025. It **passed** the preregistered local confirmation gate.

Receipt: `docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json`

Primary pooled result: direction hit identical at 0.693069; magnitude
correlation 0.319940 -> 0.521871; MAE 0.002417 -> 0.002400; RMSE 0.005410 ->
0.005094. Correlation is positive in every year 2021-2025, and both error
metrics beat baseline in 3 of 5 years. Production authority remains false.

## 11. Local 2026 direction challenge

The frozen Median direction successor was refit on 2015-2025 and then opened
once on 2026-01-05 through 2026-08-21. Cloud execution could not open this
window because the bounded repository still has no raw 2021+ rows. The local
controller used the same annotated panel, DataHub 1m export and FRED prints as
the 2021-2025 confirmation. The window passed both the raw-hit and robust
layers.

Receipt: `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`

Primary pooled result: direction hit 0.642857 -> 0.720779; correct count 99 ->
111; balanced accuracy 0.646160 -> 0.725148; recall_up 0.518987 -> 0.556962;
recall_down 0.773333 -> 0.893333. McNemar p on 20 disagreements is 0.011818 and
is uncertainty-only. Production authority remains false. Post-2026-08-21 was
not opened.

## Current research decision

1. **Retain the original frozen signed-gap baseline as the baseline.**
2. **Do not promote the global clock-aware signed-gap replacement.**
3. **Reject the simple clock-state full-model gate.**
4. **The two-head magnitude head is locally confirmed on 2021-2025:** `abs(clock_prediction)`.
5. **The Median direction successor is locally robustly confirmed on 2026-01-05 through 2026-08-21.** It is eligible only for a separate research-baseline review as the two-head direction head.
6. **2019-2020, 2021-2025 and 2026-01-05_to_2026-08-21 are consumed for these identities; do not retune on them.**
7. **Production authority remains false pending a separate production review.**
