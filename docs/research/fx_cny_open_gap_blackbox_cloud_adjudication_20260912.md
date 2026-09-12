# OFP-B3 FX/CNY driver — reusable BLACKBOX adjudication

Date: 2026-09-12

Research identity: `overnight_fx_cny_open_gap_v1`

Parent Development identity: `overnight_fx_cny_driver_v1`

The frozen candidate is the continuous HKMA-derived `fx_cny_z` coordinate; target is normalized CSI1000 opening gap with the frozen domestic baseline. The sign convention, strict-before-China source semantics, lagged-RMS normalization and positive sign hypothesis were frozen before validation and were not changed after Development.

The compact validation used the parity-gated 2015–2025 base-panel reconstruction plus the governed external-source pack. The temporary panel was not committed. The compact receipt stores no exact metrics, counts, annual results, bootstrap results or failure attribution.

Receipt commit `08852250b254aa04cf0787667e44c3612fd356bd` adds only `docs/research/local_fx_cny_open_gap_blackbox_receipt_v1.json`.

The query identifier was independently recomputed from the frozen identity and protocol/source/reconstruction SHA256 values and matches the receipt:

`34699d9d9b3ca36d1a6d`

## Decision

**FAIL**

This closes the exact B3 continuous FX/CNY successor without validated product authority. Hidden validation behavior may not be used to change the sign convention, search thresholds/buckets, interpolate HKMA values, change the normalization window, combine B1/B2/B4 channels, or design a rescue under this identity.

Reusable BLACKBOX ledger ordinal: **10**.

`production_authority=false`.
