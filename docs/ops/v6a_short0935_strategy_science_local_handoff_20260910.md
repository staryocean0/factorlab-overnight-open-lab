# V6A 09:35 short-side strategy-science local handoff

Date: 2026-09-10

## Objective

Execute exactly one detailed 2019-2020 strategy-science evaluation for the frozen identity:

`overnight_v6a_short0935_to_close_v1`

This is **not** the 2021-2025 reusable BLACKBOX query. Do not open 2021-2025 strategy outcomes for this identity.

## Frozen contract

- decision-use contract: `docs/governance/v6a_short0935_financial_decision_use_contract_v1.json`
- strategy-science protocol: `docs/governance/v6a_short0935_strategy_science_protocol_v1.json`
- state: `docs/governance/v6a_short0935_strategy_science_state_v1.json`

Research execution proxy:

- underlier: CSI1000 index `000852.SH` (synthetic research PnL proxy only)
- signal: frozen V6A signed-gap prediction `> 0`
- side: short only
- entry: 09:35 one-minute close
- exit: 15:00 one-minute close
- entry cost: 1bp
- exit cost: 1bp
- total round trip: 2bp
- no long side
- no stop / target / sizing / leverage / time / threshold search

The index is not claimed to be directly shortable. Future option implementation is a separate identity.

## Execute

From repository root:

```bash
git pull
bash scripts/run_v6a_short0935_strategy_science_dev.sh
```

Expected stdout is exactly one of:

- `DEV_PASS`
- `DEV_CLOSE`
- `DEV_INSUFFICIENT`

## Expected output

The runner writes:

`docs/research/local_v6a_short0935_strategy_science_dev_receipt_v1.json`

2019-2020 is a detailed historical strategy-science window, so this receipt may contain the frozen aggregate/year-level metrics required by the protocol.

The runner must record:

- `blackbox_2021_2025_opened_for_this_strategy_identity = false`
- V6A mapped-strategy aggregate metrics
- V5A mapped-strategy comparator metrics
- always-short context
- 2019/2020 candidate metrics
- all frozen gates
- protocol/decision-contract hashes

## Commit rule

If the run completes successfully, commit only the receipt (plus this communication note only if the local process must add execution metadata) using `[skip ci]`.

Do not modify:

- V6A predictor features or parameters
- threshold `0`
- entry/exit clocks
- costs
- side
- strategy-science gates
- 2021-2025 BLACKBOX ledger

Do not open or report 2021-2025 strategy outcomes.

## Cloud continuation

- `DEV_PASS` -> cloud verifies receipt, then writes a separate low-bandwidth reusable BLACKBOX protocol for 2021-2025 under this exact strategy identity.
- `DEV_CLOSE` -> close this strategy identity; no rescue tuning and no strategy BLACKBOX query.
- `DEV_INSUFFICIENT` -> close/fail-closed unless a genuinely new identity is separately motivated; do not relax sample gates after seeing the result.

Production authority remains `false`.
