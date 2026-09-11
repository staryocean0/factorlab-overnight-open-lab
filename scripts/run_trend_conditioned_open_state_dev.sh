#!/usr/bin/env bash
set -euo pipefail

python3 scripts/diagnose_trend_conditioned_open_state_dev.py \
  --base-panel data/development/csi1000_open_pit_panel.parquet \
  --minute-bars data/high_open_dev_2015_2025/1m_official.parquet \
  --protocol docs/governance/trend_conditioned_open_state_v1_protocol.json \
  --receipt-out docs/research/local_trend_conditioned_open_state_dev_diagnostic_v1.json
