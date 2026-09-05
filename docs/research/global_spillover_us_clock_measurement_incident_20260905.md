# US information-clock measurement incident — 2026-09-05

## Status

`measurement_gap_blocks_clean_cumulative_US_mechanism_test`

This incident does **not** invalidate the frozen baseline receipt itself. The baseline uses already-materialized panel features and replays exactly. It does invalidate the clean economic interpretation of v1 `C1_unabsorbed_us_closure_accrual`, because C1 was reconstructed from the packaged US level series and that series is not sufficiently complete to reproduce the baseline daily US features on every row.

## Discovery chain

1. v1 C1 added a cumulative NASDAQ/VIX return between the last packaged US close before the previous China session and the last packaged US close before the target China session.
2. v2 introduced an exact-duplicate placebo and an `extra = cumulative - baseline daily feature` decomposition.
3. On purported one-US-session windows, `extra` was materially nonzero. That should be impossible if both objects use the same source calendar and transform.
4. The first v2 economic adjudication (Actions run `33968348582`) was therefore invalidated before promotion.
5. Independent-calendar diagnostics then showed that the panel features are ordinary percentage changes on the overwhelming majority of rows, but the packaged level history has missing intermediate US trading dates.

## Reproducibility evidence

Actions run `33968654230` passed package validation, 8 tests, frozen baseline replay and v1 replay before running the clock diagnostics.

For the full panel:

- reconstructed NASDAQ daily percentage return is exactly equal to panel `us_nasdaq` within `1e-10` on `96.374829%` of rows;
- reconstructed VIX daily percentage change is exactly equal to panel `us_vix_chg` within `1e-10` on `96.369863%` of rows;
- lagged or led transforms have near-zero correlation, so this is not a systematic one-day shift;
- the mismatch dates cluster where the packaged level sequence jumps across an intermediate US trading session that the panel feature nevertheless reflects.

Concrete examples:

- China `2018-12-28`: packaged NASDAQ levels jump `2018-12-24 6192.92 -> 2018-12-27 6579.49`, which would imply `+6.2421%`; panel `us_nasdaq=+0.3834%`. The panel therefore used an intermediate prior US level not present in the packaged level sequence.
- China `2020-09-10`: packaged levels jump `2020-09-04 11313.13 -> 2020-09-09 11141.56`, implying `-1.5166%`; panel `us_nasdaq=+2.7091%`. The missing intermediate date changes both sign and economic meaning.
- China `2019-01-24`: packaged VIX levels jump `2019-01-18 17.80 -> 2019-01-23 19.52`, implying `+9.6629%`; panel `us_vix_chg=-6.1538%`, again proving the panel daily feature was computed from an intermediate level absent from this package.

## Scientific consequence

The original v1 cumulative feature can include a foreign return that occurred **before** the previous China session and was therefore already absorbable by A shares. It is causal in the weak sense of using only past dates, but it is not a clean representation of `foreign information unabsorbed since the previous China session`.

Therefore:

- v1 C1 numerical performance remains a reproducible retrospective observation;
- its label/financial mechanism is withdrawn pending a complete point-in-time US daily level calendar;
- invalid v2 run `33968348582` cannot be used as economic evidence;
- no corrected cumulative-US model will be run from the incomplete package;
- the next valid test requires the complete pre-2021 NASDAQ and VIX source rows that generated the panel, or an equivalent content-addressed PIT reconstruction approved by the local controller.

The repository contract still forbids downloading new market rows in this cloud round, so this incident is closed as a measurement/data-package gap rather than silently fetching replacement history.

## Authority

No fresh OOS, baseline replacement, strategy selection, routing, registry mutation, or production authority is granted.
