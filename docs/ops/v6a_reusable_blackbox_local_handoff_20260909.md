# V6A reusable BLACKBOX local execution handoff

Date: 2026-09-09

## Task

Execute exactly one reusable BLACKBOX query for the frozen Overnight identity:

`V6A_plus_ordinary_A50_preauction_closure`

Comparator:

`V5A_common_sample_comparator`

BLACKBOX window:

`2021-01-01 .. 2025-12-31`

This window is **reusable BLACKBOX validation**, not a one-time consumable dataset.

## Public-output rule

The only allowed scientific output is one of:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Do not return or commit exact metrics, sample counts, yearly/quarterly breakdowns, dates/events, subgroup diagnostics, attribution, probability details, failure clues or rescue suggestions.

The controller computes the frozen gates internally and deliberately does not persist those details.

## Frozen authority

Current BLACKBOX protocol:

`docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json`

Reusable BLACKBOX policy:

`docs/governance/overnight_reusable_blackbox_policy_v1.json`

Historical V6 authority is frozen on branch:

`codex/overnight-next-explained-20260905`

with candidate code SHA:

`2ffec2a2ebfc3490ff0805e9b14680aa076a320e`

and bounded external-data freeze:

`0ae33649208805937dd41549f6874496319ae911`

Do not change feature definitions, cutoff times, contract-selection rules, model family, alpha, missing-data rules, gates or sample rules.

## Required local source inputs

The local controller needs these source objects before opening BLACKBOX outcomes:

1. CSI1000 annotated panel covering 2015-2025 with the frozen baseline columns and `gap` target.
2. FRED NASDAQ and VIX histories covering the needed clock range.
3. HKMA `usdcny_hk` daily history covering the needed clock range.
4. SGX A50 holiday endpoints preserving frozen V5A same-contract semantics and target cutoff `<09:25:00`.
5. SGX A50 ordinary endpoints preserving frozen V6A same-contract semantics and target cutoff `<09:15:00`.
6. A source-manifest JSON frozen before evaluation.

The current repository already records local-origin paths for the 2015-2025 CSI1000/FRED pack in `data/high_open_dev_2015_2025/manifest.json`. Use the authoritative local files or byte-identical copies. Do not substitute an approximate A50 index, continuous contract, later cutoff, future-volume roll, or a different FX proxy.

## Source-manifest minimum contract

Before running, create a local JSON manifest containing source file hashes/provenance and these exact assertions:

```json
{
  "assertions": {
    "same_contract_all_events": true,
    "no_future_volume_or_oi_selection": true,
    "no_mid_window_roll": true,
    "no_forward_fill_or_interpolation": true,
    "blackbox_not_used_for_fit_or_rule_selection": true
  }
}
```

Additional provenance may be stored locally, but outcome details must not be committed.

## Execution

Use branch:

`codex/v6a-reusable-blackbox-20260909`

Run:

```bash
python3 scripts/run_v6a_reusable_blackbox_local.py \
  --panel '<LOCAL_2015_2025_ANNOTATED_PANEL.parquet>' \
  --nasdaq '<LOCAL_FRED_NASDAQ.csv>' \
  --vix '<LOCAL_FRED_VIX.csv>' \
  --hkma '<LOCAL_HKMA_USDCNY.parquet>' \
  --holiday-a50 '<LOCAL_SGX_A50_HOLIDAY_ENDPOINTS_2015_2025.parquet>' \
  --ordinary-a50 '<LOCAL_SGX_A50_ORDINARY_ENDPOINTS_2015_2025.parquet>' \
  --source-manifest '<LOCAL_V6A_BLACKBOX_SOURCE_MANIFEST.json>' \
  --protocol 'docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json' \
  --receipt-out 'docs/research/local_v6a_reusable_blackbox_receipt_v1.json'
```

Expected stdout is exactly one scientific state:

`PASS`, `FAIL`, or `INSUFFICIENT`.

## Allowed repository feedback

Commit only:

`docs/research/local_v6a_reusable_blackbox_receipt_v1.json`

The receipt contains only decision + non-outcome provenance hashes. Do **not** commit the local source manifest if it contains path inventories the owner does not want public; its SHA is sufficient in the receipt.

Use `[skip ci]`.

Do not edit the query ledger locally. Cloud review will verify the compact receipt and append exactly one ledger entry only after confirming an actual query occurred.

## Fail closed

If any source is missing, approximate, causally ambiguous or fails the frozen source contract, do **not** open the target outcomes and do not manufacture a PASS/FAIL. Return `INSUFFICIENT` only if the controller validly opened the frozen evaluation and source/coverage integrity prevents a scientific decision; otherwise report an execution/source blocker without creating a BLACKBOX query.

`production_authority=false`.
