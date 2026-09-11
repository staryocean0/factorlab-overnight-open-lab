#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${OVERNIGHT_HISTORICAL_INDEX_1M_LAKE:?OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required}"
python3 scripts/run_relative_index_open_leadership_joint_blackbox_local.py
