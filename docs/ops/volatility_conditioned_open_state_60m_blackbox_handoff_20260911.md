# OFP-C2 volatility-conditioned open state 60m — reusable BLACKBOX handoff (2026-09-11)

## Goal

Execute the already-frozen identity:

`overnight_volatility_conditioned_open_state_60m_v1`

This is a reusable 2021-2025 BLACKBOX validation query for one fixed continuous factor product. It is **not** a development search and not a trading backtest.

## Frozen identity

Factor:

`vol_gap_interaction = observed_gap_rvol * log(rvol20)`

where:

- `observed_gap_rvol = observed_gap / rvol20`
- `trend20_rvol = r20 / (sqrt(20) * rvol20)`
- validated C1 baseline control: `trend_gap_interaction = observed_gap_rvol * trend20_rvol`

Frozen target:

`09:35 -> 10:35`

Baseline controls are fixed by:

`docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json`

Do not change the volatility lookback, gap normalization, controls, target clock or gates.

## BLACKBOX boundary

Window:

`2021-01-01 .. 2025-12-31`

Public scientific output is exactly one of:

`PASS / FAIL / INSUFFICIENT`

Do not inspect, print, persist, commit or report:

- exact metrics;
- sample counts;
- yearly or quarterly results;
- calendar-year signs;
- event rows or dates;
- bootstrap support;
- subgroup/regime results;
- failure examples or internal gate details.

The detailed BLACKBOX may not be converted into a public CSV/text pack.

## Execute

From repository root:

```bash
git pull --ff-only
bash scripts/run_volatility_conditioned_open_state_60m_blackbox.sh
```

The one-command runner first applies the historical exact-parity reconstruction gate and creates any 2021-2025 reconstructed panel only in a temporary directory. Temporary material is deleted on exit.

Expected stdout:

`PASS`, `FAIL`, or `INSUFFICIENT`

Expected compact receipt:

`docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json`

## Commit rule

If execution completes normally, commit only the compact receipt:

```bash
git add docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json
git commit -m "Record C2 60m reusable BLACKBOX receipt [skip ci]"
git push
```

Do not update the ledger, state, registry, current authority or adjudication locally. Cloud review owns those changes.

## Forbidden rescue/search

Do not:

- create high-vol / low-vol buckets;
- search volatility thresholds or quantiles;
- change the 20-day volatility coordinate;
- test 15m or 30m alternatives;
- change the 60m target;
- add/remove controls;
- use Opening Surprise;
- run strategy PnL/cost/position optimization;
- rerun with modified gates after seeing the BLACKBOX decision.

If the command fails technically, return the traceback/error and do not modify scientific semantics to make it pass.

`production_authority=false`.
