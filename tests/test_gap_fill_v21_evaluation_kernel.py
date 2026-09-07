from pathlib import Path
import json
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import v21_evaluation_kernel as ev

CONTRACT = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_evaluation_kernel_contract_v1.json"
FAMILY = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_candidate_family_v1.json"
STATE = ROOT / "docs/governance/gap_fill_v21_state_v1.json"


def synthetic_block(years=(2016, 2017, 2018), per_year=30, gap=0.002):
    n = len(years) * per_year
    yy = np.resize(np.array([0.0, 1.0]), n)
    yr = np.repeat(np.asarray(years, dtype=int), per_year)
    gaps = np.full(n, float(gap))
    candidate = np.where(yy > 0.5, 0.80, 0.20)
    control = np.where(yy > 0.5, 0.70, 0.30)
    benchmark = np.where(yy > 0.5, 0.65, 0.35)
    return yy, yr, gaps, candidate, control, benchmark


def test_metric_definitions_are_literal():
    y = np.array([0.0, 1.0])
    p = np.array([0.25, 0.75])
    assert np.isclose(ev.brier_score(y, p), 0.0625)
    expected_ll = -0.5 * (np.log(0.75) + np.log(0.75))
    assert np.isclose(ev.log_loss(y, p), expected_ll)
    assert np.isclose(ev.two_horizon_mean_brier(y, y, p, p), 0.0625)
    assert np.isclose(ev.two_horizon_mean_log_loss(y, y, p, p), expected_ll)


def test_dev_primary_good_synthetic_candidate_passes_all_gates():
    y, years, gaps, candidate, control, benchmark = synthetic_block()
    result = ev.evaluate_dev_primary(
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        beta_histories={"shared": [0.2, -0.1, 0.3]},
        monotonicity_violations=0,
    )
    assert result["status"] == "eligible"
    assert result["eligible"] is True
    assert result["sample"]["pooled_gt10"] == 90
    assert result["sample"]["by_validation_year_gt10"] == {"2016": 30, "2017": 30, "2018": 30}
    assert all(result["gates"].values())


def test_dev_primary_both_horizons_are_required_not_averaged_rescue():
    y, years, gaps, candidate, control, benchmark = synthetic_block()
    bad60 = np.where(y > 0.5, 0.55, 0.45)
    result = ev.evaluate_dev_primary(
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=bad60,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        beta_histories={"shared": [0.2, 0.1, 0.3]},
        monotonicity_violations=0,
    )
    assert result["eligible"] is False
    assert result["gates"]["primary_gt10_15m_brier_strictly_better_than_geometry_control"] is True
    assert result["gates"]["primary_gt10_60m_brier_strictly_better_than_geometry_control"] is False


def test_dev_sample_shortfall_is_evidence_insufficient_not_date_relaxation():
    y, years, gaps, candidate, control, benchmark = synthetic_block(per_year=19)
    result = ev.evaluate_dev_primary(
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        beta_histories={"shared": [0.2, 0.1, 0.3]},
        monotonicity_violations=0,
    )
    assert result["status"] == "evidence_insufficient"
    assert result["eligible"] is False
    assert result["gates"] == {}


def test_beta_direction_must_emerge_in_two_of_three_fits():
    y, years, gaps, candidate, control, benchmark = synthetic_block()
    result = ev.evaluate_dev_primary(
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        beta_histories={"shared": [-0.2, -0.1, 0.3]},
        monotonicity_violations=0,
    )
    assert result["eligible"] is False
    assert result["gates"]["each_beta_component_direction_stable"] is False


def test_cross_index_shared_candidate_has_nonharm_gate():
    y, _, gaps, candidate, control, _ = synthetic_block()
    passed = ev.evaluate_cross_index_shared_nonharm(
        y15=y, y60=y, abs_gap=gaps,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
    )
    assert passed["passed"] is True
    harmful = np.where(y > 0.5, 0.55, 0.45)
    failed = ev.evaluate_cross_index_shared_nonharm(
        y15=y, y60=y, abs_gap=gaps,
        candidate15=harmful, candidate60=harmful,
        control15=control, control60=control,
    )
    assert failed["passed"] is False


def test_audit_good_candidate_passes_even_if_gt30_is_only_descriptively_insufficient():
    y, years, gaps, candidate, control, benchmark = synthetic_block(years=(2019, 2020, 2021), gap=0.002)
    result = ev.evaluate_future_audit_primary(
        expected_years=ev.AUDIT_A_YEARS,
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        monotonicity_violations=0,
    )
    assert result["status"] == "pass"
    assert result["passed"] is True
    assert result["sample"]["gt30_descriptive_reporting_sufficient"] is False
    assert result["sample"]["primary_sufficient"] is True
    assert all(result["gates"].values())


def test_audit_requires_all_three_frozen_years_for_annual_gate():
    y, years, gaps, candidate, control, benchmark = synthetic_block(years=(2019, 2020), per_year=30)
    result = ev.evaluate_future_audit_primary(
        expected_years=ev.AUDIT_A_YEARS,
        y15=y, y60=y, abs_gap=gaps, years=years,
        candidate15=candidate, candidate60=candidate,
        control15=control, control60=control,
        benchmark15=benchmark, benchmark60=benchmark,
        monotonicity_violations=0,
    )
    assert result["status"] == "evidence_insufficient"
    assert result["passed"] is False
    assert result["sample"]["by_full_year_gt10"]["2021"] == 0


def test_audit_rejects_row_outside_frozen_calendar():
    y, years, gaps, candidate, control, benchmark = synthetic_block(years=(2019, 2020, 2022), per_year=30)
    with pytest.raises(ValueError, match="outside frozen audit calendar"):
        ev.evaluate_future_audit_primary(
            expected_years=ev.AUDIT_A_YEARS,
            y15=y, y60=y, abs_gap=gaps, years=years,
            candidate15=candidate, candidate60=candidate,
            control15=control, control60=control,
            benchmark15=benchmark, benchmark60=benchmark,
            monotonicity_violations=0,
        )


def test_contract_and_repo_state_keep_kernel_pure_and_future_sealed():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    f = json.loads(FAMILY.read_text(encoding="utf-8"))
    s = json.loads(STATE.read_text(encoding="utf-8"))
    assert c["implementation_scope"] == "pure_array_evaluation_only_no_file_IO_no_model_fit_no_market_data_access"
    assert c["numeric_contract"]["strict_comparison_epsilon"] == 1e-12
    assert c["future_audit_sample_contract"]["gt30_descriptive_shortfall_blocks_primary_confirmation"] is False
    assert c["V21_DEV_outcomes_open_authorized"] is False
    assert c["Audit_A_outcomes_open_authorized"] is False
    assert c["Audit_B_outcomes_open_authorized"] is False
    assert f["V21_DEV_outcomes_open_authorized"] is False
    assert s["evaluation_kernel"]["contract"] == "docs/governance/cloud_session_20260907_gap_fill_v21_evaluation_kernel_contract_v1.json"
    assert s["evaluation_kernel"]["implementation"] == "scripts/v21_evaluation_kernel.py"
    assert s["evaluation_kernel"]["file_IO_authority"] is False
    assert s["evaluation_kernel"]["model_fit_authority"] is False
    assert s["evaluation_kernel"]["future_outcome_authority"] is False
    assert s["sealed"]["V21_DEV_outcomes"] is True
    assert s["sealed"]["V21_AUDIT_A_outcomes"] is True
    assert s["sealed"]["V21_AUDIT_B_outcomes"] is True
    source = (ROOT / "scripts/v21_evaluation_kernel.py").read_text(encoding="utf-8")
    assert "read_parquet" not in source
    assert "open(" not in source
    assert ".fit(" not in source
