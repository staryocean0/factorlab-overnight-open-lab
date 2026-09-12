# Source implementations and execution boundary

Current metadata CLI: `python scripts/check_repository_consistency.py`.

The following frozen reference implementations/dependencies retain their original bytes and paths. Their historical main() entry points do not constitute an active research authorization; none is run by default CI. The source list is dependency-closed, while independent retired experiments live in the indexed archive.

- `scripts/build_driver_runtime_text_carrier.py`
- `scripts/build_gap_fill_v2_target_ledger.py`
- `scripts/build_runtime_text_carrier.py`
- `scripts/build_v6a_frozen_base_panel.py`
- `scripts/diagnose_driver_agreement_disagreement_dev.py`
- `scripts/diagnose_gap_fill_v2_phase1_factors.py`
- `scripts/diagnose_high_open_false_negatives_dev.py`
- `scripts/diagnose_offshore_china_price_discovery_dev.py`
- `scripts/diagnose_trend_conditioned_open_state_dev.py`
- `scripts/diagnose_volatility_conditioned_open_state_dev.py`
- `scripts/evaluate_gap_fill_v2_true_fresh_2026q4.py`
- `scripts/evaluate_local_2021_2025_two_head.py`
- `scripts/evaluate_local_gap_fill_v2_2026_repeat.py`
- `scripts/fit_gap_fill_v2_selected_dev.py`
- `scripts/run_driver_coherence_open_gap_blackbox.py`
- `scripts/run_global_risk_open_gap_blackbox.py`
- `scripts/run_single_external_driver_blackbox.py`
- `scripts/run_trend_conditioned_open_state_15m_blackbox_local.py`
- `scripts/run_v6a_reusable_blackbox_local.py`
- `scripts/run_volatility_conditioned_open_state_60m_blackbox_local.py`
- `scripts/select_clock_candidates_dev.py`
- `scripts/select_gap_fill_v2_phase2_hazard_family.py`
- `scripts/select_high_open_recall_phase2_dev.py`

Component mappings: `docs/governance/component_bindings_v1.json`. Historical path resolver: `python scripts/check_repository_consistency.py --resolve ORIGINAL_PATH`.
