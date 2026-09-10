#!/usr/bin/env bash
set -euo pipefail

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PANEL_TMP="$TMP_DIR/v6a_base_panel_2015_2025.parquet"
NASDAQ_TMP="$TMP_DIR/fred_nasdaq_normalized.csv"
VIX_TMP="$TMP_DIR/fred_vix_normalized.csv"

# Reconstruct the historical V6A base feature surface using the exact logic
# already present in evaluate_local_2021_2025_two_head.py. The builder first
# requires exact 2015-2020 parity with the frozen package panel. If parity fails,
# this script exits before any 2021-2025 BLACKBOX feature panel is materialized.
python3 scripts/build_v6a_frozen_base_panel.py \
  --raw-panel data/high_open_dev_2015_2025/annotated_panel.parquet \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --nasdaq data/high_open_dev_2015_2025/fred_nasdaq.csv \
  --vix data/high_open_dev_2015_2025/fred_vix.csv \
  --frozen-panel data/development/csi1000_open_pit_panel.parquet \
  --panel-out "$PANEL_TMP" \
  --nasdaq-normalized-out "$NASDAQ_TMP" \
  --vix-normalized-out "$VIX_TMP" \
  >/dev/null

# Only this command opens the reusable 2021-2025 BLACKBOX. It prints and
# persists no scientific detail beyond PASS / FAIL / INSUFFICIENT and compact
# non-outcome provenance in the receipt.
python3 scripts/run_v6a_reusable_blackbox_local.py \
  --panel "$PANEL_TMP" \
  --nasdaq "$NASDAQ_TMP" \
  --vix "$VIX_TMP" \
  --hkma data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet \
  --holiday-a50 data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet \
  --ordinary-a50 data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet \
  --source-manifest data/v6a_external_sources_2015_2025/manifest.json \
  --protocol docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json \
  --receipt-out docs/research/local_v6a_reusable_blackbox_receipt_v1.json
