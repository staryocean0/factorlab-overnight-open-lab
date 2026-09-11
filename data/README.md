# Overnight data surfaces

This directory contains bounded research packs with different evidence roles.
Do not infer scientific freshness from file dates or physical availability.

Current package-level boundaries are governed by:

`docs/governance/package_scope.json`

## `development/`

Frozen 2015-2020 core Overnight development material:

- `csi1000_open_pit_panel.parquet`
- `1m_official.parquet`
- `us_nasdaq_vix.parquet`

This pack supplies the historical frozen V6A base panel used for exact parity and
reconstruction checks.

## `high_open_dev_2015_2025/`

CSI1000 development carrier through 2025-12-31 plus FRED NASDAQ/VIX histories.

It is used by several historical development identities and by the active
Opening Surprise diagnostic, whose runner explicitly filters detailed target use
to 2019-2020.

Physical presence of 2021-2025 rows does **not** authorize detailed use for every
identity.

## `offshore_etf_dev_2015_2025/`

Bounded Yahoo chart-v8 offshore ETF development artifact retained for the closed
offshore-China research lineage. Do not treat that closed lineage as active merely
because the data pack remains present.

## `v6a_external_sources_2015_2025/`

Admitted HKMA + SGX FTSE China A50 same-contract source pack used by the frozen
V6A lineage and current factor research.

The SGX source preserves frozen same-contract/cutoff semantics. Continuous/CFD
substitutes are not interchangeable.

## `gap_fill_repeat_2026/`

User-authorized repeat-only Gap-Fill V2 inputs through 2026-08-21.

This is **not fresh OOS**. It exists to preserve/replay the frozen repeat identity.
The true-fresh Gap-Fill V2 block is separately governed and post-2026-08-21
outcomes are not present here.

## Evidence discipline

- data availability is not outcome authority;
- read the active identity's protocol/state before loading a pack;
- do not call an opened interval fresh again for the same identity;
- reusable BLACKBOX governance may permit a separately frozen aggregate query,
  but never grants unrestricted detailed inspection;
- do not commit local-only large sources unless a specific source-admission step
  authorizes a bounded repo copy;
- production authority is false.
