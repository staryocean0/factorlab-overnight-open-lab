# FactorLab Overnight Open Lab

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

Scientific status: `research_candidate_local_2021_2025_confirmed`.
Production authority is false. A separate production review is still required.
