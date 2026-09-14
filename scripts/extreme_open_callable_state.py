from __future__ import annotations
import math
from typing import Mapping

SCHEMA_ID = "overnight_extreme_open_callable_state@1.0"
EVIDENCE_LABEL = "DEV_PROGRESSION_ONLY_NOT_REUSABLE_VALIDATED"

EDGES = {
    "B1_global_risk": {"q1": -0.20658745938920686, "q2": 0.3617976846900284},
    "B2_china_offshore": {"q1": -0.13148580359538747, "q2": 0.47579244128414716},
    "B4_driver_coherence": {"q1": -0.42760610092652673, "q2": 1.0},
    "causal_prior_volatility_parent": {"q1": -4.4724644437027035, "q2": -3.9107816033032954},
}

P1_ORDER = (
    "P1_UP_B1_HIGH", "P1_UP_B2_HIGH", "P1_UP_VOL_HIGH",
    "P1_DOWN_B1_LOW", "P1_DOWN_B2_LOW", "P1_DOWN_B4_LOW",
)
P1 = {
    "P1_UP_B1_HIGH": ("EXTREME_UP", "B1_global_risk", "HIGH"),
    "P1_UP_B2_HIGH": ("EXTREME_UP", "B2_china_offshore", "HIGH"),
    "P1_UP_VOL_HIGH": ("EXTREME_UP", "causal_prior_volatility_parent", "HIGH"),
    "P1_DOWN_B1_LOW": ("EXTREME_DOWN", "B1_global_risk", "LOW"),
    "P1_DOWN_B2_LOW": ("EXTREME_DOWN", "B2_china_offshore", "LOW"),
    "P1_DOWN_B4_LOW": ("EXTREME_DOWN", "B4_driver_coherence", "LOW"),
}

P3_ORDER = (
    "UP_B1_HIGH_X_B2_HIGH", "UP_B1_HIGH_X_VOL_HIGH", "UP_B2_HIGH_X_VOL_HIGH",
    "DOWN_B1_LOW_X_B2_LOW", "DOWN_B1_LOW_X_B4_LOW", "DOWN_B2_LOW_X_B4_LOW",
)
P3 = {
    "UP_B1_HIGH_X_B2_HIGH": {
        "target": "EXTREME_UP", "requires": ("P1_UP_B1_HIGH", "P1_UP_B2_HIGH"),
        "dev_event_probability": 0.44776119402985076, "dev_parent_probability": 0.1736613603473227,
        "dev_incremental_lift_pp_over_stronger_constituent": 8.776119402985078,
    },
    "UP_B1_HIGH_X_VOL_HIGH": {
        "target": "EXTREME_UP", "requires": ("P1_UP_B1_HIGH", "P1_UP_VOL_HIGH"),
        "dev_event_probability": 0.5166666666666667, "dev_parent_probability": 0.17445054945054944,
        "dev_incremental_lift_pp_over_stronger_constituent": 19.782608695652183,
    },
    "UP_B2_HIGH_X_VOL_HIGH": {
        "target": "EXTREME_UP", "requires": ("P1_UP_B2_HIGH", "P1_UP_VOL_HIGH"),
        "dev_event_probability": 0.5454545454545454, "dev_parent_probability": 0.17316017316017315,
        "dev_incremental_lift_pp_over_stronger_constituent": 18.545454545454543,
    },
    "DOWN_B1_LOW_X_B2_LOW": {
        "target": "EXTREME_DOWN", "requires": ("P1_DOWN_B1_LOW", "P1_DOWN_B2_LOW"),
        "dev_event_probability": 0.6434108527131783, "dev_parent_probability": 0.2098408104196816,
        "dev_incremental_lift_pp_over_stronger_constituent": 15.514794191505626,
    },
    "DOWN_B1_LOW_X_B4_LOW": {
        "target": "EXTREME_DOWN", "requires": ("P1_DOWN_B1_LOW", "P1_DOWN_B4_LOW"),
        "dev_event_probability": 0.5773809523809523, "dev_parent_probability": 0.2098408104196816,
        "dev_incremental_lift_pp_over_stronger_constituent": 8.911804158283026,
    },
    "DOWN_B2_LOW_X_B4_LOW": {
        "target": "EXTREME_DOWN", "requires": ("P1_DOWN_B2_LOW", "P1_DOWN_B4_LOW"),
        "dev_event_probability": 0.546448087431694, "dev_parent_probability": 0.2098408104196816,
        "dev_incremental_lift_pp_over_stronger_constituent": 6.527653931453925,
    },
}


def _finite(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def bucket_for(coordinate: str, value) -> str | None:
    if coordinate not in EDGES or not _finite(value):
        return None
    v = float(value)
    q1, q2 = EDGES[coordinate]["q1"], EDGES[coordinate]["q2"]
    if v <= q1:
        return "LOW"
    if v <= q2:
        return "MID"
    return "HIGH"


def evaluate_extreme_open_state(coordinates: Mapping[str, float | int | None]) -> dict:
    buckets = {name: bucket_for(name, coordinates.get(name)) for name in EDGES}
    missing_inputs = [name for name in EDGES if buckets[name] is None]

    supporting = []
    fired_p1 = set()
    for state_id in P1_ORDER:
        target, coord, required_bucket = P1[state_id]
        if buckets[coord] == required_bucket:
            fired_p1.add(state_id)
            supporting.append({"state_id": state_id, "target": target})

    fired = []
    targets = set()
    for state_id in P3_ORDER:
        spec = P3[state_id]
        if all(req in fired_p1 for req in spec["requires"]):
            targets.add(spec["target"])
            fired.append({
                "state_id": state_id,
                "target": spec["target"],
                "event_threshold_bp": 30,
                "evidence_label": EVIDENCE_LABEL,
                "dev_event_probability": spec["dev_event_probability"],
                "dev_parent_probability": spec["dev_parent_probability"],
                "dev_incremental_lift_pp_over_stronger_constituent": spec["dev_incremental_lift_pp_over_stronger_constituent"],
            })

    if not fired:
        primary_action = "ABSTAIN_NO_P3_STATE"
        target_consensus = None
    elif len(targets) == 1:
        primary_action = "STATE_SET"
        target_consensus = next(iter(targets))
    else:
        primary_action = "ABSTAIN_TARGET_CONFLICT"
        target_consensus = None

    return {
        "schema_id": SCHEMA_ID,
        "primary_action": primary_action,
        "target_consensus": target_consensus,
        "fired_states": fired,
        "supporting_univariate_states": supporting,
        "coordinate_buckets": buckets,
        "missing_inputs": missing_inputs,
        "postopen_transition_action": "ABSTAIN_NO_VALIDATED_P2_STATE",
        "combined_probability": None,
        "combined_probability_authority": False,
        "three_way_state_authority": False,
        "position_authority": False,
        "instrument_mapping_authority": False,
        "order_execution_authority": False,
        "production_authority": False,
    }
