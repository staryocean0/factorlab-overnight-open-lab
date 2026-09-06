# FactorLab Overnight Open Lab

Latest research continuation on this branch: [2026-09-06 handoff](docs/user/overnight_research_handoff_20260906.md)
and [v9 conclusion](docs/research/global_spillover_v9_conclusion_20260906.md).
V9 is complete and is not promoted; V6A remains the candidate awaiting its
independent local unseen confirmation. The initial package description below
is historical scope, not a statement that later branch research is missing.

Private, bounded cloud workspace for one task: predict the next CSI1000 overnight
open (high open vs low open, and gap size). It is not the two-wave Layer 3 theme
and must not be merged into `factorlab-two-wave-strategy-lab`.

The package is a research minimum set: clock/gap contracts, 2015-2020 CSI1000
bars, PIT US prints, a frozen literature-factor baseline, and a holdout receipt.
It does not contain 2021+ market rows, FactorLab git history, credentials, or
Layer 4 execution.

## Start here

```bash
python -m pip install -e .
python scripts/validate_theme_package.py
pytest -q
```

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md).

Scientific status: `research_candidate_waiting_local_2021_2025_controller_confirm`.
Production authority is false.
