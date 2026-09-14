# Overnight Factor Product Program

## Stable charter

This repository researches causal China opening-state information and bounded short-horizon conditions, and maintains exact frozen factor definitions, implementation lineage and evidence. Downstream timing, stock-selection and portfolio-risk adapters require independently frozen consumers and protocols. Market-level factors are not stock-specific ranking alpha.

Current statuses are generated in `docs/CURRENT_STATUS.md` from `docs/governance/current_authority_v1.json`, `docs/governance/overnight_factor_product_registry_v1.json`, and `docs/governance/component_bindings_v1.json`. This charter intentionally contains no independently maintained active experiment list or query counter.

## Boundaries

Continuous coordinates do not authorize buckets, sign-based trading, reweighting, new horizons or account execution. New identities must have an independent result-free motivation, causal availability, explicit source and comparator, an evidence-sufficiency rule, and a frozen protocol before relevant outcomes are read.

Development progression, validation, account execution and production are separate claims. A downstream failure does not invalidate an upstream component. An insufficient surface is not selection or rescue authority. Never decompose completed reusable BLACKBOX behavior to design a successor; reused periods are not independent OOS.

## vNext research program — Conditional Extreme Open State Transition

The next research generation changes the product objective from a broad weak-information opening bucket to a **sparse callable conditional-state component**. A future consumer should receive a signal only when a preregistered state produces a materially different conditional distribution; otherwise the component must return `ABSTAIN`.

This program is independently motivated by the consumer-interface problem. It is not a rescue of closed Opening Surprise, C3, D1, E1/E2/E3 or any failed reusable BLACKBOX identity, and hidden BLACKBOX behavior may not be decomposed to design it.

### Frozen event and transition semantics

The first-generation material-event gate is fixed before outcome analysis:

- `EXTREME_UP`: observed 09:31 opening gap `>= +30 bp` versus the prior mainland 15:00 close;
- `EXTREME_DOWN`: observed 09:31 opening gap `<= -30 bp`;
- otherwise the extreme-event layer returns `NONE` / `ABSTAIN`.

The post-open transition layer is conditional on an already-observed extreme gap. It freezes two exact, non-selectable horizons:

- early transition: `09:35 -> 09:50`;
- one-hour transition: `09:35 -> 10:35`.

For an extreme high open, positive forward return means continuation and negative forward return means fade. For an extreme low open, negative forward return means continuation and positive forward return means rebound. Exact zero or unavailable clocks are neutral / missing, never forced into a direction. Both horizons are reported; there is no post-hoc winner selection.

### Causal phase separation

The program has two callable phases and they must not leak information across clocks:

1. **pre-open extreme-event propensity** — conditions for a future `EXTREME_UP` or `EXTREME_DOWN`; this phase may not use the current opening gap or any target-day China post-open field;
2. **post-open extreme-transition state** — after the 09:31 gap is observed, conditions for continuation versus fade/rebound; this phase may use frozen gap geometry and causal state available by the reference clock, but never future path information.

First-generation pre-open candidate coordinates are restricted to already-authorized causal parents / shelf products: V6A expected-open state, B1 global-risk coordinate, B2 China-offshore coordinate, B4 driver-coherence coordinate, and the causal prior trend / volatility parents needed to reconstruct validated C1/C2 semantics. First-generation post-open candidates are restricted to observed gap geometry, the validated C1 15-minute interaction, the validated C2 60-minute interaction, and B4 as a confidence/context coordinate. Closed A3/C3/D1 identities are historical evidence only and are not candidate products in this generation.

### Result-free bucket construction and development boundary

The detailed row-level development boundary is `2015-01-05 .. 2020-12-31`. No 2021-2025 row-level BLACKBOX detail is authorized by this program.

To prevent threshold mining, first-generation categorical cuts are feature-distribution cuts rather than outcome-optimized cuts. Frozen feature quantile boundaries are learned only from the 2015-2017 development **feature distribution without inspecting the target outcomes used by this program**. Conditional-outcome evaluation and all promotion decisions are then made only on 2018-2020. Outcome-ranked threshold search, arbitrary sign flips, alternate material-gap thresholds, alternate clocks and Cartesian feature factories are forbidden.

Phase 1 tests only one-dimensional states. Phase 2 may test a small preregistered set of two-way intersections **only among Phase-1 survivors**. It may not enumerate all pairwise combinations.

### Callable-bucket progression gates

A bucket can progress only when all applicable gates pass on its frozen 2018-2020 evaluation surface:

- at least `30` evaluation observations in the bucket overall and at least `5` observations in each of 2018, 2019 and 2020;
- material conditional-probability separation versus the correct parent cohort: **either** absolute probability lift of at least `12.5 percentage points` **or** a risk ratio of at least `1.5` when the ratio is well-defined;
- a 95% interval for the probability difference that excludes zero;
- the conditional effect has the same direction in **all three** evaluation years 2018, 2019 and 2020;
- Benjamini-Hochberg family false-discovery control at `q <= 0.10` for each preregistered candidate family;
- for post-open transition buckets, the sign of mean forward-return separation must agree with the probability interpretation;
- no progression from pooled significance alone when temporal stability fails.

A state that does not clear the frozen gates is not weakened into a lower-confidence trading signal; it returns `ABSTAIN`.

### Planned consumer contract

A validated future component is expected to expose a compact state object, not a raw factor dump: `phase`, `as_of`, `event_class`, `transition_class`, `bucket_id`, `expected_probability`, `probability_lift`, `mean_return`, `coverage`, `sample_n`, `confidence`, `version`, and explicit `risk_flags`. This is a research interface contract only. It grants no account execution, position sizing, instrument mapping or production authority.

### Research order

The order is frozen and must be followed:

- **P0 — infrastructure/parity:** freeze clocks, event semantics, source lineage, development boundary, result-free bucket builder and synthetic tests;
- **P1 — pre-open univariate states:** identify conditions associated with `EXTREME_UP` / `EXTREME_DOWN`;
- **P2 — post-open univariate transitions:** identify conditions for high-open continuation/fade and low-open continuation/rebound at both frozen horizons;
- **P3 — sparse interactions:** test only preregistered two-way intersections built from P1/P2 survivors;
- **P4 — rule-list packaging:** freeze a sparse callable rule list with mandatory `ABSTAIN` outside certified states;
- **P5 — separate reusable validation:** only a separately frozen successor identity may open a reusable BLACKBOX after DEV progression; reuse is not independent OOS;
- **P6 — consumer integration:** only after component validation may a consumer strategy run its own independently frozen integration/account evaluation.

Documentation and infrastructure must be committed before P1/P2 outcome execution. `production_authority=false` throughout this program unless a future authority file explicitly changes it.

## Software and evidence maintenance

The authoritative engineering explanation is `docs/WHITEPAPER.md`. Component-to-source/protocol/receipt/test links are in the component bindings. The lifecycle manifest classifies every tracked file and prevents unrecorded drift. Preserve immutable research evidence, parameter identities and provenance; archive obsolete stages rather than rewrite them.

Current production-service packaging and trading authorization are not implied by passing the repository QA suite.

`production_authority=false`.
