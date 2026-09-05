# Global spillover v2 forensic conclusion — 2026-09-05

## Executive conclusion

The second round narrows, rather than broadens, the v1 result.

The v1 `C1_unabsorbed_us_closure_accrual` numerical improvement is reproducible, but it should **not** be promoted as a generic daily cumulative-US factor. A source-clock audit found that the packaged US level history omits a minority of intermediate US observations that were evidently available when the materialized panel features were produced. This makes an all-row `unabsorbed since the previous China session` label too strong.

However, fixed-prediction forensics show that those source-clock mismatch rows do **not** create the v1 gain. They hurt C1. The observed gain is overwhelmingly localized to the already-defined `holiday_reopen` rows. Therefore the surviving research object is a narrower mechanism hypothesis:

> When the A-share market is closed for a long holiday while foreign markets continue to price information, the cumulative foreign return over the closure may help explain the reopening gap beyond the final foreign daily return alone.

This is a retrospective mechanism hypothesis only. It is not a runtime holiday route, not a new baseline, and not fresh OOS evidence.

## Frozen numbers

Full 2019-2020 consumed holdout, n=485:

- C0 frozen baseline: IC 0.45698248, sign hit 71.96%.
- v1 C1: IC 0.49135679, sign hit 72.16%.

Source-clock exact subset, n=468:

- C0 IC 0.45715227.
- C1 IC 0.49785861.
- C0 sign hit 71.58%.
- C1 sign hit 73.29%.
- C1 vs C0 squared-error improvement: +0.00101736.

Source-clock mismatch subset, n=17:

- C0 IC 0.48349576.
- C1 IC 0.12401095.
- C0 sign hit 82.35%.
- C1 sign hit 41.18%.
- C1 vs C0 squared-error improvement: -0.00037975.

The mismatch rows therefore reduce, rather than manufacture, the C1 improvement.

## Where the gain actually lives

The fixed predictions were then decomposed without refitting or selecting a new policy.

`holiday_reopen`, n=12:

- C0 IC 0.41135245 -> C1 IC 0.69065702.
- sign hit 75.00% -> 83.33%.
- squared-error improvement +0.00188167.

Non-holiday, n=473:

- C0 IC 0.51805917 -> C1 IC 0.51690844.
- sign hit unchanged at 71.88%.
- squared-error improvement -0.00124406.

Even on the 456 non-holiday rows whose US source clock is exactly reconstructable, the squared-error change is negative (-0.00086431). Thus the current evidence does not support a generic ordinary-session cumulative-US feature.

## Measurement incident and endpoint audit

The packaged `us_nasdaq_vix.parquet` is sufficient to replay the frozen baseline because the baseline consumes already-materialized panel features. It is not complete enough to reconstruct those daily features on every row from source levels alone. Roughly 96.37% of panel rows match reconstructed percentage changes exactly; the rest reveal missing intermediate source observations.

For the 12 consumed-holdout `holiday_reopen` rows that drive the retrospective C1 gain:

- target-side panel daily US features align exactly on 12/12 rows;
- cumulative endpoint values recalculate exactly from stored start/end levels on 12/12 rows;
- the start and end dates selected by v1 are internally date-consistent on 12/12 rows;
- a corrected package-only endpoint audit establishes 11/12 rows;
- 2019-01-02 remains conservatively unresolved because 2019-01-01 is an intervening weekday and the package does not contain an authoritative US exchange-holiday calendar. The stored 2018-12-31 endpoint and cumulative return themselves recalculate exactly; the unresolved point is calendar sufficiency, not arithmetic.

The earlier v2 mechanism run `33968348582` is explicitly invalid as economic evidence because it mixed this source-clock mismatch into `cumulative - panel daily feature`. Its attractive output is retained only as an incident/counterexample.

## Literature consistency

Bao, Guo, Peng & Rao (2023), *International Review of Financial Analysis*, use non-overlapping A/H-share holidays and find that H-share price changes while mainland China is closed predict post-holiday A-share adjustment, with a stronger relationship for longer closures. This supports the economic premise that information generated while the local market is shut can be absorbed at reopening.

Yang & Qiu (2026) similarly study situations where local markets close while foreign markets continue trading and report concentrated foreign-information absorption on reopening. This is recent working-paper evidence and is treated as mechanism motivation, not validation authority.

The literature is therefore consistent with the observed holiday localization, but it cannot rescue the statistical limitations: only 12 holdout holiday cases were observed, the localization was discovered after the holdout had already been consumed, and one endpoint remains package-calendar unresolved.

## Next valid experiment

Do not tune another threshold on 2019-2020 and do not turn `holiday_reopen` into a runtime rule from these results.

The next valid experiment should be preregistered before opening new outcomes and should use complete point-in-time external calendars/levels. Its primary hypothesis should be the **foreign-information return accumulated over a predeclared A-share market closure**. The same causal clock should then admit additional economically closer channels in a bounded family, with priority:

1. SGX/FTSE China A50;
2. offshore RMB/CNH;
3. KOSPI pre-China-open price discovery;
4. Chinese commodity night-session information;
5. Japan and broad Europe only after proving incremental information beyond the above and US risk factors.

The local controller's genuinely unseen 2021-2025 period is the proper place to challenge a frozen candidate. Until that occurs, the frozen baseline remains the operational comparator.

## Scientific status

`holiday_closure_accumulation_retrospective_mechanism_hypothesis_waiting_complete_PIT_calendar_and_unseen_local_controller_confirmation`

Authority remains false for fresh OOS, baseline replacement, holiday runtime routing, production, and registry mutation.
