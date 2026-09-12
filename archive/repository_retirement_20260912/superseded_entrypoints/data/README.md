# Overnight data surfaces

This directory contains bounded research packs with different evidence roles. Do not infer scientific freshness from file dates or physical availability.

Current package-level boundaries are governed by:

`docs/governance/package_scope.json`

## `development/`

Frozen 2015-2020 core Overnight development material:

- `csi1000_open_pit_panel.parquet`
- `1m_official.parquet`
- `us_nasdaq_vix.parquet`

This pack supplies the historical frozen V6A base panel used for exact parity and reconstruction checks.

It also contains the bounded connector-readable text carrier:

`trend_open_state_dev_pack_2019_2020/`

That CSV pack contains only the already-opened 2019-2020 development slice and is bound to the original parquet sources by SHA256 lineage. It may be used for cloud development diagnostics such as C1/C2 without changing the evidence boundary.

## `runtime_text_2015_2025/`

Connector-readable yearly CSV carrier for cloud development execution. The intended technical window is 2015-2025, but only 2015-2020 text shards are materialized. It is a year-split text projection of the frozen factor panel plus exact opening clocks (`09:35`, `09:50`, `10:05`, `10:35`).

This is a runtime carrier, not a new scientific dataset, fresh OOS, factor authority, or production dataset. Physical/textual accessibility does not by itself grant evidence authority. Do not add 2021-2025 row-level CSV shards.

## `high_open_dev_2015_2025/`

CSI1000 carrier through 2025-12-31 plus FRED NASDAQ/VIX histories.

This pack is the physical source used by several historical identities and by reusable BLACKBOX controllers that have separately frozen authority. Physical presence of 2021-2025 rows does **not** authorize detailed inspection.

For the active C2 60m identity, 2021-2025 remains a reusable BLACKBOX. Do not export its detailed factor/target rows to a public CSV/text pack; public scientific output is restricted by the frozen protocol to `PASS / FAIL / INSUFFICIENT`.

## `offshore_etf_dev_2015_2025/`

Bounded Yahoo chart-v8 offshore ETF development artifact retained for the closed offshore-China research lineage. Do not treat that closed lineage as active merely because the data pack remains present.

## `v6a_external_sources_2015_2025/`

Admitted HKMA + SGX FTSE China A50 same-contract source pack used by the frozen V6A lineage and relevant factor research.

The SGX source preserves frozen same-contract/cutoff semantics. Continuous/CFD substitutes are not interchangeable.

## `gap_fill_repeat_2026/`

User-authorized repeat-only Gap-Fill V2 inputs through 2026-08-21.

This is **not fresh OOS**. It exists to preserve/replay the frozen repeat identity. The true-fresh Gap-Fill V2 block is separately governed and post-2026-08-21 outcomes are not present here.

## Evidence discipline

- data availability is not outcome authority;
- read the active identity's protocol/state before loading a pack;
- do not call an opened interval fresh again for the same identity;
- reusable BLACKBOX governance may permit a separately frozen aggregate query, but never grants unrestricted detailed inspection;
- connector-readable text packs are allowed only for intervals whose detailed evidence role is already open;
- do not convert a sealed/reusable BLACKBOX detailed interval into a public text pack;
- do not commit local-only large sources unless a specific source-admission step authorizes a bounded repo copy;
- production authority is false.
