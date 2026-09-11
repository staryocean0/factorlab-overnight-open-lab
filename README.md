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

## Current active research — C2 60m volatility-conditioned opening state

Active identity:

`overnight_volatility_conditioned_open_state_60m_v1`

Product family:

`OFP-C2 prior_volatility_context × OFP-A2 observed_open_geometry`

Frozen continuous coordinates:

```text
observed_gap_rvol = observed_gap / rvol20
trend20_rvol = r20 / (sqrt(20) * rvol20)
trend_gap_interaction = observed_gap_rvol * trend20_rvol
log_rvol20 = log(rvol20)
vol_gap_interaction = observed_gap_rvol * log_rvol20
```

The validated C1 `trend_gap_interaction` stays in the C2 baseline so C2 must add information beyond trend-conditioned opening state.

Frozen target:

`09:35 -> 10:35`

The 2019-2020 C2 development diagnostic was executed in the cloud from the bounded CSV development carrier. The adjudication was:

`C2_DEV_PROGRESS_60M_CONTINUOUS_COORDINATE_ONLY`

The 15-minute C2 interaction failed cross-year stability. The 30-minute interaction was directionally stable but too weak/uneven for progression. The 60-minute interaction was stable enough to justify a separately frozen reusable BLACKBOX identity.

Development authority:

`docs/research/volatility_conditioned_open_state_dev_cloud_adjudication_20260911.md`

The current stage is a **reusable 2021-2025 aggregate BLACKBOX**. Public scientific output may be only:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Execute locally with:

```bash
git pull --ff-only
bash scripts/run_volatility_conditioned_open_state_60m_blackbox.sh
```

Expected compact receipt:

`docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json`

Authority:

- state: `docs/governance/volatility_conditioned_open_state_60m_state_v1.json`
- protocol: `docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json`
- handoff: `docs/ops/volatility_conditioned_open_state_60m_blackbox_handoff_20260911.md`
- reusable BLACKBOX policy: `docs/governance/overnight_reusable_blackbox_policy_v1.json`

Still forbidden:

- high-vol / low-vol threshold search;
- volatility quantile buckets;
- alternate volatility lookbacks;
- alternate target horizons;
- changing the validated C1 baseline control;
- Opening Surprise rescue terms;
- downstream strategy PnL optimization;
- detailed 2021-2025 result release or public BLACKBOX CSV export.

## Product shelf status

- **OFP-A1 Expected Open State** — stable confirmed components.
- **OFP-A2 Observed Open Geometry** — active foundational coordinate.
- **OFP-A3 Opening Surprise** — closed after DEV stability failure; no BLACKBOX opened.
- **OFP-A4 Gap-Fill Hazard** — frozen/repeat-confirmed; true-fresh 2026Q4 challenge remains separately gated.
- **OFP-C1 Prior Trend Context** — validated BLACKBOX-PASS 15-minute continuous factor product.
- **OFP-C2 Prior Volatility Context** — 60-minute continuous candidate at frozen reusable BLACKBOX stage.
- **OFP-B4 Driver Agreement/Disagreement** — planned after active C2 adjudication.
- **OFP-D1 Relative Index Open** — planned as a separate identity.

Do not multiply the shelf into a Cartesian regime factory. Continuous coordinates come before categorical adapter views.

## Stable prediction authority

Repository-wide next-open architecture remains:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

The global-spillover single-head baseline remains:

`V6A_plus_ordinary_A50_preauction_closure`

Its completed reusable 2021-2025 BLACKBOX decision is `PASS`; hidden details remain sealed.

## Data and archive

The connector-readable CSV carrier under `data/development/trend_open_state_dev_pack_2019_2020/` is limited to the already-opened 2019-2020 development interval. It does not expose the reusable 2021-2025 BLACKBOX.

The yearly runtime text pack under `data/runtime_text_2015_2025/` is also connector-readable, but only 2015-2020 shards are present. It does not replace parquet provenance and does not open the reusable 2021-2025 BLACKBOX.

Read `data/README.md` and `docs/governance/package_scope.json` for data boundaries. Historical files are not automatically active; `docs/governance/current_authority_v1.json` is the canonical execution pointer.
