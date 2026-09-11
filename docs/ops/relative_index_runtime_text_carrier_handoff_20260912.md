# D1 relative-index runtime text carrier — local mechanical handoff

Date: 2026-09-12

Repository: `staryocean0/factorlab-overnight-open-lab`

## Responsibility boundary

The cloud main agent has already completed source admission and frozen the D1 v1 scientific identity before any D1 outcome inspection.

Local execution is **data engineering only**. Do not run a D1 regression, inspect relative-return behavior, change the index pair, tune clocks, choose horizons, add thresholds, or open any 2021-2025 BLACKBOX detail.

D1 v1 candidate is already frozen as CSI1000 versus CSI300. CSI500 is included only in the carrier inventory and must not be substituted into the candidate.

## Exact command

```bash
git pull --ff-only
export OVERNIGHT_HISTORICAL_INDEX_1M_LAKE="/home/starryocean/桌面/量化/unified_datahub/.runtime/live/lake/bars/dataset_version=bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
python3 scripts/build_relative_index_runtime_text_carrier.py \
  --source "$OVERNIGHT_HISTORICAL_INDEX_1M_LAKE" \
  --csi1000-factor-runtime-root data/runtime_text_2015_2025 \
  --out-dir data/relative_index_runtime_text_2015_2020 \
  --receipt-out docs/research/relative_index_runtime_text_carrier_parity_receipt_v1.json
```

Expected stdout marker:

`RELATIVE_INDEX_RUNTIME_TEXT_CARRIER_COMPLETE`

Expected outputs:

- `data/relative_index_runtime_text_2015_2020/relative_index_open_carrier_2015.csv` through `relative_index_open_carrier_2020.csv`
- `data/relative_index_runtime_text_2015_2020/manifest.json`
- `data/relative_index_runtime_text_2015_2020/README.md`
- `docs/research/relative_index_runtime_text_carrier_parity_receipt_v1.json`

## Hard prohibitions

Do not generate or commit any 2021-2025 row-level CSV. Do not change `relative_index_open_leadership_v1_protocol.json`, `relative_index_open_leadership_v1_state.json`, registry, current authority, BLACKBOX ledger, or scientific conclusions. Do not use nearest-clock substitution, forward fill, backward fill, resampling, alternative opening clocks, alternate volatility windows, CSI500 candidate substitution, V2.1 P2 formulas, Gap-Fill targets, or strategy PnL.

If the builder fails because the local source schema differs from the frozen source reader assumption, stop and report the exact traceback. Do not weaken the evidence boundary to make it run.

## Commit rule

After a successful run, verify `git status`, then commit only the carrier directory and carrier receipt:

```bash
git add data/relative_index_runtime_text_2015_2020 \
  docs/research/relative_index_runtime_text_carrier_parity_receipt_v1.json
git commit -m "Materialize D1 2015-2020 relative-index runtime carrier [skip ci]"
git push
```

Report the execution HEAD, source path/version, stdout marker, parity status, whether any post-2020 rows/text were generated, and final commit SHA. Then stop. The cloud main agent owns D1 six-year development execution and adjudication after carrier acceptance.
