# Ops handoffs

Only one handoff is currently active:

- `trend_conditioned_open_state_dev_handoff_20260911.md`

All other handoffs in this directory are historical execution records for completed, closed, or sealed research identities unless their current state file explicitly says otherwise.

Before executing any handoff, read:

1. `docs/governance/current_authority_v1.json`
2. the identity's current state file
3. the referenced protocol

The completed Opening Surprise DEV handoff is no longer active. Its identity is closed after cloud adjudication and must not be rescued through post-hoc thresholds, buckets, horizons, or interactions.

Do not rerun a historical handoff merely because the file still exists. Closed executable entrypoints that pose a material confusion risk should be moved to `archive/` while their authority/receipts remain in governance/research evidence paths.
