# FactorLab Overnight Open Lab

This repository is the **Overnight/Open factor-product laboratory** for FactorLab. It researches causal information around the next China open and packages reusable coordinates for downstream timing, stock-selection, execution, and risk systems. It is not required to produce one standalone all-day Overnight strategy.

`production_authority=false`.

## Start here

Read in this order:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_program_v1.md`
3. `docs/governance/overnight_factor_product_registry_v1.json`
4. the active identity state + protocol
5. `docs/ops/README.md`

For model/factor/strategy changes also follow `.codex/skills/strategy-slice-rebuild/SKILL.md`.

## Current active research — C1 15m trend-conditioned opening state

Active identity:

`overnight_trend_conditioned_open_state_15m_v1`

Product family:

`OFP-C1 prior_trend_context × OFP-A2 observed_open_geometry`

Frozen continuous coordinate:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
```

Frozen target:

`09:35 -> 09:50`

The 2019-2020 multi-horizon DEV diagnostic is complete. It showed cross-year directional stability only at the 15-minute horizon, so a separately named 15m successor was frozen before any 2021-2025 query. Longer 30/60-minute horizons were not promoted.

Cloud adjudication:

`docs/research/trend_conditioned_open_state_dev_cloud_adjudication_20260911.md`

The current stage is a **reusable 2021-2025 aggregate BLACKBOX**. Its public result may be only:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Do not expose exact metrics, sample counts, years, quarters, events, subgroup results, bootstrap statistics, or internal gate failures.

Execute locally with:

```bash
git pull --ff-only
bash scripts/run_trend_conditioned_open_state_15m_blackbox.sh
```

Expected receipt:

`docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`

Authority:

- state: `docs/governance/trend_conditioned_open_state_15m_state_v1.json`
- protocol: `docs/governance/trend_conditioned_open_state_15m_blackbox_protocol_v1.json`
- handoff: `docs/ops/trend_conditioned_open_state_15m_blackbox_handoff_20260911.md`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`

Still forbidden:

- `up / range / down` threshold search;
- trend quantile buckets;
- alternate trend lookbacks;
- alternate target horizons;
- volatility conditioning;
- Opening Surprise rescue terms;
- downstream strategy PnL optimization;
- any detailed 2021-2025 result release.

## Product shelf status

- **OFP-A1 Expected Open State** — stable confirmed components.
- **OFP-A2 Observed Open Geometry** — active foundational coordinate.
- **OFP-A3 Opening Surprise** — closed after DEV stability failure; no BLACKBOX opened.
- **OFP-A4 Gap-Fill Hazard** — frozen/repeat-confirmed; true-fresh 2026Q4 challenge remains separately gated.
- **OFP-C1 Prior Trend Context** — active at the frozen 15m BLACKBOX stage.
- **OFP-C2 Prior Volatility Context** — planned after C1 is adjudicated.
- **OFP-B4 Driver Agreement/Disagreement** — planned.
- **OFP-D1 Relative Index Open** — planned as a separate identity.

Do not multiply the shelf into a Cartesian regime factory. Continuous coordinates come before categorical adapter views.

## Stable prediction authority

Repository-wide next-open architecture remains:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

The global-spillover single-head baseline remains:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX decision is `PASS`; hidden details remain sealed.

## Data and archive

Read `data/README.md` and `docs/governance/package_scope.json` for data boundaries.

Closed/completed executable entrypoints are kept under `archive/` where appropriate. Historical files remaining under `docs/ops/` are not automatically active; `docs/governance/current_authority_v1.json` is the canonical execution pointer.

Post-2026-08-21 outcomes remain sealed wherever their separate protocols require.
