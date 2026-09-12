# C2 60m prior-volatility conditioned open-state — reusable BLACKBOX adjudication

Date: 2026-09-12

Research identity: `overnight_volatility_conditioned_open_state_60m_v1`

Parent Development identity: `overnight_volatility_conditioned_open_state_v1`

## Frozen identity

Candidate increment:

`vol_gap_interaction = (gap / rvol20) * log(rvol20)`

Target:

`09:35 -> 10:35`

Baseline controls remain exactly the frozen protocol controls, including the already validated C1 continuous interaction `trend20_rvol * observed_gap_rvol`.

No volatility threshold, bucket, alternate lookback, alternate horizon, Opening Surprise term or trading-return optimization was introduced.

## Execution integrity

The cloud run used the existing parity-gated V6A base-panel reconstruction path. Development reconstruction parity is enforced before the temporary 2015–2025 panel is materialized. The temporary panel is not committed.

The reusable BLACKBOX controller persisted only the compact receipt and public decision enum. No exact metrics, counts, annual signs, bootstrap statistics, event rows, subgroup results or failure attribution were written.

The receipt commit contains only `docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json`.

The query identifier was independently recomputed from the frozen identity, protocol SHA256, source-manifest SHA256 and reconstruction-contract SHA256 and matches the receipt:

`a1068de9321c04632aad`

## Decision

**PASS**

This validates only the continuous C2 60-minute coordinate under the frozen identity:

`(gap / rvol20) * log(rvol20)` for the `09:35 -> 10:35` target, conditional on the frozen baseline controls.

It does not authorize high/low-volatility buckets, thresholds, a different volatility window, another horizon, strategy PnL tuning or production use.

Reusable BLACKBOX ledger ordinal: **7**.

`production_authority=false`.
