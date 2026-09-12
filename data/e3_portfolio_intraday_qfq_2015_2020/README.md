# E3 held-symbol intraday QFQ carrier (2015–2020)

This pack is **not** a scientific result and is **not** an E3 protocol change.

It is a **minimal price carrier** for frozen REAKA consumption-portfolio holdings:

- consumer: `staryocean0/factorlab-multifactor-stock-lab` @ `af2e478aaff5c8ef7f753424b57fd2d19019f248`
- strategy / model / account: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1` / `d8-h8-K1-r0_fit_prefix_successor_incumbent` / `N30_equal_backfill_unconstrained`
- clocks: previous-day exact `15:00`, current-day exact `09:35`, current-day exact `09:50`
- price view: DataHub canonical QFQ signal, built by the official mechanical conversion `close_qfq = close_raw * price_multiplier`

## Source identity

- raw 1m: `bars_cn_a_1m_raw_canonical_4ceca170a851`
- adjustment: `adjust_factors_cn_a_xdxr_v10_20260816`
- window: `2015-01-05` .. `2020-12-31`
- inventory: union of 14:30 and 14:45 `2011_2020` account identities, then deduplicated to `(trading_day, prev_trading_day, asset_id)`

A leftover READY materialized view `bars_cn_a_1m_qfq_canonical_deep_value_domain_repair_20260628` exists, but it is Sina-adjusted and is not current CN-A stock QFQ authority. It was not used.

## What is included

CSV columns only:

`trading_day,prev_trading_day,asset_id,prev_close_1500_qfq,close_0935_qfq,close_0950_qfq`

One row = one frozen holding's next-day exact-clock price requirement. If an exact bar is absent, the price cell stays empty. No nearest-clock substitution, fill, interpolation, or resampling.

## What this does NOT authorize

This pack does not calculate 09:35→09:50 returns, portfolio returns, weights, C1, candidate actions, risk/return improvement, annual statistics, bootstrap, or PASS/FAIL. It does not modify E3 protocol/state/current authority.
