# Opening Surprise factor preanalysis — 2026-09-10

## Research question

The new factor-product program needs to determine whether the deepest Overnight research creates useful information *after* the market opens, without pretending that Overnight information should explain the entire trading day.

The first candidate product therefore asks:

> Once the CSI1000 09:31 opening gap is observed, does the difference between the observed gap and the frozen V6A expected gap contain incremental information about the first 15–60 minutes of the post-open path beyond the raw gap and simple pre-open context?

This is a factor-information diagnostic, not a standalone trading backtest.

## Why surprise is more valuable than another raw bucket

A downstream timing or stock-selection strategy can cheaply observe:

- whether the market opened high or low;
- the raw gap size;
- a simple trailing trend;
- trailing volatility.

What it cannot cheaply reproduce is the *expected* opening state implied by the already-researched Overnight information set.

Two 50bp high opens can therefore be economically different:

- one may be almost fully explained by the pre-open information set;
- the other may be a large positive surprise relative to the expected open.

The factor-product hypothesis is that these two states should not automatically be treated as equivalent by downstream strategies.

## Frozen factor definitions

For day `t`:

- `expected_gap_t`: frozen V6A signed-gap prediction fit only on 2015-2018 and evaluated on 2019-2020;
- `observed_gap_t`: CSI1000 09:31 open relative to previous China 15:00 close under the existing Overnight gap contract;
- `opening_surprise_t = observed_gap_t - expected_gap_t`;
- `observed_gap_rvol_t = observed_gap_t / rvol20_t`;
- `opening_surprise_rvol_t = opening_surprise_t / rvol20_t`;
- `trend20_rvol_t = r20_t / (sqrt(20) * rvol20_t)`.

Rows with missing/non-positive `rvol20` fail complete-case admission. No epsilon floor is introduced.

The factor becomes available only after the opening observation is known. It has no pre-open trading authority.

## Development evidence boundary

Only `2019-01-01..2020-12-31` is opened for this diagnostic.

Why this window:

- V6A is fit only on 2015-2018;
- 2019-2020 is already consumed historical material and may be inspected in detail;
- 2021-2025 remains governed as the reusable aggregate BLACKBOX and must not be opened in detail for this new identity;
- no 2026 rows are needed or authorized.

The current V6A BLACKBOX PASS may motivate the program direction, but its hidden behavior may not define this factor or its thresholds.

## Short-horizon outcomes

The diagnostic intentionally avoids 15:00 close-to-close/full-day economics.

Factor availability is 09:31; a four-minute operational buffer is used before measuring downstream path information.

Frozen outcome clocks:

- `ret_0935_0950` — approximately 15 minutes after the 09:35 reference;
- `ret_0935_1005` — approximately 30 minutes;
- `ret_0935_1035` — approximately 60 minutes.

All are CSI1000 index-level research returns from exact 1-minute PIT/raw prices. They are information targets, not assumed executable fills.

## Incremental-information test

For each horizon, compare a fixed baseline linear diagnostic against the same diagnostic plus `opening_surprise_rvol`.

Baseline controls:

- `observed_gap_rvol`;
- `trend20_rvol`;
- `r1`;
- `prev_daytime`;
- `holiday_reopen`.

Candidate diagnostic adds exactly:

- `opening_surprise_rvol`.

Report:

- pooled and per-year partial correlation between `opening_surprise_rvol` and the future return after residualizing both on the baseline controls;
- baseline versus candidate in-sample diagnostic R² and delta-R²;
- standardized candidate coefficient sign/magnitude;
- complete-case counts;
- simple sign-conditioned future-return means for positive versus negative surprise as descriptive mechanism evidence.

These are mechanism diagnostics only. No trading costs, position sizing, entry thresholds, stop rules, regime routing, or downstream strategy PnL are optimized.

## Interpretation rule

This phase does **not** auto-promote a factor from one pooled metric.

The main agent must review whether:

- the incremental relationship is non-zero in a practically meaningful way;
- the coefficient direction is stable across 2019 and 2020;
- the effect is not confined to one horizon only;
- the factor adds information beyond the raw opening gap rather than merely restating it;
- sample sufficiency is adequate.

If supported, the next step is to freeze a bounded Opening Surprise factor family and only then decide whether an aggregate 2021-2025 reusable BLACKBOX query is warranted.

If unsupported, close this product without trying many arbitrary surprise thresholds, trend buckets, or horizon searches.

## Relation to future context products

Trend/volatility cross-products are deliberately postponed until the base surprise coordinate is understood.

If Opening Surprise survives, the preferred next context research is:

1. continuous trend context × surprise/open geometry;
2. volatility context × surprise/open geometry;
3. driver agreement/disagreement;
4. relative-index opening leadership.

This ordering prevents a large regime grid from hiding whether the core Overnight-derived residual contains useful information at all.

`production_authority=false`.
