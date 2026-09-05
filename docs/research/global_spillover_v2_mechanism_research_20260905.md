# Global spillover v2 mechanism research — 2026-09-05

## Question

The v1 candidate `C1_unabsorbed_us_closure_accrual` improved 2019-2020 holdout IC from 0.45698 to 0.49136. Before interpreting that as an economic mechanism, v2 asks whether the gain is genuinely caused by foreign information accumulated while China is closed, or whether adding a feature highly correlated with the existing `us_nasdaq` / `us_vix_chg` simply changes Ridge regularization geometry.

This round is diagnostic only. The 2019-2020 holdout is already consumed. No result can replace the baseline or grant production authority.

## Literature support for the mechanism prior

1. Bao, Guo, Peng & Rao (2023), *International Review of Financial Analysis*, “Trading gap in holidays and price transmission: Evidence from cross-listed stocks on the A-share and H-share markets”, DOI 10.1016/j.irfa.2023.102616. Mainland-China holidays create non-overlapping trading gaps versus Hong Kong. H-share price movements during the A-share closure are positively associated with post-holiday A-share drift, and the association is stronger for longer non-overlapping holidays. This directly motivates isolating information that arrives after the last China close but before reopening rather than only taking the final foreign daily return.
   Source: https://www.sciencedirect.com/science/article/pii/S1057521923001321

2. Yang & Qiu (2026), “When Local Markets Close but the World Keeps Trading: Global Information Absorption at Market Reopening”. Using exchange-calendar differences, the study reports that foreign returns accumulated during verified local-market closures are strongly reflected in reopening-day returns relative to matched pseudo-closures. This is recent working-paper evidence, so it is used as mechanism motivation rather than authority.
   Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7248259

3. Zhang (2025), *Journal of Banking & Finance*, “International information flow and market quality”, DOI 10.1016/j.jbankfin.2025.107420. Non-overlapping foreign holidays are used to identify disruptions in international information flow. The evidence supports the premise that foreign markets are an economically meaningful information-production channel rather than a purely contemporaneous correlation proxy.
   Source: https://www.sciencedirect.com/science/article/abs/pii/S0378426625000408

4. “Overnight information and stochastic volatility: A study of European and US stock exchanges” documents the general mechanism that price-sensitive information accumulates during non-trading periods, with weekends and holidays creating longer information windows than ordinary weeknights. This supports measuring the whole non-trading information window rather than treating all close-to-open intervals as equal length.
   Source: https://www.sciencedirect.com/science/article/pii/S0378426607001811

## Why a placebo is mandatory

In v1, the cumulative-US feature is almost the same as the baseline one-day US return on ordinary sessions. With `StandardScaler + Ridge(alpha=1)`, adding a near-duplicate feature can alter the effective shrinkage applied to that economic direction even if no new information is introduced. Therefore a zero-information duplicate placebo is required before giving the v1 gain a causal/economic interpretation.

The v2 preregistration freezes three distinct objects:

- **C1 cumulative replay:** reproduces the v1 feature set exactly.
- **C2 exact-duplicate placebo:** adds exact copies of `us_nasdaq` and `us_vix_chg`; any gain here is purely model geometry because the information set is unchanged.
- **C3 incremental-information-only:** adds `cumulative_return - final_US_session_return`; this is the genuinely new part of the foreign information window.

C4/C5 separate NASDAQ from VIX. C6/C7 localize the new information to long-holiday versus shorter/non-holiday multi-US-session windows. None of those subset variants may become runtime routing rules from this consumed holdout.

## Frozen financial interpretation rules

- If C3 does not beat C0, the v1 “closure accumulation” interpretation is rejected or unproven even if C1 still looks good.
- If C2 beats C0, duplicate-feature regularization is a real artifact channel and must be disclosed.
- A positive C3 is genuine retrospective progression material, but still not fresh OOS and not a baseline replacement.
- Existing `|gap| = 30bp` ordinary/tail cut is reused only as a diagnostic partition; no new threshold search is allowed.
- Additive squared-error improvement is decomposed by holiday/non-holiday, one-US-session/multi-US-session, ordinary/tail, and 2019/2020 so that a few reopening crashes cannot silently create the entire result.
