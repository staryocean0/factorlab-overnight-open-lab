# OFP-B1 global-risk driver — reusable BLACKBOX adjudication

Date: 2026-09-12

Research identity: `overnight_global_risk_open_gap_v1`

Parent Development identity: `overnight_global_risk_driver_v1`

## Frozen identity

Candidate: `global_risk_z`.

Target: `opening_gap_rvol`.

The coordinate, 60-day lagged-RMS normalization, domestic baseline controls and positive sign hypothesis were frozen before 2021–2025 validation. No A50, FX, B4 coherence, threshold, bucket, weight, normalization or target changes were made.

## Execution integrity

The validation used the existing parity-gated V6A reconstruction path. The temporary 2015–2025 panel was not committed. The compact controller persisted no internal metrics, counts, annual results, bootstrap results or failure attribution.

The receipt commit `efabcbf3f9f3de4b597c0cad29c45ccdbe2ed754` adds only `docs/research/local_global_risk_open_gap_blackbox_receipt_v1.json`.

The query identifier was independently recomputed from the frozen identity, protocol SHA256, source-manifest SHA256 and reconstruction-contract SHA256 and matches the receipt:

`6b0b6899f94fd8353a34`

## Decision

**PASS**

This validates the continuous B1 global-risk coordinate for normalized CSI1000 opening-gap interpretation under the frozen domestic baseline.

It does not authorize discrete risk-on/off thresholds, magnitude buckets, alternative NASDAQ/VIX weights, another normalization window, B2/B3 channel mixing, strategy PnL tuning or production use.

Reusable BLACKBOX ledger ordinal: **8**.

`production_authority=false`.
