# FactorLab Overnight Open Lab

Bounded cloud workspace for one task: predict the next CSI1000 overnight open
(high open vs low open, and gap size). It is not the two-wave Layer 3 theme and
must not be merged into `factorlab-two-wave-strategy-lab`.

The package contract requires a private repository. The repository is currently
public only because the private-repository GitHub Actions quota/runner path was
unavailable and a public runner was needed to execute the already-frozen
direction-objective experiment. See
`docs/governance/cloud_session_20260906_public_runner_recovery_v1.json`.
Restore private visibility after public-runner-only checks are complete before
treating the package as fully compliant with its confidentiality contract.

The package is a research minimum set: clock/gap contracts, 2015-2020 CSI1000
bars, PIT US prints, a frozen literature-factor baseline, and research receipts.
It does not contain raw 2021+ market rows, FactorLab git history, credentials, or
Layer 4 execution.

## Start here

```bash
python -m pip install -e .
python scripts/validate_theme_package.py
pytest -q
```

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md).

Scientific status:

- the two-head architecture's clock-aware **magnitude head is locally confirmed on 2021-2025**;
- the frozen direction successor `median_quantile_sign` is **locally robustly confirmed** on the unseen 2026-01-05 through 2026-08-21 challenge against Ridge;
- that 2026 window is now consumed for this identity and must not be reused to retune it;
- post-2026-08-21 remains unread for this candidate identity;
- the candidate is eligible only for a separate research-baseline review as the two-head direction head.

Direction candidate spec SHA256:
`9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`.

Receipt:
`docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`.

Production authority is false. A separate production review is still required.
