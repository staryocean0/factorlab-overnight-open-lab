# Direction-head pre-analysis — 2026-09-06

## Research question

The locally confirmed two-head architecture materially improved overnight-gap magnitude estimation on fresh 2021-2025 data while preserving the original Ridge direction decision exactly. The remaining modeling bottleneck is therefore the high-open / low-open direction head.

This branch asks one narrow question:

> Can a loss function that is mathematically aligned with sign prediction improve direction accuracy without changing the existing causal feature set?

No new market feature, calendar exception, external data source, direction threshold, or magnitude-head rule is introduced in this experiment.

## Why the current Ridge objective may be misaligned

The current direction head fits `gap` with squared-error Ridge and classifies by `prediction >= 0`. Squared error targets the conditional mean. Large overnight gaps receive disproportionate weight, so a small number of tail observations can shift the conditional mean even when the majority sign around zero is unchanged.

The financial question is binary: whether the next CSI1000 open gap is nonnegative or negative. Under equal misclassification cost and negligible point mass exactly at zero, the Bayes sign decision is governed by whether `P(gap >= 0 | X)` exceeds 0.5. Two low-capacity objectives map naturally to that problem:

1. **Conditional-median regression**: estimate the 0.5 conditional quantile and classify by whether the predicted median is nonnegative. This is robust to large response tails relative to squared error and directly asks where half of the conditional gap distribution lies.
2. **Logistic sign classification**: estimate `P(gap >= 0 | X)` directly and use the fixed 0.5 threshold. No threshold search is permitted.

Predictive quantile regression is an established method for stock-return distribution forecasting, including conditional median predictability. Recent China/US spillover evidence also continues to show that US shocks are absorbed quickly by the next A-share trading day and can be state dependent. This branch intentionally does **not** add spillover features so that any result isolates the objective-function change rather than feature expansion.

References used only for mechanism/method motivation:

- Maynard & Shimotsu et al., "Inference in predictive quantile regressions", Journal of Econometrics, 2024/2025 publication cycle, predictive median/quantile stock-return regressions.
- Huang, Tian & Shen, "Characteristics and mechanisms of the U.S. stock market spillover effects on the Chinese A-share market", International Review of Financial Analysis 87 (2023), 102644.
- Yuan, Long, Li & Zhao, "Asymmetric connectedness in the Chinese stock sectors: Overnight and daytime return spillovers", Pacific-Basin Finance Journal 89 (2025), 102585.

## Evidence boundary

- 2015-2020 is consumed development material for this new direction branch.
- 2019-2020 is not a fresh holdout anymore and may be used only as development material here.
- 2021-2025 is already consumed by the confirmed two-head identity but is **not used at all** for candidate construction, ranking, or corroboration in this cloud experiment.
- 2026+ remains unopened in this repository and is reserved for a future local challenge if a nontrivial direction successor is frozen.

## Candidate family

All candidates use exactly the existing 13 baseline direction features and the same causal rows/missing-data mask.

- `ridge_mean_sign`: frozen comparator, `StandardScaler + Ridge(alpha=1.0)`, target `gap`, sign at zero.
- `median_quantile_sign`: `StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")`, target `gap`, sign at zero.
- `logistic_sign`: `StandardScaler + LogisticRegression(C=1.0, L2, lbfgs)`, target `gap >= 0`, probability threshold fixed at 0.5.

No alpha/C grid, no class weighting, no threshold tuning, no feature selection, no year-specific rule.

## Evaluation design

Use expanding natural-year OOF tests:

- fit 2015 -> test 2016;
- fit 2015-2016 -> test 2017;
- fit 2015-2017 -> test 2018;
- fit 2015-2018 -> test 2019;
- fit 2015-2019 -> test 2020.

Primary metric: direction hit rate. Secondary diagnostics: balanced accuracy, ROC AUC from each model's continuous score, and correct-count deltas versus the frozen Ridge comparator.

A nontrivial successor is admissible only if, across the five OOF years:

- year-equal mean direction hit is strictly above Ridge;
- total correct-count increment is positive;
- at least 3 of 5 years have a strictly positive hit-rate delta;
- median annual hit-rate delta is nonnegative.

If neither candidate passes, the direction head remains the frozen Ridge baseline. If a candidate passes, it is only a retrospective research successor waiting for a new unseen local challenge; it receives no fresh-OOS or production authority from 2015-2020.
