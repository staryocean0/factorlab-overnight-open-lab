# Historical archive

Archives preserve prior source, contracts, whitepapers, handoffs and tests as historical evidence, not current execution authority. Start at `CONTINUE_HERE.md` for today's repository.

The 2026-09-12 reconciliation is indexed by `docs/maintenance/20260912_reconciliation.json`. Every original path has a disposition and a baseline blob. Complete historical replay uses baseline commit `0e28a6285745552a665d5b1cba11c9da73fbacd7` in a separate worktree and its original environment/authorization, not direct execution of relocated scripts.

Archive file bodies and relative paths retain freeze-time meaning. Resolve original repository paths with `python scripts/check_repository_consistency.py --resolve ORIGINAL_PATH`. Completed one-shot workflows were removed from the current tree but remain recoverable at the baseline anchor.

Do not relabel old results fresh, turn old next_action text into current authority, or alter frozen evidence to match present code. `production_authority=false`.
