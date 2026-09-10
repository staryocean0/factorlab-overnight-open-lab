# FactorLab Overnight Open Lab

Bounded cloud workspace for Overnight/Open factor research on the CSI1000 opening state. It is not the two-wave Layer 3 theme and must not be merged into `factorlab-two-wave-strategy-lab`.

The package contract requires a private repository. The repository is currently public only because the private-repository GitHub Actions quota/runner path was unavailable and a public runner was needed to execute already-frozen research workflows. See `docs/governance/cloud_session_20260906_public_runner_recovery_v1.json`. Restore private visibility after public-runner-only checks are complete before treating the package as fully compliant with its confidentiality contract.

## Repository scope

This repository is **Overnight/Open only**. Generic reversal / mean-reversion, parent-trend pullback, range re-entry, HighVol routing, and broad RMR payoff research are out of scope here. See `docs/governance/repository_scope_restoration_20260909.md`.

## Program direction — factor products and adapters

The primary objective is now to build a **deep Overnight/Open factor-product shelf** for downstream timing, stock-selection, portfolio-risk, and future instrument-mapping systems. The repository should not force every useful Overnight signal into a standalone full-day trading strategy.

The economic layers are separated:

1. predict / describe the opening state;
2. measure short-horizon residual information after the opening is observed;
3. expose frozen factor products to downstream strategies through thin adapters;
4. let the consuming strategy test its own PnL without feeding that PnL back into the upstream factor definition.

Current shelf structure:

- expected opening direction / signed gap / magnitude;
- observed opening geometry and volatility-normalized gap;
- opening surprise / residual versus the frozen expected gap;
- Gap-Fill hazard probabilities;
- global-risk / China-specific-offshore / FX driver coordinates;
- trend, volatility, prior-session-shape and calendar context;
- relative-index opening leadership;
- timing, stock-selection and portfolio-risk adapters.

Do not create an uncontrolled Cartesian product of regime buckets. Continuous causal coordinates come first; any `uptrend / range / downtrend` thresholds or other categorical states require their own result-free freeze and validation.

Program authority:

- `docs/governance/overnight_factor_product_program_v1.md`;
- `docs/governance/overnight_factor_product_registry_v1.json`.

The first active new factor identity is **`overnight_open_surprise_factor_v1`**. It asks whether

`(observed_gap - frozen_V6A_expected_gap) / rvol20`

adds information about the first 15/30/60 minutes after a 09:35 reference beyond the raw opening gap and simple causal context. This is an information diagnostic, not a trading backtest. Detailed development is limited to 2019-2020; the 2021-2025 reusable BLACKBOX remains closed for this identity until a later separately frozen aggregate protocol authorizes it.

The previously proposed `overnight_v6a_short0935_to_close_v1` route was closed **before DEV execution** because judging an Overnight predictor by the full 09:35-to-15:00 index return confounds the opening signal with post-open information outside the model's causal scope.

## Start here

```bash
python -m pip install -e .
python scripts/validate_theme_package.py
pytest -q
```

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md).

## Scientific status — next-open prediction

The current prediction-model research cycle is closed for the accepted identity.

- **Magnitude head:** `abs_frozen_clock_signed_prediction` is fresh-OOS confirmed on 2021-2025.
- **Direction head:** `median_quantile_sign` is robustly fresh-OOS confirmed against Ridge on 2026-01-05 through 2026-08-21.
- Accepted status: `component_confirmed_incumbent_research_architecture`.
- Direction and magnitude remain separate primary tasks; no stronger joint-fresh full-model claim is made.
- Opened intervals may not be reused as fresh evidence for identities they have already informed. Under the current reusable-BLACKBOX policy, 2021-2025 may still be queried for a separately frozen identity without becoming a new independent OOS sample.
- Post-2026-08-21 remains unread for the integrated identity.

Direction candidate spec SHA256: `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`.

Research acceptance: `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`.

## Scientific status — V6A global-spillover baseline

The frozen single-head signed-gap candidate `V6A_plus_ordinary_A50_preauction_closure` completed one reusable 2021-2025 BLACKBOX query and returned **PASS**. The BLACKBOX released no detailed metrics, year/quarter breakdowns, event rows, sample counts, attribution or failure clues.

A separate baseline replacement review is complete:

**V6A is now the current research baseline for the global-spillover single-head signed-gap lineage, replacing V5A in that scope only.**

This does **not** replace the repository-wide accepted two-head architecture (`median_quantile_sign` + `abs_frozen_clock_signed_prediction`), does not replace its direction or magnitude heads, and does not create a trading or production baseline.

Authority:

- `docs/governance/global_spillover_current_baseline_v1.json`;
- `docs/governance/global_spillover_v6a_baseline_replacement_review_20260910.json`;
- `docs/governance/global_spillover_v6a_blackbox_state_v1.json`;
- `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`;
- `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`.

The 2021-2025 BLACKBOX remains reusable for other separately frozen identities, but reuse does not create a new independent OOS sample and hidden BLACKBOX behavior may not be used to tune a successor.

## Scientific status — Gap-Fill V2

`gap_fill_prediction_v2` predicts, after the CSI1000 09:31 opening gap is observed, the probability that the previous 15:00 close is revisited by 15m, 60m, or EOD. The frozen V2 v1 uses only `abs_gap` and `abs_gap_over_rvol20`, with separate high/low three-stage hazard heads.

- selected architecture SHA256: `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`;
- final parameter bundle SHA256: `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`;
- 2026-01-05 through 2026-08-21 repeat-only validation: both high and low heads passed all 6/6 frozen gates;
- that 2026 block is repeat-only, not scientifically fresh;
- the first true-fresh V2 challenge remains the complete `2026-08-24 .. 2026-12-31` block and must not be partially opened or scored before its frozen protocol permits execution.

See `docs/research/gap_fill_v2_v1_development_closeout_20260906.md`, `docs/research/gap_fill_v2_2026_repeat_cloud_adjudication_20260906.md`, and `docs/governance/gap_fill_v2_true_fresh_state_v1.json`.

## Scientific status — Gap-Fill V2.1 P2 successor

The V21 P2 successor family is closed at DEV with authoritative decision **`V21_DEV_no_P2_successor`**. All three frozen candidates were `evidence_insufficient` because the CSI500-high `abs_gap > 10bp` validation count for 2017 was 15, below the preregistered per-year minimum of 20. No threshold/date relaxation, pooling rescue, candidate addition, or Audit-A opening is allowed.

- selected candidate: `null`;
- parameter freeze written: `false`;
- V21 Audit A/B: sealed / unauthorized;
- V21 external reserve: sealed;
- CSI1000 post-2026-08-21 outcomes: sealed;
- production authority: `false`.

Evidence: `docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`, `docs/research/gap_fill_v21_dev_cloud_adjudication_20260909.md`, and `docs/governance/gap_fill_v21_state_v1.json`.

## Production and downstream boundary

Production authority is `false`.

Upstream factor research must remain separate from downstream strategy monetization. Do not tune factor definitions, regime thresholds, horizons, or source rules using a consuming strategy's return. Once an upstream factor is frozen, a downstream timing/stock-selection/risk repository may preregister a thin adapter and test whether that factor improves its own complete policy.

The CSI1000 index level remains a research underlier rather than a fictitious executable fill. A future option/futures/ETF implementation requires a separate instrument-mapping and execution contract.

The closed 09:35-to-15:00 standalone short route is historical negative design evidence only; do not revive it as the default economic objective.

For the closed V2.1 P2 family, do not open its Audit A/B blocks or rescue the frozen DEV insufficiency by changing thresholds, years, model classes, candidate order, or sample gates. Any new V2.1-style continuation requires a separately motivated and preregistered Overnight identity.
