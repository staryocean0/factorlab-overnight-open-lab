from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_regime_diagnostic_protocol_v1.json"
RUNNER = ROOT / "scripts/diagnose_gap_fill_v21_regime_consumed.py"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_identity_and_parent_failure_are_frozen():
    p = protocol()
    assert p["research_identity"] == "gap_fill_v2_1_regime_conditioned_successor"
    assert p["stage"] == "V21_RD1_consumed_evidence_mechanism_diagnostic_before_successor_family"
    assert p["parent_failure_decision"] == "CT_AUDIT_B_final_backward_external_not_confirmed"
    assert p["old_identity_must_not_be_rewritten"] == "gap_fill_cross_index_transport_v1"
    assert p["frozen_base_architecture"]["CSI300_bundle_sha256"] == "87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb"
    assert p["frozen_base_architecture"]["CSI500_bundle_sha256"] == "6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957"


def test_primary_cell_and_five_probes_are_fixed():
    p = protocol()
    assert p["primary_cell"] == {
        "index": "CSI500",
        "sign": "high",
        "cohort": "abs_gap_gt_10bp",
        "horizons": ["fill_15m", "fill_60m"],
    }
    probes = p["probes"]
    assert len(probes) == 5
    assert [x["id"] for x in probes] == [
        "P1_common_gap_support",
        "P2_relative_gap_excess",
        "P3_trend20_alignment",
        "P4_prior_daytime_alignment",
        "P5_relative_momentum5_alignment",
    ]
    assert [x["expected_beta_sign"] for x in probes] == ["negative", "positive", "negative", "negative", "negative"]


def test_diagnostic_is_one_parameter_and_not_candidate_authority():
    p = protocol()
    d = p["diagnostic_model"]
    assert d["beta_dimension"] == 1
    assert d["beta_bounds"] == [-6.0, 6.0]
    assert d["minimum_cell_rows"] == 20
    assert d["calibration_layer_authority"] is False
    assert d["candidate_model_authority"] is False
    gates = p["mechanism_admission_rule"]
    assert len(gates) == 7
    assert all(gates.values())


def test_future_partitions_are_preallocated_and_outcomes_forbidden():
    p = protocol()
    assert p["future_external_partitions_frozen_before_outcome_open"] == {
        "V21_DEV": {"start": "2015-01-01", "end": "2018-12-31"},
        "V21_AUDIT_A": {"start": "2019-01-01", "end": "2021-12-31"},
        "V21_AUDIT_B": {"start": "2022-01-01", "end": "2024-12-31"},
        "V21_EXTERNAL_RESERVE": {"start": "2025-01-01", "end": "2026-08-21"},
    }
    inv = p["future_partition_inventory"]
    assert inv["allowed_columns"] == ["symbol", "trading_day", "timestamp"]
    assert inv["OHLC_read_allowed"] is False
    assert inv["gap_or_fill_target_construction_allowed"] is False
    assert inv["model_scoring_allowed"] is False
    assert any("2014-10-17" in x for x in p["forbidden_outcome_windows"])
    assert any("2015-01-01" in x for x in p["forbidden_outcome_windows"])


def test_runner_hard_denies_future_outcome_open_and_successor_fit():
    text = RUNNER.read_text(encoding="utf-8")
    assert "CONSUMED_END = \"2014-10-16\"" in text
    assert "frame[\"trading_day\"] >= \"2014-10-17\"" in text
    assert 'columns=["symbol", "trading_day", "timestamp"]' in text
    assert '"future_external_OHLC_read": False' in text
    assert '"future_external_gap_fill_or_model_scores_opened": False' in text
    assert '"2014Q4_supporting_crosscheck_opened": False' in text
    assert '"V21_DEV_outcomes_opened": False' in text
    assert '"successor_model_fit_performed": False' in text
    assert '"successor_model_selection_performed": False' in text
    assert "LogisticRegression" not in text
    assert ".fit(" not in text


def test_runner_uses_frozen_offset_bounds_and_primary_material_gap():
    text = RUNNER.read_text(encoding="utf-8")
    assert "BETA_BOUNDS = (-6.0, 6.0)" in text
    assert "MIN_CELL_ROWS = 20" in text
    assert "minimize_scalar" in text
    assert '(scored["CSI500"]["abs_gap"] > 0.001)' in text
    assert '(scored["CSI300"]["abs_gap"] > 0.001)' in text


def test_rd1_outputs_not_preexisting_before_execution():
    assert not (ROOT / "docs/research/local_gap_fill_v21_regime_diagnostic_receipt_v1.json").exists()
    assert not (ROOT / "docs/governance/local_gap_fill_v21_regime_diagnostic_data_usage_v1.json").exists()
