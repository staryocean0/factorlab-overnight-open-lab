# OFP-E3 portfolio-risk adapter v1 — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_c1_intraday_portfolio_risk_abstention_v1`

Phase: retrospective intraday portfolio utility/risk diagnostic only.

Development window: `2015-01-05..2020-12-31`.

## Frozen identity

Consumer is the immutable REAKA account snapshot at commit `af2e478aaff5c8ef7f753424b57fd2d19019f248`, strategy `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`, account policy `N30_equal_backfill_unconstrained`, with the 14:30 and 14:45 account variants evaluated jointly.

Upstream signal is validated C1 only:

`c1_action = sign(-(gap / rvol20) * (r20 / (sqrt(20) * rvol20)))`.

Comparator exposure over 09:35→09:50 is always one. Candidate exposure is zero iff `c1_action < 0`, otherwise one. No threshold, magnitude bucket, clock choice, alternative horizon or additional upstream product was searched.

## Execution integrity

The locally uploaded price pack was accepted only as a mechanical carrier. It contains exact previous-day 15:00, current-day 09:35 and 09:50 QFQ signal prices for the union of symbols carried by the frozen accounts. The carrier records no feature engineering, target engineering, scientific diagnostic, portfolio return calculation, C1 calculation, BLACKBOX execution or post-2020 rows.

Cloud execution independently downloaded the frozen consumer `holdings.parquet`, `portfolio_daily.parquet` and snapshot manifest from the pinned consumer commit, verified the frozen SHA/canonical identities, verified all E3 carrier shard hashes and boundaries, reconstructed C1 from the accepted 2015–2020 factor carrier, and reconstructed the exact frozen portfolio interval formula.

No account execution, costs, fills, account-path mutation or 2021–2025 rows were opened.

## Sufficiency result

The frozen complete-case rule requires every carried holding on an account-day to have all three exact QFQ prices. Missing exact clocks make that account-day incomplete; nearest-clock substitution, forward/back fill and resampling are forbidden.

Under that rule, annual sufficiency fails for both frozen account clocks in multiple years. The accepted diagnostic therefore returns:

**`E3_DEV_INSUFFICIENT`**

This is an evidence-sufficiency outcome, not a scientific FAIL of C1 or the consumer portfolio. Because sufficiency fails before progression adjudication, observed progression statistics on the incomplete subset do not authorize selection, rejection, rescue, threshold changes, alternate price handling or a successor.

## Decision

**Close E3 v1 at Development as `INSUFFICIENT`; no successor is authorized.**

The exact-price missingness is part of the frozen causal/exact-clock evidence contract. It must not be repaired after seeing outcomes with alternate clocks, fill rules, stale prices, alternate vendor prices or relaxed complete-case accounting under this identity.

No reusable BLACKBOX query is created. BLACKBOX ledger remains unchanged.

`production_authority=false`.
