#!/usr/bin/env bash
set -euo pipefail

python3 scripts/diagnose_trend_conditioned_open_state_dev.py \
  --dev-pack-dir data/development/trend_open_state_dev_pack_2019_2020 \
  --protocol docs/governance/trend_conditioned_open_state_v1_protocol.json \
  --receipt-out docs/research/cloud_trend_conditioned_open_state_dev_diagnostic_v1.json
