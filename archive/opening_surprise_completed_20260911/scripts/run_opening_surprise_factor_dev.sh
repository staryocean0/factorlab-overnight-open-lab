#!/usr/bin/env bash
set -euo pipefail

python3 scripts/diagnose_opening_surprise_factor_dev.py \
  --base-panel data/development/csi1000_open_pit_panel.parquet \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --nasdaq data/high_open_dev_2015_2025/fred_nasdaq.csv \
  --vix data/high_open_dev_2015_2025/fred_vix.csv \
  --hkma data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet \
  --holiday-a50 data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet \
  --ordinary-a50 data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet \
  --protocol docs/governance/opening_surprise_factor_v1_protocol.json \
  --receipt-out docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json
