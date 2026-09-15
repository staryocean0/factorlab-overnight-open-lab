# RETIRED — DO NOT CONTINUE RESEARCH HERE

**Effective 2026-09-15, this repository is retired as an active research/control-plane repository.**

Do not start, resume, extend, rerun, retune, or hand off new research in this repository. Retained code, data, protocols, results, branches, issues, and workflows are historical evidence only unless one of the current paired repositories explicitly imports them by immutable identity.

Current project work must be placed in the applicable paired control plane rather than a `factorlab-*` legacy lab. Historical scientific verdicts remain preserved, but this repository grants no current research, BLACKBOX, trading, or production authority.

---

# Overnight/Open — agent instructions

Read `CONTINUE_HERE.md`, `docs/governance/current_authority_v1.json`, `docs/CURRENT_STATUS.md`, and `docs/governance/component_bindings_v1.json` before substantial work.

This repository maintains Overnight/Open research and frozen reference implementations. Generic RMR/HighVol discovery, trading production, and downstream-PnL tuning of upstream factors are out of scope. Validated science is not a production API or executable-account authorization.

## Current execution authority

Only `docs/governance/current_authority_v1.json` may grant current research execution. Do not copy its counters/statuses here. Historical state files and their `next_action` fields are immutable as-of evidence, not today's instructions. Consult `docs/governance/repository_lifecycle_v1.json` and `docs/maintenance/20260912_reconciliation.json` for every retained, retired, moved, or deleted path.

When active research is null, run only the metadata/synthetic maintenance checks. Never execute an old handoff or workflow just because it remains in Git history or because a frozen implementation contains main(). Source preservation does not reopen a query.

## Maintenance

Run `python scripts/check_repository_consistency.py` and `python -m pytest` after installing `requirements-ci.txt`. Default tests deliberately block real market/account carriers and network access. Do not disable this barrier to make tests pass. Historical data integration belongs to an independently authorized replay, not ordinary CI.

README, CONTINUE_HERE, CURRENT_STATUS and WHITEPAPER are generated from the same authority/registry/component bindings. After legitimate metadata changes use `python scripts/check_repository_consistency.py --write-views`, then update the per-file lifecycle inventory and run all checks. Additions or deletions not classified in the lifecycle manifest fail CI.

Never rewrite sealed protocols, original parameter bundles, scientific receipts, or data provenance to make hashes agree with new code. Preserve the original blob and trace legitimate changes through the archive/history mapping. BLACKBOX query history is append-only, and repeated physical periods are not independent OOS. Incomplete Development surfaces cannot design rescue candidates.

For actual model/factor/strategy/account changes also read `.codex/skills/strategy-slice-rebuild/SKILL.md` and its project contract. Its inherited strategy procedures do not turn this maintenance request into a new experiment.

`production_authority=false`.
