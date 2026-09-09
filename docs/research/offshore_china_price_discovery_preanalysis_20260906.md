# Offshore-China price discovery preanalysis — 2026-09-06

## Why a new information source is now justified

The bounded high-open-recall work has reached an information limit rather than a mere functional-form limit.

Phase 1 showed that prior China weakness is genuinely associated with missed high opens. Phase 2 then gave the existing Median head a minimal negative-side hinge. The last-hour version improved high-open recall and material-high-open recall, proving that a rebound channel exists, but it also created more false high calls and failed the total-hit / balanced-accuracy gates. OHR-04 then preregistered domestic conditioning variables and could not find a stable multi-year state that separated rescued high opens from new false highs.

Therefore the next scientific question is not whether to slice prior weakness more finely. It is whether there is **new causal information arriving after China closes** that reveals whether a weak session is being repriced upward or is continuing to weaken before the next China open.

## The price-discovery opportunity created by non-overlapping trading hours

The Chinese cash market closes well before the US regular session opens. US-listed ETFs whose underlying assets are Chinese equities continue trading while their home-market constituents are closed. In that interval their market prices can incorporate news, investor demand and market-maker fair-value expectations about the next reopening of the underlying Chinese market.

This is a standard international-ETF price-discovery mechanism rather than same-morning China leakage. The new protocol uses only completed US regular sessions after the prior China 15:00 close and before the current China 09:31 open.

The literature provides both motivation and a warning:

1. Ou (2023), *Price discovery or overreaction? A study on the reaction of Asia Pacific country ETFs to the US stock market*, Investment Analysts Journal, DOI 10.1080/10293523.2023.2208904. The study finds that US-listed Asia-Pacific ETF returns and the S&P 500 can predict next-home-market NAV returns and interprets ETF prices during non-overlapping hours as short-term expectations about the underlying market.
2. Levy and Lieberman (2013), *Overreaction of country ETFs to US market returns: Intraday vs. daily horizons and the role of synchronized trading*, Journal of Banking & Finance. During non-synchronized trading, US common-market returns can dominate country-ETF pricing. This means a raw China ETF return may mix China-specific price discovery with a US common factor.
3. Huang, Tian and Shen (2023), *Characteristics and mechanisms of the U.S. stock market spillover effects on the Chinese A-share market*, International Review of Financial Analysis 87, 102644. US return spillovers into A-shares are short-lived and become more prominent when the Chinese market has performed poorly, which is directly relevant to the rebound-versus-continuation problem.
4. Li and Zhang (2013/2014), *Spillover and Cojumps Between the U.S. and Chinese Stock Markets*. US price changes predict next-day Chinese closing-to-opening returns.
5. Alhaj-Yaseen et al. (2026), *The price of timing: Sequenced cross-listings and market discovery in Chinese ADRs*, Pacific-Basin Finance Journal 99, 103205. US-listed Chinese securities can lead next-day spillovers, with price-discovery leadership varying by listing structure and regime.
6. Chen, Li and Wu (2010), *Price Discovery for Segmented US-Listed Chinese Stocks: Location or Market Quality?*, Journal of Business Finance & Accounting 37(1-2), 242-269. Earlier evidence is more cautious and finds home-market leadership. This is useful because it prevents assuming that every US-listed China price is automatically informative.

The empirical question must therefore be answered with the project data rather than asserted from theory.

## Why ASHS and ASHR are the primary probes

The research target is CSI1000. The cleanest new market-state probes are US-listed ETFs holding mainland A-shares:

- **ASHS** — Xtrackers Harvest CSI 500 China A-Shares Small Cap ETF. It tracks CSI 500 and began in May 2014, so it covers the full 2015-2025 development interval. Its smaller-company exposure is directionally closer to CSI1000 than a large-cap China ETF.
- **ASHR** — Xtrackers Harvest CSI 300 China A-Shares ETF. It began in November 2013 and provides a larger-cap A-share price-discovery reference.

Their difference, `ASHS - ASHR`, is preregistered as a small/mid-cap relative offshore state. If US investors reprice smaller A-shares more positively than large A-shares after a weak China close, that is more directly relevant to CSI1000 than a generic Nasdaq move.

FXI and MCHI are retained only as broader China controls, and SPY is the US common-factor control. The point is not to search a long ETF list for the best backtest.

## Causal clock construction

For China trading day `D` with prior China trading day `P`, use only US regular sessions whose US trading date is at least `P` and strictly before `D`.

For each symbol and each such completed US session `s`, calculate its same-session return:

`r_s = close_s / open_s - 1`.

Then compound these session returns:

`r_post_cn = product(1 + r_s) - 1`.

Why use same-session open-to-close rather than the ordinary US daily close-to-close return?

- The US regular session opens after the Chinese 15:00 close, so its open-to-close movement is cleanly inside the new information interval.
- Ordinary US close-to-close returns contain an overnight portion that was partly observable before China closed and therefore mix stale and new information.
- Compounding same-session returns across a Chinese holiday measures repeated US-session price discovery while avoiding raw-price discontinuities from ETF splits across sessions.
- Existing clock-aware Nasdaq/VIX features already carry the broader cumulative completed-US-session shock. The new representation is deliberately different: it asks what US traders did **during the regular session while China was closed**.

SPY defines the expected US-session calendar. If SPY says a US session occurred but an ETF row is missing, the source row is incomplete and cannot silently become zero.

## Preregistered state representations

Only seven source representations are admitted to this diagnostic phase:

1. `ashs_session` — small/mid A-share offshore price discovery.
2. `ashr_session` — large/mid A-share offshore price discovery.
3. `ashs_minus_ashr` — small/mid versus large/mid A-share relative repricing.
4. `a_share_consensus = 0.5*(ASHS + ASHR)`.
5. `a_share_specific_vs_spy = a_share_consensus - SPY`.
6. `broad_china_specific_vs_spy = 0.5*(FXI + MCHI) - SPY`.
7. `china_etf_positive_breadth` — fraction of ASHS/ASHR/FXI/MCHI session returns above zero.

No ticker, weighting, threshold, interaction or provider may be added after seeing target diagnostics.

## Why subtract SPY

International ETF prices can move with the US market simply because the underlying home market is closed and US investors use broad US information to update fair value. A raw China ETF return can therefore be predictive without containing any China-specific information beyond the existing US factor.

The simple difference against SPY is not claimed to be a perfect beta residual. It is a low-capacity, preregistered control that asks whether the China-linked ETF moves more positively or negatively than the broad US market during the same completed regular session. If this difference is stable, a later family may consider a more formal train-only residual; if it is not stable, no residual model should be invented post hoc.

## What would count as mechanism evidence

The main development slice is deliberately targeted at the unresolved problem:

`incumbent predicts low` AND `prior last hour is weak`.

Within that slice, a useful offshore state should be larger on actual-high-open days than on actual-low-open days. For each source representation the diagnostic reports:

- pooled actual-up minus actual-down mean and median;
- quartile actual-high-open shares and counts;
- annual actual-up minus actual-down mean differences, 2016-2025;
- median annual difference;
- the same representation on the small OHR-04 disagreement set, comparing rescued highs with new false-high calls.

A representation may generate a later candidate family only if:

- the source/calendar integrity passes;
- the pooled difference has the expected positive sign;
- at least 6 of 10 annual differences have the expected sign;
- the median annual difference is positive;
- the top quartile has a higher actual-high-open share than the bottom quartile;
- the financial interpretation remains China-specific post-close price discovery rather than only a broad US-market effect.

The OHR-04 disagreement sample is supporting evidence only because it contains just 38 incumbent-down to candidate-up flips.

## Data-source discipline

The project must not select a data vendor by predictive performance. Before reading any target diagnostic, the local controller must freeze one provider/cache identity and record:

- provider;
- retrieval or export identity/date where available;
- raw/local file SHA256;
- whether OHLC is raw or adjusted and how same-session returns are constructed;
- per-symbol coverage and missing rows.

If the source is incomplete or its session clock cannot be verified, the correct result is `infrastructure_or_measurement_gap`, not a guessed fill.

Raw external rows remain local and are not committed to this bounded repository.

## Evidence boundary

All source admission and diagnostics end at `2025-12-31`.

`2026-01-05..2026-08-21` remains sealed repeat-blackbox evidence for this new research branch. It is not permitted in source choice, data cleaning decisions, feature definitions or mechanism admission.

Post-2026-08-21 remains unread true-fresh evidence.

Production authority remains false.
