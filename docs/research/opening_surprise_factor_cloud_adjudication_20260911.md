# Opening Surprise factor — cloud adjudication (2026-09-11)

## Identity

`overnight_open_surprise_factor_v1`

Receipt:

`docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`

Local execution commit:

`9ee4b6f23d634726f16ab8072b9c6130f6807193`

## Execution / boundary review

Cloud review accepts the local execution as procedurally valid:

- the local commit added only the frozen diagnostic receipt;
- the commit message used `[skip ci]`;
- `development_window == 2019-01-01..2020-12-31`;
- `target_rows_after_2020_loaded == false`;
- `reusable_blackbox_2021_2025_opened == false`;
- `candidate_family_search == false`;
- `threshold_search == false`;
- `trend_bucket_search == false`;
- `horizon_search == false`;
- `trading_return_optimization == false`;
- `auto_promotion == false`;
- production authority remains false.

The receipt source hashes for the frozen CSI1000 base panel, the 2015-2025 minute carrier, FRED NASDAQ/VIX, and admitted HKMA / SGX A50 endpoint products match their repository manifests.

## Scientific result

Decision:

**`NO_STANDALONE_OPENING_SURPRISE_PRODUCT_PROMOTION_STABILITY_FAILURE`**

The unconditional normalized coordinate

`opening_surprise_rvol = (observed_gap - frozen_V6A_expected_gap) / rvol20`

does not earn promotion as a stable reusable factor product from this development diagnostic.

The decisive evidence is stability, not the absence of any within-year fit improvement:

- in 2019 the standardized Opening Surprise coefficient is positive at all three frozen short horizons;
- in 2020 the coefficient is negative at all three frozen short horizons;
- pooled incremental explanatory power is effectively zero at 09:35→09:50 and remains very small at 09:35→10:05 and 09:35→10:35;
- pooled partial correlations are correspondingly near zero / small.

This is exactly the kind of result for which the factor-product program requires rejection of an unconditional product rather than post-hoc thresholding or regime slicing.

The positive-vs-negative raw future-return means are diagnostic only. They do not rescue the factor because the preregistered incremental test controls for raw opening gap and causal context, and the year-to-year sign reversal remains.

## Authority consequences

- OFP-A3 `opening_surprise_residual` is **not promoted** as a standalone validated coordinate.
- No 2021-2025 reusable BLACKBOX query is authorized for this identity.
- Do not search Opening Surprise thresholds, signs, tails, horizons, trend buckets, volatility buckets, or interactions as a rescue of this identity.
- The result is retained as negative / mechanism evidence: subtracting the frozen V6A expected gap from the observed gap does not produce a stable unconditional short-horizon factor on 2019-2020.
- V6A prediction authority is unaffected. This diagnostic tests post-open residual utility, not V6A next-open prediction quality.

## Next research direction

The preregistered product-shelf order already placed `prior_trend_context_x_core_opening_state` after the Opening Surprise diagnostic. That next identity is therefore allowed to open as an independent context-product experiment, **not** as a rescue or explanation of the failed Opening Surprise factor.

The next experiment will use continuous coordinates first:

- `trend20_rvol = r20 / (sqrt(20) * rvol20)`;
- `observed_gap_rvol = observed_gap / rvol20`;
- candidate increment: `trend20_rvol * observed_gap_rvol`.

It asks whether prior trend changes the short-horizon meaning of the observed opening gap after controlling for the two main effects and the same simple causal context. No up/range/down thresholds are authorized at this stage.

`production_authority=false`.
