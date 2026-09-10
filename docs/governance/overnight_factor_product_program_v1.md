# Overnight Factor Product Program v1

Date: 2026-09-10

## Program identity

This repository is no longer governed as a project whose main objective is to force one standalone Overnight trading strategy. Its primary role is now:

**an Overnight/Open factor-product laboratory and factor adapter for downstream timing, stock-selection, portfolio-risk, and execution-aware research systems.**

The repository's job is to turn deeply researched opening information into small, causal, reusable factor products with explicit availability clocks, evidence labels, provenance, and consumer-facing semantics.

A downstream strategy may consume one or more products. This repository does not assume that every useful factor must be monetizable as an isolated strategy.

## Why this direction

The next-open model explains information that becomes realized at the opening. Once the market has opened, most of the same-day path to 15:00 is driven by additional information outside the Overnight model's causal scope. Therefore a 09:35-to-close standalone strategy is not an appropriate universal test of the Overnight research program.

The economic questions are separated into three layers:

1. **Opening-state information:** what state will / did the market open into?
2. **Short-horizon residual information:** after the opening state is known, what residual continuation / reversal / fill information remains?
3. **Downstream adapter utility:** can a timing, stock-selection, or risk system improve decisions by conditioning on the Overnight factor products?

The first two layers belong primarily in this repository. Strategy-specific PnL optimization belongs in the consuming strategy's repository after the factor identity is frozen.

## Product-design rule

Do not create an unlimited Cartesian product of labels such as trend × volatility × gap sign × holiday × instrument × regime.

A product is admitted only when it satisfies all of the following:

- it has a clear causal availability timestamp;
- it captures information that is not trivially reproducible from a single raw price field, or it standardizes raw information into a validated reusable contract;
- it has a bounded mathematical definition;
- it has a consumer-facing interpretation;
- it can be validated without tuning against downstream strategy returns;
- it has an evidence boundary and a versioned authority file;
- any categorical regime or bucket threshold is frozen before the evidence used to adjudicate it is opened.

Continuous coordinates are preferred over arbitrary buckets. Buckets may be added later as separately validated adapter views.

## Product shelf

### Shelf A — Core Overnight/Open state

These are the highest-authority products and should remain small in number.

#### OFP-A1 — Expected Open State

Availability: pre-open, no later than the frozen source cutoff.

Core fields:

- expected high/low-open direction;
- expected signed opening gap;
- expected gap magnitude;
- model/source identity and confidence-quality flags.

Current evidence sources include the accepted two-head architecture and the confirmed V6A global-spillover baseline. These are not interchangeable claims; each product field must point to its exact authority.

Consumer use: pre-open exposure preparation, entry filtering, opening-risk budgeting, option/instrument selection in a downstream system.

#### OFP-A2 — Observed Open Geometry

Availability: after the frozen opening observation clock.

Core fields:

- observed signed gap;
- absolute gap;
- gap normalized by trailing realized volatility;
- high-open / low-open sign;
- material-gap flags only when thresholds are already frozen by an authority.

Consumer use: normalize the opening shock so different volatility regimes and instruments can be compared.

#### OFP-A3 — Opening Surprise / Residual

Availability: once the observed opening gap is known.

Core idea:

`opening_surprise = observed_gap - expected_gap`

Normalized form:

`opening_surprise_rvol = opening_surprise / rvol20`

This distinguishes an expected high open from an unexpectedly strong high open, and an expected low open from an unexpectedly weak low open.

This is the first new product family to research after this program reset because it directly leverages information unique to the Overnight model rather than merely rebucketing a raw gap.

Consumer use: 09:31+ timing filters, chase/avoid decisions, short-horizon continuation/reversal conditioning, stock-selection risk overlays.

#### OFP-A4 — Gap-Fill Hazard

Availability: after the opening gap is observed.

Current product family: frozen Gap-Fill V2 v1 high/low hazard probabilities at 15m / 60m / EOD, with its existing evidence labels and true-fresh boundary unchanged.

Consumer use: distinguish opening shocks with high reversion/fill risk from shocks more likely to persist.

### Shelf B — Driver / attribution coordinates

These factors answer *why* the market is opening this way. They are not permission to inspect hidden BLACKBOX details.

#### OFP-B1 — Global Risk Driver

Candidate coordinates include frozen causal U.S. session information such as NASDAQ and VIX complete-clock terms.

#### OFP-B2 — China-Specific Offshore Driver

Candidate coordinates include the same-contract SGX FTSE China A50 closure / pre-auction information already used by the confirmed V6A baseline.

#### OFP-B3 — FX / Macro Overnight Driver

Candidate coordinates include frozen HKMA-derived USD/CNY cross information where causally available.

#### OFP-B4 — Driver Agreement / Disagreement

Planned product: a low-capacity measure of whether global-risk, China-specific offshore, and FX channels point in the same or opposing directions.

Consumer use: distinguish broad global risk-on/risk-off opens from China-specific opens and mixed-driver opens.

No driver-contribution decomposition of the 2021-2025 V6A BLACKBOX is authorized. Any new driver-agreement product must be developed on admissible development evidence with a result-free preregistration.

### Shelf C — Context coordinates

Context factors describe the state in which the opening event occurs. They should be composable with Shelf A rather than multiplied into a large hard-coded regime table.

#### OFP-C1 — Prior Trend Context

Preferred initial representation: continuous trailing trend coordinate based on already-causal pre-open information, e.g. the existing `r20` / volatility-normalized trend family.

Possible categorical views such as `uptrend / range / downtrend` are **not yet authoritative**. Their thresholds must be independently frozen and validated before publication as a product.

#### OFP-C2 — Prior Volatility Context

Continuous pre-open realized-volatility state, based on causal trailing volatility such as `rvol20` and any later admitted normalization.

#### OFP-C3 — Previous China Session Shape

Existing causal coordinates such as prior full-day, afternoon, and last-hour returns may describe whether the mainland market entered the overnight interval from strength, weakness, or late-session reversal.

#### OFP-C4 — Calendar / Closure Context

Weekend, holiday-reopen, and long-closure state. This is already important because the information set accumulated while mainland markets are closed changes with closure length.

### Shelf D — Relative / cross-index opening state

#### OFP-D1 — Relative Index Open

Planned coordinates compare the opening state across broad Chinese index families, for example CSI1000 versus CSI300 / CSI500, without treating the earlier V2.1 P2 failure as permission to rescue that closed identity.

Potential fields:

- relative expected gap;
- relative observed gap;
- relative surprise;
- small-cap versus large-cap opening leadership.

Consumer use: index timing, size/style rotation, stock-selection beta and style overlays.

Any new cross-index factor product must be a new independent identity and must respect the sealed V2.1 Audit blocks.

### Shelf E — Consumer adapters

These are thin mappings, not new alpha models.

#### OFP-E1 — Timing Adapter

Possible outputs:

- risk-on / risk-off context;
- chase-allowed / chase-caution score;
- opening exposure multiplier;
- delay/abstain flag.

The exact mapping belongs to a downstream timing strategy once the upstream factor is frozen.

#### OFP-E2 — Stock-Selection Adapter

Possible use:

- market-beta exposure scaling;
- small-cap / large-cap style overlay;
- broad-market opening-shock filter;
- cross-sectional strategy abstention or risk-budget adjustment.

This repository does **not** claim that a market-level opening factor is itself stock-specific alpha.

#### OFP-E3 — Portfolio / Risk Adapter

Possible use:

- opening gross/net exposure scaling;
- hedge urgency;
- opening execution-risk classification;
- gap-fill risk awareness.

## Validation hierarchy

A factor product should be evaluated in the following order:

1. causal timing and source closure;
2. exact mathematical identity and reproducibility;
3. incremental information versus the simpler parent factor;
4. stability across independent development slices / years where available;
5. low-dimensionality and interpretability;
6. reusable BLACKBOX confirmation only after the factor identity is frozen;
7. downstream strategy PnL only in a separately frozen consumer-adapter experiment.

Do not use downstream strategy returns to tune the upstream factor definition.

## Evidence policy

The existing 2021-2025 V6A dataset remains a reusable aggregate BLACKBOX under its current policy. It may test a separately frozen factor identity, but:

- its detailed rows / years / quarters must not be exposed through the BLACKBOX interface;
- reuse does not create a new independent OOS sample;
- its hidden behavior may not be used to design the next factor version.

Existing Gap-Fill and V2.1 evidence boundaries remain unchanged.

## Immediate research priority

The next active research identity is:

`overnight_open_surprise_factor_v1`

Reason:

- it uses the unique value of the Overnight model directly;
- it is available immediately after the opening observation;
- it has obvious utility for timing and stock-selection filters;
- it avoids pretending that the entire 09:35-to-close return should be explained by Overnight information;
- it creates a natural base onto which trend, volatility, driver, calendar, and cross-index context can later be attached one bounded adapter at a time.

After Opening Surprise is adjudicated, the next preferred context research order is:

1. trend context × core opening state;
2. volatility context × core opening state;
3. driver agreement/disagreement;
4. relative-index opening leadership;
5. downstream timing / stock-selection adapter tests.

This order is a roadmap, not authority to open evidence without a separate preregistration.

`production_authority=false`.
