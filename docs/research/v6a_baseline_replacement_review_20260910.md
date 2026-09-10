# V6A baseline replacement review — 2026-09-10

## Decision

`PROMOTE_AS_GLOBAL_SPILLOVER_RESEARCH_BASELINE_ONLY`

`V6A_plus_ordinary_A50_preauction_closure` replaces V5A as the active comparator **inside the global-spillover single-head signed-gap research lineage**.

It does **not** replace the repository-wide accepted two-head prediction architecture, does not replace either accepted primary head, and does not create a trading or production baseline.

## Evidence admitted to this review

The review uses only already-authorized evidence:

- the historical V6A frozen identity and formal consumed 2019-2020 progression receipt;
- the admitted official-source A50/HKMA pack;
- the reusable 2021-2025 BLACKBOX compact receipt;
- BLACKBOX decision `PASS` for query `8d367381811d7907e2ac`.

No 2021-2025 year, quarter, event, count, metric, attribution or failure-detail decomposition was opened for this review.

## Why V6A replaces V5A within this lineage

The historical V6 experiment froze V6A as the successor to V5A before the later unseen confirmation. Its scientific distinction is the ordinary-session same-contract SGX FTSE China A50 price-discovery return from the previous mainland close to strictly before the opening auction, while preserving the existing holiday A50 treatment and other complete-clock inputs.

The later reusable BLACKBOX query used the frozen V5A common-sample comparator and returned `PASS`. Under the preregistered decision semantics, that is sufficient to resolve the old "waiting genuinely unseen confirmation" status in favor of V6A for this specific lineage.

Keeping V5A as the active comparator after that PASS would ignore the completed confirmatory gate. Therefore future separately preregistered global-spillover/signed-gap candidates should compare against V6A, not V5A.

## Why this does not replace the repository-wide two-head architecture

The current accepted next-open architecture treats direction and magnitude as distinct primary tasks:

- direction: `median_quantile_sign`;
- magnitude: `abs_frozen_clock_signed_prediction`.

The V6A BLACKBOX was not a preregistered head-to-head test against that two-head architecture. It tested a single-head signed-gap Ridge candidate against V5A on a frozen common sample. Promoting it beyond that comparator scope would therefore be inference, not evidence.

Accordingly:

- repository-wide incumbent architecture: unchanged;
- direction head: unchanged;
- magnitude head: unchanged;
- joint-fresh full-model claim: still not authorized.

## Production boundary

Prediction baseline promotion is not production readiness.

The repository's earlier production-readiness review still applies: before strategy/account science can open, a separate financial decision-use contract must specify a tradable instrument, signal/decision timestamps, order/fill semantics, post-signal economic target, costs, risk constraints and action mapping.

The CSI1000 index level remains a prediction target, not a fictitious tradable fill.

`production_authority = false`.

## Current pointers

- baseline pointer: `docs/governance/global_spillover_current_baseline_v1.json`
- machine-readable review: `docs/governance/global_spillover_v6a_baseline_replacement_review_20260910.json`
- V6A state: `docs/governance/global_spillover_v6a_blackbox_state_v1.json`
- compact BLACKBOX receipt: `docs/research/local_v6a_reusable_blackbox_receipt_v1.json`
- BLACKBOX ledger: `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`

## Next research rule

If the project later develops another global-spillover/signed-gap successor, it must be materially defined and preregistered before empirical evaluation and must use V6A as the frozen comparator. Hidden 2021-2025 BLACKBOX behavior may not be used to design that successor.
