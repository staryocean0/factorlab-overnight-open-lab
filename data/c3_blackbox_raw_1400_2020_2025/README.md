# C3 frozen BLACKBOX raw 14:00 supplement (2020 warmup + 2021–2025)

This pack is **not** development data and is **not** a scientific result.

It is a **pure raw 14:00 data supplement** for the already frozen C3 joint reusable BLACKBOX identity:

`overnight_previous_session_last_hour_conditioned_open_state_joint_30m_60m_v1`

## What is included

- CSI1000 (`000852.SH`) only
- Exact clock: `14:00`
- Raw source field only: `close_1400` from the exact 14:00 bar close
- Trading-day inventory: accepted D1 CSI1000 raw carrier days in `2020-11-01..2025-12-31`
- One row = one accepted CSI1000 trading day
- If a day has no exact 14:00 bar, `close_1400` remains empty

No feature engineering, target engineering, resampling, nearest-clock substitution, forward fill, backward fill, interpolation, or scientific analysis was applied.

## What this does NOT authorize

This supplement's existence:

- does **NOT** authorize feature redesign,
- does **NOT** authorize horizon selection,
- does **NOT** authorize threshold search,
- does **NOT** authorize prev_afternoon rescue,
- does **NOT** authorize alternate session-window search,
- does **NOT** authorize BLACKBOX adjudication,
- does **NOT** grant production authority.

## Allowed use

Cloud main agent may consume this supplement **only** to reconstruct frozen C3 raw fields and execute the already frozen reusable BLACKBOX controller.

All parity, BLACKBOX query #5, ledger registration, and final adjudication remain cloud-only.
