# Overnight gap literature used for v2 (not a complete survey)

Sources retrieved via OpenAlex, 2026-09-05.

1. Lou, Polk, Skouras, 2019, JFE, "A tug of war: Overnight versus intraday expected returns" (doi:10.1016/j.jfineco.2019.03.011). Overnight and daytime clienteles; overnight returns and daytime returns are a tug of war. Features: previous overnight return, previous daytime return.

2. Qiao and Dam, 2020, Journal of Financial Markets, "The overnight return puzzle and the T+1 trading rule in Chinese stock markets" (doi:10.1016/j.finmar.2020.100534). A-share overnight returns are on average negative because T+1 forbids same-day sale; opening prices embed a discount (~14bp) and overnight risk. Features: overnight mean, volatility / overnight risk.

3. "The nexus of overnight trend and asset prices in China", 2024, JEDC (doi:10.1016/j.jedc.2024.104997). Overnight trend (not close-to-close) forecasts because overnight clientele underreact. Feature: trailing mean of overnight gaps.

4. "Intraday momentum and reversal in Chinese stock market", 2019, FRL (doi:10.1016/j.frl.2019.04.002). Last-session-hour / last half-hour momentum. Feature: previous last hour, previous afternoon.

5. "Factor beta, overnight and intraday expected returns in China", 2023, Global Finance Journal. Overnight vs daytime decomposition of factor premia. Feature: slower daily trend (r20) kept as control, not a new hunt.

6. "Overnight versus intraday returns of anomalies in China", 2023, Pacific-Basin Finance Journal. Anomaly returns split night/day. Used only as motivation that overnight is a distinct bucket.

7. Practitioner/open-market microstructure (US close is before next China open): last US session return and VIX change between China close and next China open. NASDAQCOM + VIXCLS from FRED, as-of last US date strictly before the China trading day.

Not used as features: same-morning China news (contemporaneous with the gap).
