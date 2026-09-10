#!/usr/bin/env bash
set -euo pipefail

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
