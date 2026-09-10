# V6A reusable BLACKBOX cloud adjudication — 2026-09-10

Identity: `V6A_plus_ordinary_A50_preauction_closure`

Comparator: `V5A_common_sample_comparator`

BLACKBOX window: `2021-01-01 .. 2025-12-31`

## Decision

`PASS`

This is the only scientific result released from the reusable BLACKBOX query. No exact metrics, counts, years, quarters, events, subgroup diagnostics, attribution, failure clues or internal gate details are released.

## Receipt verification

Accepted receipt:

`docs/research/local_v6a_reusable_blackbox_receipt_v1.json`

Receipt commit:

`518111fddbbd9cd113afcf5eb4bd43acb6d6c484`

Query id:

`8d367381811d7907e2ac`

Cloud verification confirmed:

- receipt contains only the three-state decision plus non-outcome provenance;
- `decision = PASS`;
- `public_detail_release = false`;
- `internal_metrics_persisted = false`;
- `blackbox_reusable_after_query = true`;
- `blackbox_consumed = false`;
- receipt protocol SHA256 exactly matches the current frozen V6A BLACKBOX protocol;
- receipt source-manifest SHA256 exactly matches the admitted V6A source manifest;
- query id recomputes exactly from the frozen identity/comparator/window/protocol/source payload;
- the receipt commit changed only the compact receipt and used `[skip ci]`.

## Technical retry treatment

Two earlier technical attempts are not separate scientific queries:

1. the first attempt stopped before evaluation because the wrong in-repository panel path lacked the frozen V6A base features;
2. the second attempt completed the frozen evaluation but failed during receipt serialization because JSON-style booleans were used in Python.

The successful rerun changed no candidate, feature, model, alpha, source identity, cutoff, contract rule, sample rule or gate. It is therefore recorded as completion of the same logical frozen query, not as a new candidate or independent OOS sample.

## Scientific authority

Under the frozen prior confirmation contract, `PASS` means only:

`eligible_for_separate_baseline_replacement_review`

It does **not** automatically replace the baseline and does not grant production, registry mutation or runtime-routing authority.

The 2021–2025 BLACKBOX remains reusable for separately frozen future identities. Reuse does not create a new independent OOS period and BLACKBOX behavior may not be used to tune or rescue a successor.

`production_authority = false`.
