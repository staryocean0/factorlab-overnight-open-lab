# Trend-conditioned opening-state 15m BLACKBOX handoff — 2026-09-11

## Goal

Execute the frozen reusable-BLACKBOX query for:

`overnight_trend_conditioned_open_state_15m_v1`

This identity is the separately frozen 15-minute successor of the completed C1 development diagnostic. It tests exactly one continuous factor:

`trend_gap_interaction = trend20_rvol * observed_gap_rvol`

with target:

`09:35 -> 09:50`

This is **not** a trading backtest and must not be expanded into categorical trend buckets.

## Public-output rule

The 2021-2025 data are a reusable aggregate BLACKBOX for this identity.

The only permitted scientific result is one of:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Do not report or persist exact metrics, sample counts, yearly/quarterly signs, dates/events, bootstrap statistics, subgroup results, failure examples, or internal gate details.

## Frozen inputs

Read before execution:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/trend_conditioned_open_state_15m_state_v1.json`
3. `docs/governance/trend_conditioned_open_state_15m_blackbox_protocol_v1.json`
4. `docs/governance/overnight_reusable_blackbox_policy_v1.json`

Execution entrypoint:

`scripts/run_trend_conditioned_open_state_15m_blackbox.sh`

The wrapper first runs the existing exact-parity reconstruction gate against the frozen 2015-2020 panel. Only after parity succeeds does it create a temporary 2015-2025 feature panel. That temporary panel is deleted automatically and must never be committed.

## Execute

From repository root:

```bash
git pull --ff-only
bash scripts/run_trend_conditioned_open_state_15m_blackbox.sh
```

Expected stdout from a valid scientific query is exactly one of:

```text
PASS
FAIL
INSUFFICIENT
```

Expected receipt:

`docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`

## Strict prohibitions

Do not:

- change `trend20_rvol`, `observed_gap_rvol`, or their interaction formula;
- change the 20-day trend lookback;
- change 09:35 or 09:50;
- inspect alternate horizons;
- create `up/range/down` thresholds;
- inspect trend quantiles or tails;
- add volatility conditioning;
- add Opening Surprise terms;
- tune from BLACKBOX behavior;
- inspect or print year/quarter/event details;
- modify the reusable BLACKBOX ledger locally;
- modify registry/current authority locally;
- generate any detailed 2021-2025 report;
- keep the temporary reconstructed 2021-2025 factor rows.

## Commit rule

If and only if a valid compact receipt is written, commit **only**:

`docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`

with a commit message containing `[skip ci]`, for example:

`Record C1 15m reusable BLACKBOX receipt [skip ci]`

Do not edit the query ledger. Cloud review will verify protocol/source hashes, query id, receipt compactness, and then append exactly one logical query if valid.

## Failure handling

If execution fails before a valid scientific decision is produced, do not manufacture `INSUFFICIENT`. Return the traceback/error text. Do not relax parity, source hashes, gates, clocks, or formulas to make it run.

`production_authority=false`.
