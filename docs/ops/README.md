# Ops handoffs

Only one handoff is currently active:

- `trend_conditioned_open_state_15m_blackbox_handoff_20260911.md`

All other handoffs in this directory are historical execution records for completed, closed, or sealed research identities unless their current state file explicitly says otherwise.

Before executing any handoff, read:

1. `docs/governance/current_authority_v1.json`
2. the identity's current state file
3. the referenced protocol
4. `docs/governance/overnight_reusable_blackbox_policy_v1.json` when the active task is a reusable BLACKBOX query

The completed C1 multi-horizon DEV handoff `trend_conditioned_open_state_dev_handoff_20260911.md` is historical. Its cloud adjudication retained only a separately frozen 15-minute successor; do not rerun DEV or select another horizon from the old receipt.

The completed Opening Surprise DEV handoff is also historical and its identity is closed. Do not rescue it through post-hoc thresholds, buckets, horizons, or interactions.

Do not rerun a historical handoff merely because the file still exists. `docs/governance/current_authority_v1.json` is the canonical pointer for active work.
