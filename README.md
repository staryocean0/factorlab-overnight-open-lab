# FactorLab Overnight Open Lab

Bounded cloud workspace for one task: predict the next CSI1000 overnight open
(high open vs low open, and gap size). It is not the two-wave Layer 3 theme and
must not be merged into `factorlab-two-wave-strategy-lab`.

The package contract requires a private repository. The repository is currently
public only because the private-repository GitHub Actions quota/runner path was
unavailable and a public runner was needed to execute already-frozen research
workflows. See
`docs/governance/cloud_session_20260906_public_runner_recovery_v1.json`.
Restore private visibility after public-runner-only checks are complete before
treating the package as fully compliant with its confidentiality contract.

The package is a research minimum set: clock/gap contracts, 2015-2020 CSI1000
bars, PIT US prints, frozen model identities, and research receipts. It does not
contain FactorLab git history, credentials, or Layer 4 execution. Additional
bounded development/repeat packs present in this repository remain governed by
their own Overnight identities and evidence labels.

## Repository scope

This repository is **Overnight/Open only**. Generic reversal / mean-reversion,
parent-trend pullback, range re-entry, HighVol routing, and broad RMR payoff
research are out of scope here. See
`docs/governance/repository_scope_restoration_20260909.md`.

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
- All opened data through 2026-08-21 are consumed for these identities and must not be reused for retuning.
- Post-2026-08-21 remains unread for the integrated identity.

Direction candidate spec SHA256:
`9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`.

Direction fresh receipt:
`docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`.

Research acceptance:
`docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`.

## Scientific status — Gap-Fill V2

`gap_fill_prediction_v2` predicts, after the CSI1000 09:31 opening gap is observed,
the probability that the previous 15:00 close is revisited by 15m, 60m, or EOD.
The frozen V2 v1 uses only `abs_gap` and `abs_gap_over_rvol20`, with separate
high/low three-stage hazard heads.

- selected architecture SHA256: `07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00`;
- final parameter bundle SHA256: `07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0`;
- 2026-01-05 through 2026-08-21 repeat-only validation: both high and low heads passed all 6/6 frozen gates;
- that 2026 block is repeat-only, not scientifically fresh;
- the first true-fresh V2 challenge remains the complete `2026-08-24 .. 2026-12-31` block and must not be partially opened or scored before its frozen protocol permits execution.

See:

- `docs/research/gap_fill_v2_v1_development_closeout_20260906.md`;
- `docs/research/gap_fill_v2_2026_repeat_cloud_adjudication_20260906.md`;
- `docs/governance/gap_fill_v2_true_fresh_state_v1.json`.

## Scientific status — Gap-Fill V2.1 P2 successor

The V2.1 line was created after cross-index Audit B localized the unresolved
state to CSI500 high material gaps. RD1 admitted only
`P2_relative_gap_excess = sign(gap_i) * (gap_i-gap_j) / rvol20_i` as mechanism
material for a bounded successor family.

The V21 DEV candidate ladder was frozen before outcomes:

1. `P2_XI_SHARED_1B`;
2. `P2_CSI500_SHARED_1B`;
3. `P2_CSI500_STAGE_2B`.

A legitimate local DEV execution was completed on the frozen 2015-2018
CSI300/CSI500 source and was recovered after the 2026-09-09 repository-scope
restoration. The authoritative result is:

**`V21_DEV_no_P2_successor`**.

All three candidates are `evidence_insufficient` under the frozen primary sample
gate because CSI500-high `abs_gap > 10bp` validation counts are `68 / 15 / 52`
for 2016/2017/2018, while the preregistered minimum is 20 in every validation
year. Pooled n=135 is sufficient, but 2017 is not. No threshold/date relaxation,
pooling rescue, candidate addition, or Audit-A opening is allowed.

- selected candidate: `null`;
- parameter freeze written: `false`;
- V21 Audit A: sealed / unauthorized;
- V21 Audit B: sealed / unauthorized;
- V21 external reserve: sealed;
- CSI1000 post-2026-08-21 outcomes: sealed;
- production authority: `false`.

Evidence:

- `docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`;
- `docs/governance/local_gap_fill_v21_dev_data_usage_v1.json`;
- `docs/research/gap_fill_v21_dev_cloud_adjudication_20260909.md`;
- `docs/governance/gap_fill_v21_state_v1.json`.

Do not rerun the consumed V21 DEV experiment merely because the large local
HE-00 source is absent from this cloud checkout.

## Production boundary

Production authority is `false`.

For the accepted next-open architecture, the next step is **not model retuning or
unconstrained return optimization**. A financial decision-use contract must first
define the tradable instrument, signal/decision time, order and fill semantics,
post-signal economic target, costs, risk constraints, and the mapping from
direction/magnitude outputs to an action. The CSI1000 index level is not itself a
tradable fill, and an order filled at the open cannot retroactively capture the
previous-close-to-open gap.

For the closed V2.1 P2 family, do not open its Audit A/B blocks or rescue the
frozen DEV insufficiency by changing thresholds, years, model classes, candidate
order, or sample gates. Any new V2.1-style continuation requires a separately
motivated and preregistered Overnight identity.

See `docs/governance/cloud_session_20260906_production_readiness_review_v1.json`
and `docs/research/cloud_session_20260906_research_closeout_v1.md`.
