# OFP-B2 China-offshore driver — reusable BLACKBOX adjudication

Date: 2026-09-12

Research identity: `overnight_china_offshore_open_gap_v1`

Parent Development identity: `overnight_china_offshore_driver_v1`

Frozen candidate is the continuous same-contract A50 coordinate `china_offshore_z`; target is normalized CSI1000 opening gap with the frozen domestic baseline. Same-contract semantics, ordinary/holiday causal cutoffs, RMS normalization and positive sign hypothesis were frozen before validation.

The compact validation used the parity-gated 2015–2025 base-panel reconstruction plus the governed 2015–2025 A50/HKMA external-source pack. The temporary panel was not committed. The compact receipt stores no exact metrics, counts, annual results, bootstrap results or failure attribution.

Receipt commit `90ebeefb9a8177f9df7ba9f4984211de93003a80` adds only `docs/research/local_china_offshore_open_gap_blackbox_receipt_v1.json`.

The query identifier was independently recomputed from the frozen identity and protocol/source/reconstruction SHA256 values and matches the receipt:

`608e037b0d24724b097b`

## Decision

**PASS**

This validates only the continuous B2 China-offshore coordinate. It does not authorize A50 thresholds, magnitude buckets, ordinary-vs-holiday selection, alternative causal cutoffs, continuous/CFD replacement, channel mixing, strategy PnL tuning or production use.

Reusable BLACKBOX ledger ordinal: **9**.

`production_authority=false`.
