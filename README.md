# FactorLab Overnight Open Lab

This repository is the **Overnight/Open factor-product laboratory** for FactorLab.
It researches causal information around the next China open and packages useful
coordinates for downstream timing, stock-selection, execution, and risk systems.
It is not required to produce one standalone all-day Overnight strategy.

This repository is **Overnight/Open only**. Generic reversal / mean-reversion,
parent-trend pullback, broad HighVol routing, two-wave strategy logic, and
unrelated RMR research do not belong here.

`production_authority=false`.

## Start here

Read in this order:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_program_v1.md`
3. `docs/governance/overnight_factor_product_registry_v1.json`
4. the active identity state + protocol
5. `docs/ops/README.md`

For model/factor/strategy changes also follow:

`.codex/skills/strategy-slice-rebuild/SKILL.md`

## Current active research — Trend-conditioned opening state

Active identity:

`overnight_trend_conditioned_open_state_v1`

Product family:

`OFP-C1 prior_trend_context × OFP-A2 observed_open_geometry`

The current continuous coordinates are:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
```

The experiment asks whether prior trend changes the short-horizon meaning of the
observed opening gap after controlling for both main effects and simple causal
context.

This is a **2019-2020 information diagnostic**, not a trading backtest.

Execute locally with:

```bash
git pull --ff-only
bash scripts/run_trend_conditioned_open_state_dev.sh
```

Expected receipt:

`docs/research/local_trend_conditioned_open_state_dev_diagnostic_v1.json`

Current restrictions:

- detailed outcomes: `2019-01-01..2020-12-31` only;
- detailed 2021-2025 outcomes: not opened for this identity;
- 2026 outcomes: not authorized;
- no `up / range / down` thresholds;
- no trend quantile buckets;
- no gap threshold search;
- no alternate lookback/horizon search;
- no strategy PnL optimization;
- no Opening Surprise rescue.

Authority:

- `docs/governance/trend_conditioned_open_state_v1_state.json`
- `docs/governance/trend_conditioned_open_state_v1_protocol.json`
- `docs/research/trend_conditioned_open_state_preanalysis_20260911.md`
- `docs/ops/trend_conditioned_open_state_dev_handoff_20260911.md`

## Recently closed — Opening Surprise

`overnight_open_surprise_factor_v1` completed its frozen 2019-2020 diagnostic.
Execution was procedurally valid, but the unconditional factor was **not
promoted** because the standardized coefficient changed sign between 2019 and
2020 at all three frozen horizons and pooled incremental information was very
small.

Decision:

`NO_STANDALONE_OPENING_SURPRISE_PRODUCT_PROMOTION_STABILITY_FAILURE`

No 2021-2025 BLACKBOX was opened for A3. Do not rescue it through post-hoc
thresholds, buckets, horizons, or interactions.

Evidence:

- `docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`
- `docs/research/opening_surprise_factor_cloud_adjudication_20260911.md`
- `docs/governance/opening_surprise_factor_v1_state.json`

Its execution entrypoint is archived under
`archive/opening_surprise_completed_20260911/`.

## Product shelf

The factor shelf is deliberately low-dimensional:

- **OFP-A1 Expected Open State** — expected opening direction and magnitude;
- **OFP-A2 Observed Open Geometry** — actual gap sign/size normalized by volatility;
- **OFP-A3 Opening Surprise** — closed as an unconditional product after DEV stability failure;
- **OFP-A4 Gap-Fill Hazard** — frozen/repeat-confirmed; true-fresh challenge pending;
- **Shelf B Driver coordinates** — global-risk, China-specific offshore, FX, agreement/disagreement;
- **Shelf C Context coordinates** — prior trend, volatility, previous-session shape, calendar closure;
- **Shelf D Relative-index opening state** — future separately preregistered work;
- **Shelf E Downstream adapters** — timing, stock-selection, portfolio-risk mappings after upstream factors freeze.

Do not multiply these into a large Cartesian regime table. Continuous coordinates
come first; categorical adapter views require separate frozen thresholds and
evidence.

## Stable prediction authority

Repository-wide accepted next-open architecture remains:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

The V6A single-head lineage does not replace that architecture.

Current global-spillover single-head baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its one reusable 2021-2025 BLACKBOX query returned `PASS` without detailed
release. Hidden BLACKBOX behavior may not be decomposed or used to tune another
identity.

Key authority:

- `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`
- `docs/governance/global_spillover_current_baseline_v1.json`
- `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`

## Gap-Fill products

Gap-Fill V2 remains frozen and repeat-confirmed. The complete
`2026-08-24..2026-12-31` block is its separately gated true-fresh challenge and
must not be partially opened before the frozen protocol permits it.

V2.1 P2 is closed at DEV with no successor because its frozen per-year sample
gate was insufficient. Do not rescue it by changing thresholds, dates, models,
candidate order, or by opening sealed audits.

Authority:

- `docs/governance/gap_fill_v2_true_fresh_state_v1.json`
- `docs/governance/gap_fill_v21_state_v1.json`

## Data surfaces

Read `data/README.md` and `docs/governance/package_scope.json`.

Important distinction: **physical data presence does not grant evidence authority**.
Every identity must obey its own state/protocol.

Main packs:

- `data/development/` — frozen 2015-2020 core pack;
- `data/high_open_dev_2015_2025/` — CSI1000 carrier through 2025;
- `data/offshore_etf_dev_2015_2025/` — bounded offshore ETF pack;
- `data/v6a_external_sources_2015_2025/` — admitted HKMA + SGX A50 pack;
- `data/gap_fill_repeat_2026/` — repeat-only 2026 pack through 2026-08-21.

## Archive

Closed/completed executable entrypoints that might confuse later agents are moved
to `archive/` while evidence remains recoverable.

Current groups include:

- `archive/v6a_short0935_to_close_20260910/`
- `archive/v6a_reusable_blackbox_completed_20260910/`
- `archive/opening_surprise_completed_20260911/`

Read `archive/README.md`. Do not execute archived entrypoints unless a new
result-free protocol explicitly revives the idea.

## Research discipline

- Do not use downstream trading return to define or retune an upstream factor.
- Do not decompose aggregate-only BLACKBOX evidence.
- Do not create arbitrary regime buckets before a continuous mechanism earns authority.
- Do not substitute unrelated instruments or continuous proxies for frozen source identities.
- Do not rerun closed historical experiments merely because their scripts remain in Git history.
- Do not mutate any live FactorLab registry from this repository.
