# HE-00 — Gap-Fill V2 historical source inventory / admission handoff

## Status

Cloud has frozen the new historical-extension identity and fixed historical calendar partitions. **No new historical fill outcome may be opened yet.**

Research identity: `gap_fill_v2_historical_extension_v1`.

Parent frozen model: `gap_fill_prediction_v2` V2 v1.

Protocol:

`docs/governance/cloud_session_20260906_gap_fill_v2_historical_extension_protocol_v1.json`

Preanalysis:

`docs/research/gap_fill_v2_historical_extension_preanalysis_20260906.md`

Output template:

`docs/ops/gap_fill_v2_historical_source_inventory_template_v1.json`

Expected aggregate output:

`docs/research/local_gap_fill_v2_historical_source_inventory_v1.json`

## Objective

Inventory the **available historical source universe** before any new historical fill label or V2 score is constructed.

Priority order:

1. existing local Unified DataHub / FactorLab sources already available to the user;
2. any already-connected or already-licensed historical vendor source available in the local environment;
3. document-only availability checks for JoinQuant / Ricequant / Wind / Choice or other providers if credentials/data are not already locally available.

Do not purchase, subscribe to, scrape restricted data, or upload proprietary raw rows to the public repository without separate user authorization.

## Instruments to inventory

Required same-index candidate:

- CSI1000 / `000852`.

Cross-index inventory only, for a later separate transport protocol:

- CSI300 / `000300`;
- CSI500 / `000905`.

## Critical provenance rule for CSI1000

CSI1000 official publication date: `2014-10-17`; base date: `2004-12-31`.

Therefore any `000852` history before `2014-10-17` must be classified explicitly as one of:

- `vendor_backfilled_index`;
- `constituent_reconstructed_index`;
- `unknown_provenance`.

Do **not** call pre-publication observations `contemporaneous_live_index` merely because a vendor exposes the code retrospectively.

If the provider claims an official/back-calculated index history, record the provider/methodology documentation supporting that claim.

If the series is reconstructed locally from constituents, report whether point-in-time constituent membership, rebalancing history, weights/methodology and corporate-action treatment are available. Do not reconstruct the index during HE-00; inventory capability only.

## Frozen calendar blocks

Do not change these boundaries after seeing any outcome:

- `HE_DEV`: `2005-01-01 .. 2010-12-31`
- `HE_AUDIT_A`: `2011-01-01 .. 2012-12-31`
- `HE_AUDIT_B`: `2013-01-01 .. 2014-10-16`
- `HE_LIVE_CROSSCHECK`: `2014-10-17 .. 2014-12-31`

Missing early coverage may shorten only the **front of HE_DEV**. It may not move Audit A/B dates. If an audit block lacks adequate data, report it as unavailable.

## HE-00 allowed work

For every candidate source, collect only metadata/provenance/quality facts:

- provider, product/dataset and access method;
- provider symbol ↔ canonical symbol mapping;
- min/max date;
- total rows and unique trading days;
- rows-per-day distribution and count of 240-bar days;
- duplicate timestamp count;
- missing-timestamp summary;
- available fields;
- timezone and timestamp/bar-label semantics;
- price adjustment policy;
- provenance/backfill/reconstruction class and supporting documentation;
- PIT constituent/rebalance/weight capability when relevant;
- materialized local path and SHA256 if an already-existing artifact is available;
- whether each frozen historical block is completely covered.

It is acceptable to read parquet/file metadata, trading-day/timestamp columns and row counts.

## HE-00 hard denylist

Do not:

- compute `fill_15m`, `fill_60m` or `fill_eod`;
- compute whether a prior close was touched intraday;
- score the frozen V2 model;
- compute Brier/log-loss/AUC/PR-AUC;
- inspect feature/outcome correlations;
- rank candidate V2.1 features or models;
- tune any model, threshold, calibration or horizon;
- inspect any post-2026-08-21 outcome;
- modify the already-frozen V2 v1 parameter artifact or the 2026Q4 true-fresh protocol.

If a source query API necessarily returns OHLC values, do not summarize or analyze the values; use them only to derive metadata/coverage facts required above.

## Suggested local procedure

1. Update the repository to the HE-00 protocol commit or a descendant that has not changed the protocol/preanalysis/template.
2. Search existing Unified DataHub manifests/exports/catalogs for `000852`, `000300`, `000905`, frequency `1m`.
3. For each physical/provider source found, obtain metadata only.
4. If the local system can issue a bounded metadata/data query, request the smallest form needed to determine coverage and provenance. Do not build gap-fill targets.
5. Search already-installed provider clients/configs for historical minute availability; do not expose credentials in the receipt.
6. If JoinQuant/Ricequant/Wind/Choice are not connected locally, record them only as external candidates with documentation-derived coverage claims; do not fabricate access.
7. Populate a copy of `docs/ops/gap_fill_v2_historical_source_inventory_template_v1.json` and save it as the expected aggregate output.
8. Commit only the aggregate inventory JSON and optional non-sensitive documentation notes. Raw historical files stay local unless the user separately authorizes a minimal public pack.

## Minimum acceptance decision expected from local

At the end of HE-00, state:

- whether an admissible CSI1000 1m source exists for all/some of `2005..2014`;
- its earliest reliable date;
- whether pre-2014-10-17 is vendor backfill or constituent reconstruction;
- which frozen blocks are fully available;
- whether CSI300/CSI500 long-history 1m sources are available for later transport research;
- unresolved provenance/clock/data-quality blockers.

Do not authorize HE_DEV outcome opening locally. Return the inventory to cloud review first. Cloud will admit/reject the source identity and then explicitly open HE_DEV if justified.
