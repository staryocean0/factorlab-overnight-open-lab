# Gap-Fill V2 historical extension / V2.1 preanalysis — 2026-09-06

## Correction of research cadence

The prospective `2026-08-24 .. 2026-12-31` true-fresh challenge for frozen V2 v1 remains sealed and unchanged. It is a highest-grade future adjudication, **not a research pause**.

A new research identity is therefore opened for continued development using additional historical and cross-index data:

`gap_fill_v2_historical_extension_v1`

This identity may eventually produce a distinct successor such as V2.1. It may not mutate V2 v1 and then inherit V2 v1's evidence claims.

## Research objectives

1. Acquire or expose additional historical one-minute data without first examining gap-fill outcomes.
2. Classify provenance correctly, especially for CSI1000 observations before the index's official publication date.
3. Freeze historical development and sealed-audit blocks before outcome analysis.
4. Use only the historical-development block to investigate V2.1 features/mechanisms.
5. Use Audit A for bounded successor selection and Audit B for a later independent historical confirmation.
6. Preserve the already-preregistered 2026Q4 prospective block as an independent future adjudicator.
7. Separately inventory CSI300/CSI500 long-history minute data for later cross-index transport tests.

## Provenance distinction

CSI1000 / `000852` has an official publication date of 2014-10-17 and a base date of 2004-12-31. Therefore any provider-supplied pre-2014-10-17 series must not automatically be described as contemporaneously published index observations.

Every candidate source must be classified as one of:

- `contemporaneous_live_index`: index was officially published and the vendor record represents historical market-time index observations;
- `vendor_backfilled_index`: vendor provides pre-publication history/back-calculation under an index methodology;
- `constituent_reconstructed_index`: series was reconstructed from constituent-level data by us or another identified process;
- `unknown_provenance`: source cannot document which of the above applies.

`unknown_provenance` cannot authorize sealed model promotion. It may be retained only for exploratory sensitivity work under a separate label.

## Source-admission stage HE-00

HE-00 is **metadata/provenance only**. It must not construct or inspect:

- opening-gap values beyond what is necessary for schema identity checks;
- 15m / 60m / EOD fill labels;
- model probabilities or Brier/log-loss/AUC;
- any feature/outcome association;
- candidate-model ranking.

Allowed HE-00 information includes:

- provider/source identity and access method;
- symbol mapping;
- min/max date;
- row count and trading-day count;
- counts of one-minute rows per day;
- missing/duplicate timestamp counts;
- schema/field availability;
- data-adjustment policy;
- provenance/backfill/reconstruction documentation;
- SHA256 / artifact identity;
- whether point-in-time constituent membership is required/available for reconstructed sources.

## Desired same-index history and fixed calendar blocks

If an admitted CSI1000 historical source covers the calendar ranges below, the first historical-extension generation is frozen as:

- `HE_DEV`: 2005-01-01 .. 2010-12-31 — V2.1 development; may be opened after source admission;
- `HE_AUDIT_A`: 2011-01-01 .. 2012-12-31 — sealed until a V2.1 family is frozen; may be used for bounded candidate selection only;
- `HE_AUDIT_B`: 2013-01-01 .. 2014-10-16 — sealed until exactly one V2.1 successor identity is frozen after Audit A; final backward historical confirmation;
- `HE_LIVE_CROSSCHECK`: 2014-10-17 .. 2014-12-31 — post-publication supporting cross-check, not a substitute for Audit B because of its small calendar span.

Calendar boundaries are fixed before any HE outcome is opened. Missing early years shorten only the **front** of HE_DEV; they do not move Audit A/B boundaries. If a source does not cover an entire Audit A or Audit B block with acceptable quality, that block is marked unavailable rather than shifted to another date after outcomes are seen.

The existing 2015-2025 development and 2026 repeat evidence remain consumed under V2 v1. They may be used as development context for a **new** V2.1 identity only with explicit reclassification, never as fresh evidence again.

## V2.1 scope after HE-00 source admission

No V2.1 feature family is frozen yet. The financial mechanisms allowed for investigation in HE_DEV include, subject to data availability and separate preregistration before model selection:

- gap geometry and nonlinear geometry;
- opening-auction / opening-microstructure quality;
- constituent breadth, dispersion and concentration of the index gap;
- regime conditioning such as volatility/trend/state interactions;
- information-support variables only if they are point-in-time and available by 09:31.

The purpose is not to run a generic model zoo. Mathematical form must follow the mechanism and the nested fill-time target.

## Cross-index transport inventory

HE-00 also inventories long-history minute availability for:

- CSI300 / `000300`;
- CSI500 / `000905`.

These data are not automatically pooled with CSI1000. A later `gap_fill_cross_index_transport_v1` protocol will decide whether the test is zero-refit parameter transport or architecture-only transport with index-specific training. Cross-index outcomes must not be inspected during HE-00.

## Evidence hierarchy

The program now has four distinct evidence classes:

1. development / consumed diagnostic evidence;
2. sealed backward historical audit blocks;
3. cross-index external transport evidence;
4. prospective true-fresh evidence (`2026-08-24 .. 2026-12-31`), which remains the highest-grade future adjudication for frozen V2 v1.

Historical/backfilled data can materially advance strategy research now, but provenance labels must remain explicit.

Production authority remains false.
