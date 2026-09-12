# D1 joint 15m+30m+60m reusable BLACKBOX — local mechanical handoff

Date: 2026-09-12

Repository: `staryocean0/factorlab-overnight-open-lab`

## Responsibility boundary

Cloud main agent has completed and adjudicated the 2015-2020 D1 development stage. The parent identity `overnight_relative_size_open_leadership_v1` progressed jointly at all three frozen horizons. A separate successor identity has now been frozen:

`overnight_relative_size_open_leadership_joint_15m_30m_60m_v1`

Local execution is **mechanical compact BLACKBOX execution only**. Do not inspect, print, persist, chart, summarize, decompose, or tune from any 2021-2025 hidden metric or calendar-year result.

## Exact source

Use the admitted Unified DataHub canonical 1m lake:

```bash
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE="/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
```

## Exact command

```bash
git pull --ff-only
bash scripts/run_relative_index_open_leadership_joint_blackbox.sh
```

Stdout is allowed to be exactly one scientific state:

- `PASS`
- `FAIL`
- `INSUFFICIENT`

Expected compact receipt:

`docs/research/local_relative_index_open_leadership_joint_blackbox_receipt_v1.json`

The receipt must contain no hidden metrics, annual results, sample counts, bootstrap values, or failure attribution.

## Frozen identity

- pair: CSI1000 (`000852.SH`) versus CSI300 (`000300.SH`)
- CSI500 substitution: forbidden
- coordinate: `gap_rvol_CSI1000 - gap_rvol_CSI300`
- controls: `common_open_component`, `relative_r1`, `relative_log_rvol`
- targets: 09:35->09:50, 09:35->10:05, 09:35->10:35 relative returns
- joint rule: all three horizons must satisfy the frozen protocol for PASS
- unique post-hoc horizon winner: forbidden

## Hard prohibitions

Do not create 2021-2025 row-level CSV or text shards. Do not persist any internal BLACKBOX diagnostics. Do not modify the protocol/controller after seeing the decision. Do not substitute CSI500, search index pairs, change clocks, change rvol lookback, add thresholds/buckets, optimize strategy PnL, or inspect hidden failure clues.

Do not modify the reusable BLACKBOX ledger, registry, current authority or scientific state locally. Cloud main agent owns provenance acceptance, ledger registration and final product adjudication.

## Commit rule

After successful controller execution, verify that the only new scientific file is the compact receipt, then:

```bash
git add docs/research/local_relative_index_open_leadership_joint_blackbox_receipt_v1.json
git commit -m "Record D1 joint reusable BLACKBOX receipt [skip ci]"
git push
```

Then stop and report only the final commit SHA and public decision. Do not report hidden diagnostics even if visible in process memory.
