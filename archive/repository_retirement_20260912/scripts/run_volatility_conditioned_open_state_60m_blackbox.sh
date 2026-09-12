#!/usr/bin/env bash
set -euo pipefail

TMPDIR_LOCAL="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR_LOCAL"
}
trap cleanup EXIT

python3 scripts/build_v6a_frozen_base_panel.py \
  --raw-panel data/high_open_dev_2015_2025/annotated_panel.parquet \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --nasdaq data/high_open_dev_2015_2025/fred_nasdaq.csv \
  --vix data/high_open_dev_2015_2025/fred_vix.csv \
  --frozen-panel data/development/csi1000_open_pit_panel.parquet \
  --panel-out "$TMPDIR_LOCAL/frozen_panel_2015_2025.parquet" \
  --nasdaq-normalized-out "$TMPDIR_LOCAL/fred_nasdaq_normalized.csv" \
  --vix-normalized-out "$TMPDIR_LOCAL/fred_vix_normalized.csv" \
  >/dev/null

python3 scripts/run_volatility_conditioned_open_state_60m_blackbox_local.py \
  --panel "$TMPDIR_LOCAL/frozen_panel_2015_2025.parquet" \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --raw-panel data/high_open_dev_2015_2025/annotated_panel.parquet \
  --nasdaq data/high_open_dev_2015_2025/fred_nasdaq.csv \
  --vix data/high_open_dev_2015_2025/fred_vix.csv \
  --frozen-panel data/development/csi1000_open_pit_panel.parquet \
  --source-manifest data/high_open_dev_2015_2025/manifest.json \
  --base-manifest data/manifest.json \
  --reconstruction-contract docs/governance/v6a_base_panel_reconstruction_contract_20260910.json \
  --protocol docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json \
  --receipt-out docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json
