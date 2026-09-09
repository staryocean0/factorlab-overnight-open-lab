# OHR-05 cloud source review — 2026-09-06

## Decision

OHR-05 is accepted as a valid **source-only admission** for the next offshore-China price-discovery development diagnostic.

Accepted source identity:

- provider: `Yahoo Finance chart v8 (query1.finance.yahoo.com)`;
- provider id: `yahoo_finance_chart_v8_query1_interval1d_includePrePost_false_2015-01-01_2025-12-31`;
- local source SHA256: `045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd`;
- price convention: Yahoo chart-v8 `indicators.quote` regular-session OHLC, `includePrePost=false`; same-session price-discovery return is `quote.close / quote.open - 1`; dividend-adjusted `adjclose` is not used;
- source window: `2015-01-02..2025-12-31` only.

The source is authorized for OHR-06 **development diagnosis only**. No successor candidate is authorized by this source review, OHR-03 remains unopened, and production authority remains false.

## Integrity audit

The authoritative source-freeze receipt is `docs/research/cloud_session_20260906_local_offshore_china_source_freeze_v1.json`.

It records:

- `predictive_target_loaded=false`;
- `candidate_selection_performed=false`;
- `2026_rows_loaded=false`;
- `2026_blackbox_opened=false`;
- no raw offshore rows written to the bounded repository.

The fixed symbol universe remained exactly `ASHS`, `ASHR`, `FXI`, `MCHI`, `SPY`.

The five symbols each have 2,766 rows on the same SPY regular-session inventory from 2015-01-02 through 2025-12-31. Coverage versus SPY is 1.0 for all five. There are no missing SPY sessions, invalid price rows, invalid volume rows, or same-session absolute returns above 20%.

ASHS has two zero-volume rows in the development source. Because the research mechanism is price discovery, OHR-06 must treat a zero-volume ETF session as **not an informative trading session for any representation that depends on that ETF**. It must not silently interpret zero volume / unchanged price as a genuine zero price-discovery signal. To keep comparisons fair, OHR-06 will use a common complete-row inventory requiring all fixed source representations to be observable.

## Yahoo / Sina communication inconsistency

Commits `341e25d` / `96d5304` contained a communication narrative describing a Sina staticdata export, while the source-freeze receipt committed in the same result line already identified Yahoo chart v8 and the final Yahoo file hash above. Commit `6bd0139` corrected the communication narrative without replacing the receipt, provider id, or source hash.

This is classified as a **documentation inconsistency**, not a second predictive source identity, because:

1. the authoritative receipt is the source-freeze artifact required by the preregistered runner;
2. no CSI1000 target was loaded during OHR-05;
3. provider attempts were evaluated only for source availability/calendar quality before any predictive diagnostic;
4. no predictive metric exists for Sina or Yahoo at this stage.

Therefore the source choice was not target-conditioned. From this review forward, only the Yahoo identity and SHA256 above are admissible. Sina is not an alternate source and must not be used later as a fallback without a newly frozen source identity.

## Separate repository-governance gap

Commit `50c8b47` added `data/high_open_dev_2015_2025/`, including CSI1000 2015-2025 development rows, and changed the package ledger to acknowledge raw 2021-2025 development material in the repository. Commit `48e81fa` then recorded the user's restoration of public repository visibility, while `docs/governance/package_scope.json` still declares `private_repository_required=true`.

This is a package-scope / confidentiality-governance mismatch relative to the earlier bounded-repository contract. It does **not** make OHR-05 target-conditioned, because the OHR-05 source runner itself does not load China targets. It also does not grant any 2026 or production authority.

The mismatch should remain explicit until the financial owner either:

- restores private visibility and decides whether the 2021-2025 development pack is an approved scope change; or
- formally versions the package contract to permit a public development pack.

Do not silently treat this governance mutation as if the original private/no-post-2020 package contract never existed.

## Authorization for OHR-06

OHR-06 may now load 2015-2025 development targets **only under a new frozen diagnostic protocol** and only with the exact Yahoo source identity above.

OHR-06 is mechanism diagnosis, not candidate selection. It may evaluate only the seven offshore state representations preregistered before target access:

1. `ashs_session`;
2. `ashr_session`;
3. `ashs_minus_ashr`;
4. `a_share_consensus`;
5. `a_share_specific_vs_spy`;
6. `broad_china_specific_vs_spy`;
7. `china_etf_positive_breadth`.

The main unresolved slice is incumbent-predicts-low plus prior-China-last-hour-weakness. A representation may be admitted to a later bounded candidate family only if it satisfies the preregistered multi-year mechanism conditions; OHR-06 itself must not rank models or alter threshold/loss/quantile.

`2026-01-05..2026-08-21` remains sealed repeat-blackbox material. Post-2026-08-21 remains unread true-fresh evidence.
