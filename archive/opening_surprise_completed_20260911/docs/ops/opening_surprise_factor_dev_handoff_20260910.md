# Opening Surprise factor DEV handoff — 2026-09-10

## Goal

Execute the first research task under the new Overnight factor-product program:

`overnight_open_surprise_factor_v1`

This is a **factor information diagnostic**, not a trading backtest.

The question is whether `opening_surprise_rvol = (observed_gap - frozen_V6A_expected_gap) / rvol20` adds short-horizon information after the open beyond raw gap and simple causal context.

## Evidence boundary

Detailed target/price outcomes may be read only for:

`2019-01-01 .. 2020-12-31`

Do not inspect or report detailed 2021-2025 rows, years, quarters, events, factor-return relationships, or strategy outcomes for this identity. Do not read 2026 outcomes.

The existing 2021-2025 V6A BLACKBOX query remains a separate completed query and does not authorize detailed development use here.

## Frozen inputs

- protocol: `docs/governance/opening_surprise_factor_v1_protocol.json`
- preanalysis: `docs/research/opening_surprise_factor_preanalysis_20260910.md`
- runner: `scripts/diagnose_opening_surprise_factor_dev.py`
- one-command runner: `scripts/run_opening_surprise_factor_dev.sh`

The runner uses:

- historical frozen V6A base panel: `data/development/csi1000_open_pit_panel.parquet`
- minute carrier: `data/high_open_dev_2015_2025/1m_official.parquet`, filtered by the runner to 2019-2020 and exact required clocks;
- FRED histories from `data/high_open_dev_2015_2025/`;
- admitted HKMA / SGX A50 pack from `data/v6a_external_sources_2015_2025/`.

Do not change the V6A model, alpha, features, A50 contract rules, cutoffs, factor definitions, controls, or horizons.

## Execute

From repository root:

```bash
git pull
bash scripts/run_opening_surprise_factor_dev.sh
```

Expected stdout:

`OPENING_SURPRISE_DEV_DIAGNOSTIC_COMPLETE`

Expected output:

`docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`

## What may be returned

Because 2019-2020 is development material for this identity, the diagnostic receipt may contain the preregistered aggregate and per-year diagnostics for 2019 and 2020.

Do not add post-hoc thresholds, buckets, alternate horizons, charts, trading rules, costs, or strategy PnL.

Commit only the diagnostic receipt (and a minimal execution note only if needed) with `[skip ci]`.

Do not update the factor registry, state, or any BLACKBOX ledger locally. Cloud review will adjudicate the evidence and decide whether the base Opening Surprise coordinate is worth promoting into a bounded factor family.

## Failure handling

If execution fails, return the traceback/error text without modifying the research formula to make it run. Infrastructure repair is allowed only after cloud review of the failure.

`production_authority=false`.
