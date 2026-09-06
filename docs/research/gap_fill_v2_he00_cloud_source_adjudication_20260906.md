# Gap-Fill V2 historical extension HE-00 — cloud source adjudication — 2026-09-06

## Decision

Research identity: `gap_fill_v2_historical_extension_v1`.

HE-00 receipt reviewed:

`docs/research/local_gap_fill_v2_historical_source_inventory_v1.json`

Receipt commit: `13fd622506139e15e531fbe73c5f1424664c829b`.

Protocol parent: `62056c7b2806126491a81ab0a5f4d03f4f024f26`.

The commit comparison shows exactly one added file: the aggregate HE-00 inventory receipt. No protocol, partition, test, V2 v1 parameter, 2026Q4 fresh artifact, historical outcome receipt, or raw historical file changed.

The receipt explicitly records:

- `HE00_only=true`;
- `outcome_inspection_performed=false`;
- `fill_target_construction_performed=false`;
- `model_scoring_performed=false`;
- `post_2026_08_21_outcomes_opened=false`.

HE-00 is accepted as metadata/provenance evidence.

## Same-index CSI1000 adjudication

Admitted observed source identity:

- canonical symbol: `000852.SH`;
- dataset: `bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`;
- dataset SHA256: `25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`;
- provenance: `contemporaneous_live_index` only from `2014-10-17`;
- earliest observed day: `2014-10-17`;
- no row exists before `2014-10-17` in the admitted local source.

Therefore the previously frozen same-index historical blocks are adjudicated exactly as preregistered:

- `HE_DEV 2005-01-01..2010-12-31`: **unavailable**;
- `HE_AUDIT_A 2011-01-01..2012-12-31`: **unavailable**;
- `HE_AUDIT_B 2013-01-01..2014-10-16`: **unavailable**;
- `HE_LIVE_CROSSCHECK 2014-10-17..2014-12-31`: **admitted supporting crosscheck only**.

The unavailable blocks must not be shifted forward into later CSI1000 years. Existing 2015-2025 and 2026 repeat evidence remain consumed under their prior identities.

No local vendor backfilled 000852 1m source and no admissible PIT constituent reconstruction capability were found. Future acquisition of such a source may reopen a new source-admission stage, but it cannot retroactively change this HE-00 decision.

## Minute-quality adjudication

The raw canonical lake is admitted as the source identity rather than the 2015+ FactorLab densified export.

Important quality facts:

- no duplicate timestamps;
- no silent carry-forward in the admitted raw lake;
- many days contain 239 rather than 240 official clocks, dominated by absent `14:59`;
- CSI1000 has one day missing `09:31` in the full source inventory (`2020-07-22`), outside the historical-extension block being considered here;
- 15:00 is present for CSI1000 source inventory;
- the 2015+ consumer export performs bounded prior-observed-point densification and is therefore not the HE historical admission source.

Any later target protocol must fail closed on missing required clocks. Cross-index transport will use common full-240-clock rows for the first generation so no missing-minute fill event can be silently inferred.

## Cross-index source admission

The same canonical raw lake is admitted for a separate `gap_fill_cross_index_transport_v1` research identity, without pooling with CSI1000.

### CSI300 / 000300.SH

- provenance: contemporaneous published index history;
- earliest observed day: `2005-04-08`;
- DEV coverage: `2005-04-08..2010-12-31` (front shortened only by official pre-launch period);
- Audit A `2011..2012`: complete versus China A-share trading calendar;
- Audit B `2013..2014-10-16`: complete versus calendar;
- complete 240-bar days: 1283 in DEV, 480 in Audit A, 410 in Audit B.

### CSI500 / 000905.SH

- provenance: contemporaneous published index history;
- earliest observed day: `2007-01-15`;
- DEV coverage: `2007-01-15..2010-12-31` (front shortened only by official pre-launch period);
- Audit A `2011..2012`: complete versus China A-share trading calendar;
- Audit B `2013..2014-10-16`: complete versus calendar;
- complete 240-bar days: 911 in DEV, 480 in Audit A, 410 in Audit B.

These histories are sufficient to begin cross-index development immediately.

## Progression decision

Same-index historical outcome opening is **not authorized**, because the preregistered pre-2014 CSI1000 blocks do not exist in the admitted source.

The next active route is:

`gap_fill_cross_index_transport_v1`

It will be preregistered before any CSI300/CSI500 gap-fill outcome is constructed. It must preserve V2 v1 immutability and the sealed 2026Q4 CSI1000 prospective challenge.

Production authority remains false.
