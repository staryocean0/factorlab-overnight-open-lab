# Current QA test scope

Default tests have a collection-time data/network barrier. They verify metadata, frozen bytes, selected reference functions on synthetic inputs, and retained Gap-Fill/architecture contracts. They do not measure factor performance or run backtests.

Retained original tests:

- `tests/test_gap_fill_prediction_v2_protocol.py`
- `tests/test_gap_fill_v2_2026_repeat_protocol.py`
- `tests/test_gap_fill_v2_final_fit_protocol.py`
- `tests/test_gap_fill_v2_phase2_hazard_family.py`
- `tests/test_gap_fill_v2_true_fresh_protocol.py`
- `tests/test_local_2026_direction_receipt.py`
- `tests/test_local_two_head_receipt.py`

New regression suites: `tests/test_repository_consistency.py` and `tests/test_frozen_coordinate_regression.py`; barrier: `tests/conftest.py`.

Other original tests are archived by experiment scope, not deleted to hide a failing computation. The baseline run recorded 124 cases, 120 passing and 4 obsolete stage-state assertions failing; three real-carrier integration modules were intentionally excluded from that run. Numerical/synthetic assertions for archived experiments remain in the baseline archive and are not represented as current-product QA coverage.
