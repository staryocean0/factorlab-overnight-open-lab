# FactorLab Overnight Open Lab

This repository is the **Overnight/Open factor-product laboratory** for FactorLab.
Its job is not to force one Overnight predictor into a standalone all-day trading
strategy. Its job is to research, validate, and package information about the
next China open so downstream timing, stock-selection, execution, and risk
systems can consume it as a causal factor adapter.

This repository is **Overnight/Open only**. Generic reversal / mean-reversion,
parent-trend pullback, broad HighVol routing, two-wave strategy logic, and
unrelated RMR research do not belong here.

## Start here

The single current authority is:

`docs/governance/current_authority_v1.json`

Then read:

- factor-product program: `docs/governance/overnight_factor_product_program_v1.md`
- product registry: `docs/governance/overnight_factor_product_registry_v1.json`
- current active state: `docs/governance/opening_surprise_factor_v1_state.json`
- active local handoff: `docs/ops/opening_surprise_factor_dev_handoff_20260910.md`

For any model or strategy change, follow:

`.codex/skills/strategy-slice-rebuild/SKILL.md`

`production_authority=false`.

## Current active research — Opening Surprise

The active identity is:

`overnight_open_surprise_factor_v1`

The factor asks whether the part of the observed open that was **not already
expected by the frozen Overnight model** contains independent short-horizon
information:

`opening_surprise_rvol = (observed_gap - frozen_V6A_expected_gap) / rvol20`

The current phase is a **2019-2020 information diagnostic**, not a trading
backtest. It tests incremental information at fixed short post-open horizons
after controlling for raw gap and simple causal context.

Current execution command:

```bash
git pull
bash scripts/run_opening_surprise_factor_dev.sh
```

Expected output:

`docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`

For this identity:

- detailed development outcomes allowed now: `2019-01-01 .. 2020-12-31` only;
- 2021-2025 detailed outcomes: **not opened**;
- trend-bucket search: **not authorized**;
- strategy PnL optimization: **not authorized**;
- 2021-2025 reusable BLACKBOX query: **not authorized yet**.

Cloud review must happen before any bounded factor family or context interaction
is created.

## Product shelf

The repository is being organized as a factor shelf rather than a Cartesian
feature factory. Current product families include:

- **Expected open state** — expected high/low open and opening-gap magnitude;
- **Observed open geometry** — actual gap sign/size normalized by volatility;
- **Opening surprise / residual** — actual open relative to what Overnight
  information already implied;
- **Gap-fill hazard** — probability the previous close is revisited after the
  opening gap is observed;
- **Overnight driver coordinates** — global-risk, China-specific offshore, FX,
  and driver agreement/disagreement;
- **Context coordinates** — prior trend, prior volatility, previous-session
  shape, and calendar closure state;
- **Relative-index opening leadership** — future separately preregistered work;
- **Downstream adapters** — timing, stock-selection, and portfolio-risk
  interfaces after upstream factors are frozen.

Do not automatically multiply these coordinates into dozens of regime buckets.
A context interaction must earn its place by adding information beyond the base
Overnight coordinate.

## Stable prediction authority

### Repository-wide next-open architecture

The accepted component-confirmed architecture remains:

- direction: `median_quantile_sign`;
- magnitude: `abs_frozen_clock_signed_prediction`.

This architecture is not replaced by the V6A single-head lineage.

Authority:

`docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`

### V6A global-spillover baseline

`V6A_plus_ordinary_A50_preauction_closure` completed one reusable 2021-2025
BLACKBOX query and returned `PASS` without releasing hidden year/quarter/event
or metric details.

V6A is now the current research baseline for the **global-spillover single-head
signed-gap lineage only**.

Authority:

- `docs/governance/global_spillover_current_baseline_v1.json`
- `docs/governance/global_spillover_v6a_baseline_replacement_review_20260910.json`
- `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`
- `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`

The 2021-2025 BLACKBOX is reusable for another separately frozen identity, but
reuse is not a new independent OOS sample and hidden BLACKBOX behavior may not
be used for design or retuning.

## Gap-Fill products

### Gap-Fill V2

The frozen `gap_fill_prediction_v2` predicts whether the previous 15:00 close is
revisited after the 09:31 gap is observed. It uses `abs_gap` and
`abs_gap_over_rvol20` with separate high/low three-stage hazard heads.

The 2026-01-05..2026-08-21 evaluation is repeat-only evidence. The first
true-fresh block is the complete `2026-08-24..2026-12-31` window and remains
sealed under its protocol/date gate.

Current state:

`docs/governance/gap_fill_v2_true_fresh_state_v1.json`

### V2.1 P2 successor

The V21 P2 successor family is closed at DEV with no successor because the
frozen per-year sample gate was insufficient. Do not rescue it by changing the
sample threshold, gap threshold, dates, candidate order, model class, or by
opening its sealed audits.

Current state:

`docs/governance/gap_fill_v21_state_v1.json`

## Data surfaces

Current bounded data packs are documented in `data/README.md` and
`docs/governance/package_scope.json`.

Important boundaries:

- `data/development/` — frozen 2015-2020 core development material;
- `data/high_open_dev_2015_2025/` — CSI1000 development carrier through 2025;
- `data/offshore_etf_dev_2015_2025/` — bounded offshore ETF development pack;
- `data/v6a_external_sources_2015_2025/` — admitted HKMA + SGX A50 source pack;
- `data/gap_fill_repeat_2026/` — user-authorized repeat-only data through
  2026-08-21, not fresh evidence.

Post-2026-08-21 outcomes remain sealed wherever current protocols require.

## Closed and archived work

Closed/completed executable entrypoints that could confuse future agents are
moved under `archive/` while preserving their exact historical bytes.

Notably:

- `archive/v6a_short0935_to_close_20260910/` — the attempted standalone
  09:35-to-close route, closed **before DEV** because the objective was outside
  the Overnight model's causal scope;
- `archive/v6a_reusable_blackbox_completed_20260910/` — completed V6A BLACKBOX
  one-command entrypoint/handoff. The underlying frozen controller library is
  retained because current factor research imports it.

See `archive/README.md`.

Historical handoffs that remain under `docs/ops/` are not automatically active.
See `docs/ops/README.md` before executing any of them.

## Research discipline

- Do not use downstream trading return to define or retune an upstream factor.
- Do not decompose a BLACKBOX after it has been admitted as aggregate-only.
- Do not create trend/volatility/category buckets before the base coordinate
  demonstrates incremental information.
- Do not substitute unrelated instruments or continuous proxies for frozen
  source identities.
- Do not rerun consumed historical experiments merely because their local raw
  source is absent from the cloud checkout.
- Do not mutate any live FactorLab registry from this repository.
- Production authority remains false until a separate instrument/account
  contract and production review explicitly grant it.

## Repository visibility

The original package contract required a private repository. The repository is
currently public because of an earlier public-runner recovery path. This is an
explicit governance mismatch recorded in `docs/governance/package_scope.json`;
do not silently rewrite history or claim the original confidentiality contract
never existed.
