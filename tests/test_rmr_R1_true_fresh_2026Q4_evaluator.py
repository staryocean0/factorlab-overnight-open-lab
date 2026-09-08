from datetime import date
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_rmr_R1_true_fresh_2026Q4 as mod


def test_evaluator_is_no_fit_and_date_sealed():
    source = (ROOT / "scripts/evaluate_rmr_R1_true_fresh_2026Q4.py").read_text(encoding="utf-8")
    assert ".fit(" not in source
    assert "LogisticRegression" not in source
    with pytest.raises(RuntimeError):
        mod.validate_execution_date(date(2026, 12, 31))
    mod.validate_execution_date(date(2027, 1, 1))


def test_authorization_must_bind_exact_source_and_evaluator(tmp_path):
    future = tmp_path / "future.parquet"
    future.write_bytes(b"future-source-identity-only")
    future_sha = mod.sha256(future)
    auth = {
        "schema_id": mod.EXPECTED_AUTH_SCHEMA,
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "parameter_bundle_sha256": "e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c",
        "selected_candidate_id": "R1_PARENT_COMPOSITE_1D",
        "context_window": {"start": mod.FUTURE_START, "end": mod.FUTURE_END},
        "challenge_window": {"start": mod.Q4_START, "end": mod.Q4_END},
        "source_admission_cloud_review_decision": mod.EXPECTED_SOURCE_REVIEW_DECISION,
        "source_admission_receipt_sha256": "a" * 64,
        "exact_trading_calendar_sha256": "b" * 64,
        "exact_2026_extension_source_sha256": future_sha,
        "evaluator_blob_sha": mod.git_blob_sha(Path(mod.__file__)),
        "authorization_flags": {
            "Q4_R1_outcome_open_authorized": True,
            "R1_refit_authorized": False,
            "candidate_change_authorized": False,
            "scale_or_threshold_change_authorized": False,
            "calibration_authorized": False,
            "PnL_use_authorized": False,
            "production_authority": False,
        },
    }
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth), encoding="utf-8")
    loaded, actual = mod.validate_authorization(path, future)
    assert actual == future_sha
    assert loaded["authorization_flags"]["Q4_R1_outcome_open_authorized"] is True

    auth["exact_2026_extension_source_sha256"] = "0" * 64
    path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(RuntimeError):
        mod.validate_authorization(path, future)


def test_combine_sources_rejects_duplicate_minute_identity():
    hist = pd.DataFrame(
        {
            "symbol": [mod.SYMBOL],
            "trading_day": ["2025-12-31"],
            "timestamp": ["2025-12-31 15:00:00"],
            "close": [1.0],
        }
    )
    fut = pd.DataFrame(
        {
            "symbol": [mod.SYMBOL, mod.SYMBOL],
            "trading_day": ["2026-01-05", "2026-12-31"],
            "timestamp": ["2026-01-05 09:31:00", "2026-12-31 15:00:00"],
            "close": [1.0, 1.1],
        }
    )
    combined = mod.combine_sources(hist, fut)
    assert combined.iloc[-1]["trading_day"] == "2026-12-31"

    bad = pd.concat([fut, fut.iloc[[1]]], ignore_index=True)
    with pytest.raises(RuntimeError):
        mod.combine_sources(hist, bad)


def test_q4_pair_gate_uses_frozen_probabilities_and_q4_days_only():
    rows = []
    for _ in range(25):
        rows.append(
            {
                "day": "2026-10-08",
                "severity": 1.0,
                "abs_drift": 3.0,
                "overlap": 0.0,
                "parent_eff": 0.0,
                "outcome": "recovery",
            }
        )
        rows.append(
            {
                "day": "2026-11-02",
                "severity": 1.0,
                "abs_drift": 0.0,
                "overlap": 3.0,
                "parent_eff": 0.0,
                "outcome": "failure",
            }
        )
    rows.append(
        {
            "day": "2026-09-30",
            "severity": 1.0,
            "abs_drift": 3.0,
            "overlap": 0.0,
            "parent_eff": 0.0,
            "outcome": "recovery",
        }
    )
    events = pd.DataFrame(rows)
    frozen_pair = {
        "parent_feature_scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "severity_baseline_model": {
            "scaler": {"mean": [0.0], "scale": [1.0]},
            "logistic": {"coef": [0.0], "intercept": 0.0},
        },
        "selected_candidate_model": {
            "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]},
            "logistic": {"coef": [0.0, 1.0], "intercept": 0.0},
        },
    }
    result = mod.q4_pair_result(events, frozen_pair, minimum_resolved=40)
    assert result["inventory"]["resolved"] == 50
    assert result["gates"]["sample_minimum"] is True
    assert result["gates"]["brier_better"] is True
    assert result["gates"]["logloss_better"] is True
    assert result["passed"] is True


def test_decision_rule_distinguishes_insufficient_fail_and_confirmed():
    confirmed = {
        "PAIR_A": {"gates": {"sample_minimum": True}, "passed": True},
        "PAIR_B": {"gates": {"sample_minimum": True}, "passed": True},
    }
    assert mod.decide(confirmed).endswith("confirmed")

    failed = {
        "PAIR_A": {"gates": {"sample_minimum": True}, "passed": True},
        "PAIR_B": {"gates": {"sample_minimum": True}, "passed": False},
    }
    assert mod.decide(failed).endswith("failed")

    insufficient = {
        "PAIR_A": {"gates": {"sample_minimum": True}, "passed": True},
        "PAIR_B": {"gates": {"sample_minimum": False}, "passed": False},
    }
    assert mod.decide(insufficient).endswith("evidence_insufficient")


def test_protocol_preserves_q4_only_and_no_2027_resolution():
    protocol = json.loads(
        (ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_protocol_v1.json").read_text()
    )
    assert protocol["causal_reconstruction"]["challenge_event_filter"] == "event_confirmation_day_between_2026_10_01_and_2026_12_31"
    assert protocol["causal_reconstruction"]["use_2027Q1_prices_to_resolve_late_Q4_events"] is False
    assert protocol["model_use"]["refit"] is False
    assert protocol["gates"]["PAIR_A"]["minimum_resolved"] == 40
    assert protocol["gates"]["PAIR_B"]["minimum_resolved"] == 15
