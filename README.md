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
contain raw 2021+ market rows, FactorLab git history, credentials, or Layer 4
execution.

## Start here

```bash
python -m pip install -e .
python scripts/validate_theme_package.py
pytest -q
```

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md).

## Scientific status

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

## Production boundary

Production authority is `false`.

The next step is **not model retuning or unconstrained return optimization**. A
financial decision-use contract must first define the tradable instrument,
signal/decision time, order and fill semantics, post-signal economic target,
costs, risk constraints, and the mapping from direction/magnitude outputs to an
action. The CSI1000 index level is not itself a tradable fill, and an order
filled at the open cannot retroactively capture the previous-close-to-open gap.

See `docs/governance/cloud_session_20260906_production_readiness_review_v1.json`
and `docs/research/cloud_session_20260906_research_closeout_v1.md`.
