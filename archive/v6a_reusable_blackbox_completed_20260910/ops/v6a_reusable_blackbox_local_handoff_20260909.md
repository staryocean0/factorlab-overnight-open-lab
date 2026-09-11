# V6A reusable BLACKBOX local execution handoff

Date: 2026-09-10

## Task

Execute exactly one reusable BLACKBOX query for the frozen Overnight identity:

`V6A_plus_ordinary_A50_preauction_closure`

Comparator: `V5A_common_sample_comparator`.

BLACKBOX window: `2021-01-01 .. 2025-12-31`.

This window is reusable BLACKBOX validation, not a one-time consumable dataset.

## Public-output rule

The only allowed scientific output is:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Do not return or commit exact metrics, sample counts, yearly/quarterly breakdowns, dates/events, subgroup diagnostics, attribution, probability details, failure clues or rescue suggestions.

## Source admission

External source admission is complete:

- decision: `SOURCE_PASS`;
- authority: `docs/governance/global_spillover_v6a_source_admission_20260910.json`;
- A50 raw source: Singapore Exchange official ZIP archives;
- HKMA: official USD/HKD and CNY/HKD cross;
- source pack: `data/v6a_external_sources_2015_2025/manifest.json`.

No further A50/HKMA data work is required.

## Resolved execution incident

The first in-repository attempt stopped before BLACKBOX execution because `data/high_open_dev_2015_2025/annotated_panel.parquet` is a raw Overnight annotation panel, not the historical V6A base-feature surface. It therefore does not directly contain `gap`, `r1`, `r20`, and the other frozen baseline features.

This is now fixed without changing the scientific identity.

The repository already contained the exact reconstruction logic in:

`scripts/evaluate_local_2021_2025_two_head.py`

The new builder:

`scripts/build_v6a_frozen_base_panel.py`

reuses those functions. Before any 2021-2025 feature panel is materialized it reconstructs only 2015-2020 and requires exact, zero-tolerance parity against:

`data/development/csi1000_open_pit_panel.parquet`

The governing reconstruction contract is:

`docs/governance/v6a_base_panel_reconstruction_contract_20260910.json`

If that parity gate fails, execution exits before the BLACKBOX is opened.

If parity passes, the 2015-2025 base panel is created only in a temporary directory, passed to the frozen BLACKBOX controller, and automatically deleted on exit. It must never be committed.

## Frozen authority

Current BLACKBOX protocol:

`docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json`

Historical V6 candidate authority remains frozen on branch `codex/overnight-next-explained-20260905`, candidate code SHA `2ffec2a2ebfc3490ff0805e9b14680aa076a320e`.

Do not change feature definitions, cutoff times, contract-selection rules, model family, alpha, missing-data rules, gates or sample rules.

## Execution

From repository root:

```bash
git pull
bash scripts/run_v6a_reusable_blackbox_inrepo.sh
```

The wrapper performs, in order:

1. development-only exact reconstruction parity;
2. temporary frozen base-panel extension through 2025;
3. temporary FRED date-column normalization only;
4. exactly one V6A reusable BLACKBOX query;
5. automatic temporary-file deletion.

If the first three stages error, the BLACKBOX has not produced a scientific decision and no ledger entry should be created.

Expected scientific stdout from the final controller is exactly one state: `PASS`, `FAIL`, or `INSUFFICIENT`.

## Allowed repository feedback

Commit only:

`docs/research/local_v6a_reusable_blackbox_receipt_v1.json`

Use `[skip ci]`.

Do not commit the temporary panel, normalized FRED files, internal metrics, predictions or diagnostics. Do not edit the BLACKBOX ledger locally; cloud review will append exactly one ledger entry only after verifying the compact receipt.

`production_authority=false`.
