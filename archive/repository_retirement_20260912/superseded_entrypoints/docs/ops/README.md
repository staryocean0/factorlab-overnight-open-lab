# Ops handoffs

Only one handoff is currently active:

- `volatility_conditioned_open_state_60m_blackbox_handoff_20260911.md`

All other handoffs in this directory are historical execution records for completed, closed, or sealed research identities unless their current state file explicitly says otherwise.

Before executing any handoff, read:

1. `docs/governance/current_authority_v1.json`
2. the identity's current state file
3. the referenced protocol
4. `docs/governance/overnight_reusable_blackbox_policy_v1.json` when the active task is a reusable BLACKBOX query

The active task is the frozen reusable BLACKBOX validation for:

`overnight_volatility_conditioned_open_state_60m_v1`

Execute only:

```bash
git pull --ff-only
bash scripts/run_volatility_conditioned_open_state_60m_blackbox.sh
```

Commit only the compact receipt produced by that command. Do not update the ledger, state, registry or current authority locally.

Historical handoffs include the completed C1 15m BLACKBOX and its multi-horizon DEV parent. C1 is already a validated 15-minute continuous factor product and must not be rerun or decomposed.

The C2 multi-horizon DEV parent is also complete. Its cloud adjudication authorized only the fixed 60-minute successor; do not rerun DEV to select another horizon or construct high/low-volatility buckets.

Do not rerun a historical handoff merely because the file still exists. `docs/governance/current_authority_v1.json` is the canonical pointer for active work.
