# C1 15m trend-conditioned opening-state BLACKBOX adjudication — 2026-09-11

## Identity

`overnight_trend_conditioned_open_state_15m_v1`

Parent development identity:

`overnight_trend_conditioned_open_state_v1`

Product family:

`OFP-C1 prior_trend_context × OFP-A2 observed_open_geometry`

BLACKBOX window:

`2021-01-01 .. 2025-12-31`

## Decision

**`PASS`**

This is the only scientific outcome released from the reusable BLACKBOX query. No exact metrics, counts, calendar-year signs, dates/events, subgroup diagnostics, bootstrap statistics, failure clues, or internal gate details are released.

Accepted receipt:

`docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`

Receipt commit:

`61899e85ba92c4ea2718c3ce513c49c402661bc0`

Query id:

`5a27b953276382e473c0`

## Receipt / provenance review

Cloud review accepts the receipt as valid because:

- the receipt commit adds only the compact receipt and uses `[skip ci]`;
- `decision = PASS`;
- `public_detail_release = false`;
- `internal_metrics_persisted = false`;
- `blackbox_reusable_after_query = true`;
- `blackbox_consumed = false`;
- `production_authority = false`;
- the research identity and comparator match the frozen controller;
- the query id recomputes exactly from the frozen controller payload `identity | protocol_sha256 | source_manifest_sha256 | reconstruction_contract_sha256`;
- the referenced protocol, source manifest, and reconstruction contract were not modified by the receipt commit or the immediately preceding CSV-development-pack commit.

The frozen controller admits only `PASS / FAIL / INSUFFICIENT` and does not persist the internal 2021-2025 diagnostics.

## Scientific authority

The PASS confirms the separately frozen 15-minute continuous interaction product:

`trend_gap_interaction = trend20_rvol * observed_gap_rvol`

with target clock:

`09:35 -> 09:50`

under the frozen baseline controls and negative-direction scientific gates in the protocol.

Authority consequence:

**`PROMOTE_C1_15M_CONTINUOUS_FACTOR_PRODUCT`**

This promotion is deliberately narrow:

- it validates the continuous trend-conditioned opening-state coordinate for the frozen 15-minute information target;
- it does not validate the 30-minute or 60-minute horizons rejected from progression at DEV;
- it does not authorize `up / range / down` thresholds, trend quantile buckets, gap-size thresholds, or a six-cell trend × high/low-open adapter;
- it does not grant strategy-PnL, position-sizing, instrument-mapping, or production authority;
- it does not make reuse of 2021-2025 an independent OOS sample.

A categorical consumer view may be researched later only under a separately frozen, result-free threshold contract. Hidden BLACKBOX behavior may not be used to choose or rescue those thresholds.

## CSV development pack

The 2019-2020 text development pack added in commit `9cf2aa550e2da7e5f5344d79ce526d8b571041fd` is admitted as a convenience carrier for the already-opened development interval only. Its manifest links the CSV slices back to the original parquet hashes.

It does not convert the 2021-2025 reusable BLACKBOX into a detailed CSV surface and does not alter BLACKBOX confidentiality.

`production_authority=false`.
