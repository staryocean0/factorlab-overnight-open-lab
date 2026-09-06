# Direction-head objective experiment — 2026-09-06

## Decision

The bounded direction-objective family was executed successfully on GitHub Actions run `34012509781`, attempt 3, after repository visibility became public and public-runner access became available.

The candidate family and script were unchanged from the two earlier zero-step infrastructure failures.

**Selected retrospective candidate:** `median_quantile_sign`.

Scientific status:

`retrospective_direction_candidate_waiting_new_unseen_local_challenge`

Production authority remains `false`.

## Why this experiment existed

The existing Ridge direction head fits signed `gap` with squared error and then uses the sign of the conditional-mean estimate. The financial task, however, is high-open versus low-open classification. Under equal per-day sign-misclassification cost, the conditional median or direct sign probability is mathematically closer to the decision boundary than the conditional mean.

The frozen family therefore changed only the objective, not the 13 causal features:

1. comparator: Ridge mean-sign;
2. candidate: 0.5 Quantile / conditional-median sign;
3. candidate: Logistic sign probability.

No alpha/C grid, quantile search, threshold search, class weighting, feature changes or return optimization were allowed.

## Expanding natural-year OOF result

Five fixed folds were used: 2015→2016, 2015-16→2017, 2015-17→2018, 2015-18→2019, 2015-19→2020.

Pooled 2016-2020 OOF (`n=1214`):

- Ridge direction hit: `0.699341`
- Median Quantile direction hit: `0.718287`
- Logistic direction hit: `0.705931`
- Median Quantile correct-count increment versus Ridge: `+23`

Year-equal mean direction hit:

- Ridge: `0.699341`
- Median Quantile: `0.718221`
- Logistic: `0.705712`

Median annual direction-hit deltas versus Ridge:

- 2016: `+3.306 pp`
- 2017: `+9.836 pp`
- 2018: `-1.235 pp`
- 2019: `+0.413 pp`
- 2020: `-2.881 pp`

Median Quantile therefore satisfies the preregistered admission gate: higher year-equal mean hit, positive total correct increment, improvement in 3/5 years, and nonnegative median annual delta. Logistic improves only 2/5 years and is rejected.

Authoritative receipt:

`docs/research/cloud_session_20260906_direction_head_dev_receipt_v1.json`

Frozen candidate:

`docs/governance/cloud_session_20260906_direction_head_selected_v1.json`

Candidate spec SHA256:

`9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`

## Important robustness caveat

The Median candidate is **not** yet a globally better direction model.

Pooled balanced accuracy changes from Ridge `0.705223` to Median `0.697070`, while AUC is essentially flat (`0.764719` vs `0.764337`). The Median model predicts the high-open side only `36.74%` of OOF days versus Ridge `46.87%`; actual high-open share is `36.90%`.

This means the hit-rate gain partly comes from a more conservative sign boundary / better alignment with the prevailing base rate, not from a clear improvement in score ranking across both classes.

The yearly evidence reinforces this concern: the Median advantage is larger in low-high-open-prevalence years and weaker in high-high-open-prevalence years. Across the five development years, the correlation between actual high-open share and Median-minus-Ridge hit-rate delta is approximately `-0.757`.

That relationship is post-hoc diagnostic evidence only. It is not a new threshold, gate or parameter.

## Next valid evidence step

Do not use 2021-2025 to promote this direction candidate. That window was already consumed by the parent two-head architecture cycle before this direction objective was selected.

The next challenge is frozen independently on 2026-01-05 through 2026-08-21:

`docs/governance/cloud_session_20260906_direction_2026_fresh_protocol_v1.json`

Both fixed direction heads must be refit on 2015-2025 **before** opening 2026 target values.

The 2026 protocol distinguishes:

- raw-hit confirmation: the Median model truly gets more individual days correct;
- robust confirmation: it also avoids the development-period base-rate concern by not losing balanced accuracy and by retaining >50% recall on both high-open and low-open sides.

Only robust confirmation makes the Median direction head eligible for a separate research-baseline replacement review.

The already confirmed clock-aware magnitude head is not reopened or retuned in this direction challenge.
