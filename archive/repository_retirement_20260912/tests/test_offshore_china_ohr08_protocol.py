from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_ohr08_protocol_freezes_single_overlay_and_blackbox() -> None:
    p = json.loads((ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr08_frozen_base_overlay_v1.json").read_text())
    assert p["multiplicity"] == 1
    assert p["single_candidate"]["name"] == "frozen_incumbent_plus_one_dim_offshore_residual_overlay"
    assert p["single_candidate"]["g_definition"] == "broad_china_specific_vs_spy * 1(prev_last_hour < 0)"
    assert "fit_intercept=false" in p["single_candidate"]["stage_2_model"]
    assert p["accepted_source"]["sha256"] == "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
    assert p["evidence_boundary"]["sealed_repeat_blackbox"] == "2026-01-05_to_2026-08-21"
    assert p["evidence_boundary"]["repeat_blackbox_fresh_authority"] is False
    assert p["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert p["production_authority"] is False


def test_ohr08_selector_keeps_exact_incumbent_training_inventory() -> None:
    text = (ROOT / "scripts/select_offshore_china_ohr08_frozen_base_overlay_dev.py").read_text()
    assert "base_train_mask = highdiag.complete_mask(train, base_features)" in text
    assert "overlay_train_mask = overlay_common_mask(train, base_features)" in text
    assert "base.fit(x_base_train, y_base_train)" in text
    assert "reference_oof = reference_incumbent_common(frame, base_features)" in text
    assert '"stage1_exact_incumbent_replay": reference_score_max_abs <= EPS' in text
    assert "Stage-1 score drifted from exact incumbent replay" in text


def test_ohr08_overlay_has_one_raw_no_intercept_coefficient() -> None:
    text = (ROOT / "scripts/select_offshore_china_ohr08_frozen_base_overlay_dev.py").read_text()
    assert 'G = "broad_china_specific_tail_weak"' in text
    assert "QuantileRegressor(quantile=0.5, alpha=0.0, fit_intercept=False, solver=\"highs\")" in text
    assert "overlay.fit(g_train.reshape(-1, 1), residual)" in text
    assert "StandardScaler" not in text
    assert "beta_grid" not in text.lower() or '"beta_grid_search_performed": False' in text
    assert '"parameter_search_performed": False' in text
    assert '"beta_grid_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"quantile_search_performed": False' in text


def test_ohr08_outside_state_and_2026_are_fail_closed() -> None:
    text = (ROOT / "scripts/select_offshore_china_ohr08_frozen_base_overlay_dev.py").read_text()
    assert "np.array_equal(inc.loc[non_tail, \"score\"].to_numpy(), cand.loc[non_tail, \"score\"].to_numpy())" in text
    assert '"non_tail_predictions_identical_to_incumbent"' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text
    assert '"ohr_03_opened": False' in text
