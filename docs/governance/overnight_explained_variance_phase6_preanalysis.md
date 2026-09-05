# Phase 6 explained-variance pre-analysis

Date: 2026-09-05

Branch: `codex/overnight-next-explained-20260905`

Frozen parent: `d183c7da81c2f4a46c8d938c7fa959acb939887c`

## Purpose

Continue the CSI1000 next-session 09:31 opening-gap research after the v5 A50-holiday result, but do so on a new successor branch so the already-frozen `V5A_plus_A50_closure` identity and its 2021-2025 unseen-controller contract remain untouched.

The user-approved research aspiration is to determine whether economically distinct, causally available information channels can raise genuine out-of-sample explanatory power from the current roughly 20%-25% region toward 25%-35%. **25%-35% is an aspiration, not a selection threshold, stop rule, or permission to search until a metric is reached.**

2019-2020 is already consumed development material. It may support bounded retrospective progression work only. It is not fresh OOS. 2021+ remains unread by cloud research.

## Financial decomposition

The remaining unexplained opening-gap variance is treated as a mixture rather than as a single missing factor:

`gap = global overnight information + China-linked offshore price discovery + domestic night-session information + pre-open state + regime-dependent transmission + irreducible/news/microstructure noise`

The research program therefore separates information sources before considering additional model flexibility.

## Parallel pre-research ranking

### 1. Offshore China — SGX FTSE China A50 daily pre-auction clock

**Priority: first executable experiment.**

Financial need: obtain a China-linked price-discovery measure available while mainland A shares are closed on ordinary sessions, not only long holidays.

Why this precedes generic Japan/Europe indices:

- SGX A50 is directly linked to Chinese equities.
- The existing v5 result already supports an A50 closure mechanism on long A-share holidays.
- Existing code has an official-SGX tick archive contract, explicit contract-selection clock, same-contract guard, and archive provenance.
- Literature supports meaningful SGX A50 price discovery even when mainland index futures also trade.

Primary phase-6 clock will stop at **09:14:59 Singapore/Beijing time**, immediately before mainland A-share opening call auction begins at 09:15. This intentionally excludes target-market auction information from the primary offshore feature.

Authoritative China-market timing references:

- Shanghai Stock Exchange trading rules: opening call auction is 09:15-09:25; 09:20-09:25 does not accept cancellation; auction realtime information includes virtual reference price, virtual matched volume and virtual unmatched volume.
  - https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml
- Historical SSE rules in force during the development window also state 09:15-09:25 opening call auction.
  - https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/c_20180806_10784917.shtml

The earlier v5 holiday feature used 09:24:59 under its already-frozen contract. Phase 6 does not rewrite that historical experiment. The new ordinary-session feature uses the stricter 09:14:59 cutoff to answer a different question: how much **pure offshore** information exists before mainland auction formation begins?

### 2. Domestic night session — Chinese commodity futures

**Priority: source-validation track in parallel; no model admission yet.**

Financial need: capture China-specific information generated after the A-share 15:00 close but before the next equity open, especially industrial-demand and construction-cycle information not fully represented by U.S. equity/VIX or offshore A50.

A bounded, economically predefined basket is preferred over contract mining:

- SHFE copper `CU`: broad industrial/global-China cyclical demand.
- SHFE rebar `RB`: domestic construction/infrastructure demand.
- DCE iron ore `I`: China steel-chain demand.

A public CC0 GitHub dataset was located:

- `Freddy-Hexas/china-futures-5min-2015-2025`
- 5-minute contract OHLCV/open-interest data across CFFEX/CZCE/DCE/INE/SHFE/GFEX.

This is **not treated as an authoritative exchange source**. It may be used only as a candidate transport source after a frozen source-integrity audit against official exchange session clocks and sampled official daily/settlement data. If the audit fails, the entire domestic-night track is invalidated rather than rescued with another proxy after seeing model results.

No domestic-night model result may be read before that source gate is sealed.

### 3. Mainland opening-auction / pre-open state

**Priority: economically important but current historical data contract blocked.**

SSE rules establish that 09:15-09:25 auction realtime information includes virtual reference price, virtual matched volume and virtual unmatched volume. These variables are directly relevant to the opening-price formation mechanism.

However:

- historical auction/order-flow data is not currently present in this repository;
- exchange realtime trading information is exchange-owned/licensed;
- using the final 09:25 auction price to predict the 09:31 gap would be target-proximate and would change the economic decision clock.

Therefore Phase 6 **does not use final mainland auction output**. Any future auction experiment must separately preregister its execution/decision time and historical data provenance before reading results.

The 09:14:59 A50 cutoff is intentionally chosen so the first phase-6 experiment remains outside this ambiguity.

### 4. Nonlinear regime-dependent transmission

**Priority: deferred until at least one new information channel is sealed.**

Financial need: allow the same external shock to have different transmission strength under different pre-existing market states.

This is not used as the first step because nonlinear flexibility on an already-consumed 2019-2020 holdout can manufacture apparent fit without adding information.

When admitted, the first regime experiment must be low-dimensional and economically interpretable, for example a single continuous interaction between a frozen offshore signal and a pre-existing volatility/state measure derived only from pre-target data. Threshold grids, tree depth searches, model-family sweeps and holdout-selected state boundaries are forbidden.

## Deprioritized channels

- KOSPI same-morning information retains a strong financial prior, but the official KRX historical intraday data contract is currently authentication/licensing blocked.
- Japan is lower priority because prior high-frequency literature is more consistent with China -> Japan than Japan -> China.
- Broad Europe is lower priority because Europe is closed before the China morning and likely overlaps global risk already represented by U.S. information.
- HKEX HSI/HSCEI futures have an attractive clock but official historical tick data is a paid product; no free reproducible official historical contract has yet been established.

## Phase-6 execution order

1. Resolve the pre-2016 SGX historical tick schema/message-code ambiguity before bulk extraction.
2. Freeze and test a scalable official-SGX daily A50 endpoint extractor.
3. Execute exactly one selectable daily-A50 increment against a same-sample frozen comparator.
4. In parallel, audit the domestic-night candidate data source without reading target-model performance.
5. Only after a new information channel is sealed may a single low-DOF regime interaction be preregistered.
6. Auction-state work remains blocked until a lawful, historical, causal data contract is established.

## Hard governance

- 2021+ cloud read: forbidden.
- 2019-2020: consumed/repeat research material only.
- PnL/total-return/Sharpe selection: forbidden.
- target R2 range 25%-35%: aspiration only, never a search budget or acceptance threshold.
- no feature fishing across commodity symbols, market indices, cutoffs, models or regime definitions.
- no mutation of the frozen v5 unseen-controller contract.
- no production, registry, runtime-routing or baseline-replacement authority.
- all attractive results that fail source, clock, common-sample or preregistration validity are invalidated rather than salvaged.
