# Legacy overnight-gap literature note

> **Scope notice (2026-09-08):** this file is the literature note for the historical overnight-open / Gap-Fill specialist program. It remains valid for that subprogram, but it is **not** the literature authority for the repository-wide broad reversal / mean-reversion program. New R1/R2/R3 literature should be maintained separately under the authority reset defined in `CONTINUE_HERE.md`.

Sources retrieved via OpenAlex, 2026-09-05, with additional offshore price-discovery sources reviewed 2026-09-06.

1. Lou, Polk, Skouras, 2019, JFE, "A tug of war: Overnight versus intraday expected returns" (doi:10.1016/j.jfineco.2019.03.011). Overnight and daytime clienteles; overnight returns and daytime returns are a tug of war. Features: previous overnight return, previous daytime return.

2. Qiao and Dam, 2020, Journal of Financial Markets, "The overnight return puzzle and the T+1 trading rule in Chinese stock markets" (doi:10.1016/j.finmar.2020.100534). A-share overnight returns are on average negative because T+1 forbids same-day sale; opening prices embed a discount (~14bp) and overnight risk. Features: overnight mean, volatility / overnight risk.

3. "The nexus of overnight trend and asset prices in China", 2024, JEDC (doi:10.1016/j.jedc.2024.104997). Overnight trend (not close-to-close) forecasts because overnight clientele underreact. Feature: trailing mean of overnight gaps.

4. "Intraday momentum and reversal in Chinese stock market", 2019, FRL (doi:10.1016/j.frl.2019.04.002). Last-session-hour / last half-hour momentum. Feature: previous last hour, previous afternoon.

5. "Factor beta, overnight and intraday expected returns in China", 2023, Global Finance Journal. Overnight vs daytime decomposition of factor premia. Feature: slower daily trend (r20) kept as control, not a new hunt.

6. "Overnight versus intraday returns of anomalies in China", 2023, Pacific-Basin Finance Journal. Anomaly returns split night/day. Used only as motivation that overnight is a distinct bucket.

7. Practitioner/open-market microstructure (US close is before next China open): last US session return and VIX change between China close and next China open. NASDAQCOM + VIXCLS from FRED, as-of last US date strictly before the China trading day.

## Offshore-China / non-overlapping-market price discovery

8. Ou, 2023, Investment Analysts Journal, "Price discovery or overreaction? A study on the reaction of Asia Pacific country ETFs to the US stock market" (doi:10.1080/10293523.2023.2208904). US-listed Asia-Pacific country ETFs trade while their underlying markets are closed; ETF and S&P 500 information can predict the next local-market NAV/return. Motivation for testing US-session China-ETF price discovery rather than assuming that only broad US returns matter.

9. Levy and Lieberman, 2013, Journal of Banking & Finance, "Overreaction of country ETFs to US market returns: Intraday vs. daily horizons and the role of synchronized trading". During non-synchronized hours, US common-market returns can dominate international ETF pricing. Used as a warning that raw China-ETF returns may mix China-specific price discovery with a US common factor; motivates preregistered SPY-differenced controls.

10. Huang, Tian and Shen, 2023, International Review of Financial Analysis 87, 102644, "Characteristics and mechanisms of the U.S. stock market spillover effects on the Chinese A-share market" (doi:10.1016/j.irfa.2023.102644). US return spillovers into A-shares are mostly absorbed quickly in the next trading day and become more prominent when the Chinese market has performed poorly. Directly relevant to rebound-versus-continuation after a weak China close.

11. Li and Zhang, 2013/2014, Emerging Markets Finance and Trade, "Spillover and Cojumps Between the U.S. and Chinese Stock Markets" (doi:10.2753/REE1540-496X4902S202). US price changes predict next-day Chinese closing-to-opening as well as closing-to-closing returns.

12. Chen, Li and Wu, 2010, Journal of Business Finance & Accounting 37(1-2), 242-269, "Price Discovery for Segmented US-Listed Chinese Stocks: Location or Market Quality?" (doi:10.1111/j.1468-5957.2009.02153.x). Earlier cross-listed-China evidence finds stronger home-market price discovery, so US-listed China prices must be empirically admitted rather than presumed informative.

13. Alhaj-Yaseen, Rowland, George and Bice, 2026, Pacific-Basin Finance Journal 99, 103205, "The price of timing: Sequenced cross-listings and market discovery in Chinese ADRs" (doi:10.1016/j.pacfin.2026.103205). Cross-listing sequence and regime affect price-discovery leadership; US shocks can predict next-day returns in secondary venues.

14. ETF market-structure references reviewed 2026-09-06: international ETFs continue trading after Asian underlying markets close and can act as fair-value / price-discovery vehicles; apparent premium/discount can therefore reflect new information rather than simple tracking error. This supports using same-US-session open-to-close moves after the China close, while source admission separately audits liquidity and noise.

## New source candidates constrained before data

- ASHS: Xtrackers Harvest CSI 500 China A-Shares Small Cap ETF; inception 2014-05-20. Chosen as the closest preregistered US-listed A-share small/mid-cap state to CSI1000.
- ASHR: Xtrackers Harvest CSI 300 China A-Shares ETF; inception 2013-11. Large/mid-cap A-share comparison.
- FXI: iShares China Large-Cap ETF; inception 2004-10-05. Broad/large-cap China offshore control.
- MCHI: iShares MSCI China ETF; inception 2011-03-29. Broad China offshore control.
- SPY: US broad-market common-factor control.

The source universe is fixed before predictive diagnostics. No same-morning China market, news, A50 futures, mainland/HK open, CNH morning move, or other contemporaneous China information is admitted.
