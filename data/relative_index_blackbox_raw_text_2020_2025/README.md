# Relative-index BLACKBOX raw clock carrier (2020 warmup + 2021–2025)

This pack is **not** development data.

It is a **cloud-execution raw carrier for an already frozen reusable BLACKBOX identity**:

`overnight_relative_size_open_leadership_joint_15m_30m_60m_v1`

## What is included

- CSI1000 (`000852.SH`) and CSI300 (`000300.SH`) only
- Exact clocks: `09:31`, `09:35`, `09:50`, `10:05`, `10:35`, `15:00`
- Raw source prices only: `open_0931` from the 09:31 bar open; all other clocks from the exact bar close
- Read window: `2020-11-01..2025-12-31` (2020 shard is warmup-only: `2020-11-01..2020-12-31`)

No feature engineering, target engineering, resampling, nearest-clock substitution, or fill was applied. Missing exact clocks remain empty.

## What this does NOT authorize

This carrier's existence:

- does **NOT** authorize feature redesign,
- does **NOT** authorize tuning,
- does **NOT** authorize horizon selection,
- does **NOT** authorize CSI500 substitution,
- does **NOT** create independent fresh OOS.

## Allowed use

Cloud main agent may consume this carrier **only** to execute one logical BLACKBOX query under the frozen protocol:

`docs/governance/relative_index_open_leadership_joint_blackbox_protocol_v1.json`

All regression, sufficiency gates, bootstrap, horizon joint decision, query registration, and final adjudication remain cloud-only.
