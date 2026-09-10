# V6A reusable BLACKBOX local execution handoff

Date: 2026-09-10

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

## Source admission

Source admission is complete:

- decision: `SOURCE_PASS`
- authority: `docs/governance/global_spillover_v6a_source_admission_20260910.json`
- source pack: `data/v6a_external_sources_2015_2025/manifest.json`
- A50 raw source: Singapore Exchange official ZIP archives
- HKMA source: official HKMA USD/HKD and CNY/HKD cross

No further data transformation or source redesign is authorized or required before execution.

## Frozen authority

Current BLACKBOX protocol:

`docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json`

Reusable BLACKBOX policy:

`docs/governance/overnight_reusable_blackbox_policy_v1.json`

Historical V6 candidate authority remains frozen on branch:

`codex/overnight-next-explained-20260905`

with candidate code SHA:

`2ffec2a2ebfc3490ff0805e9b14680aa076a320e`

Do not change feature definitions, cutoff times, contract-selection rules, model family, alpha, missing-data rules, gates or sample rules.

## Exact in-repository inputs

Use these files exactly as committed on current `main`:

- panel: `data/high_open_dev_2015_2025/annotated_panel.parquet`
- NASDAQ: `data/high_open_dev_2015_2025/fred_nasdaq.csv`
- VIX: `data/high_open_dev_2015_2025/fred_vix.csv`
- HKMA: `data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet`
- holiday A50: `data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet`
- ordinary A50: `data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet`
- source manifest: `data/v6a_external_sources_2015_2025/manifest.json`
- protocol: `docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json`

Do not substitute any other files.

## Execution

From repository root, run exactly:

```bash
python3 scripts/run_v6a_reusable_blackbox_local.py \
  --panel data/high_open_dev_2015_2025/annotated_panel.parquet \
  --nasdaq data/high_open_dev_2015_2025/fred_nasdaq.csv \
  --vix data/high_open_dev_2015_2025/fred_vix.csv \
  --hkma data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet \
  --holiday-a50 data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet \
  --ordinary-a50 data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet \
  --source-manifest data/v6a_external_sources_2015_2025/manifest.json \
  --protocol docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json \
  --receipt-out docs/research/local_v6a_reusable_blackbox_receipt_v1.json
```

Expected stdout is exactly one scientific state:

`PASS`, `FAIL`, or `INSUFFICIENT`.

## Allowed repository feedback

Commit only the compact receipt:

`docs/research/local_v6a_reusable_blackbox_receipt_v1.json`

Use a commit message containing `[skip ci]`.

Do not commit internal metrics, debug tables, predictions, yearly/quarterly diagnostics or any temporary outcome artifacts.

Do not edit the BLACKBOX query ledger locally. Cloud review will verify the compact receipt and append exactly one ledger entry only after confirming an actual query occurred.

## Fail closed

If execution itself errors before a valid frozen evaluation is completed, do not manufacture `INSUFFICIENT`; report the execution error without creating a BLACKBOX ledger entry.

`production_authority=false`.
