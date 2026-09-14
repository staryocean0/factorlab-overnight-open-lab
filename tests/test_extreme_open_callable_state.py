import math
from extreme_open_callable_state import EDGES, P3_ORDER, bucket_for, evaluate_extreme_open_state


def base(**kw):
    x={
        'B1_global_risk':0.0,
        'B2_china_offshore':0.0,
        'B4_driver_coherence':0.0,
        'causal_prior_volatility_parent':-4.2,
    }
    x.update(kw); return x


def fired(result):
    return [x['state_id'] for x in result['fired_states']]


def test_exact_bucket_boundary_semantics():
    for name,e in EDGES.items():
        assert bucket_for(name,e['q1'])=='LOW'
        assert bucket_for(name,e['q2'])=='MID'
        assert bucket_for(name,math.nextafter(e['q2'], math.inf))=='HIGH'
    assert bucket_for('B1_global_risk',None) is None


def test_no_pair_means_abstain():
    r=evaluate_extreme_open_state(base())
    assert r['primary_action']=='ABSTAIN_NO_P3_STATE'
    assert r['target_consensus'] is None
    assert fired(r)==[]
    assert r['postopen_transition_action']=='ABSTAIN_NO_VALIDATED_P2_STATE'


def test_single_up_pair_is_returned_without_combination():
    r=evaluate_extreme_open_state(base(B1_global_risk=1.0,B2_china_offshore=1.0))
    assert r['primary_action']=='STATE_SET' and r['target_consensus']=='EXTREME_UP'
    assert fired(r)==['UP_B1_HIGH_X_B2_HIGH']
    assert r['combined_probability'] is None and r['combined_probability_authority'] is False


def test_all_three_up_pairs_are_returned_in_frozen_order():
    r=evaluate_extreme_open_state(base(B1_global_risk=1.0,B2_china_offshore=1.0,causal_prior_volatility_parent=-3.0))
    assert r['primary_action']=='STATE_SET' and r['target_consensus']=='EXTREME_UP'
    assert fired(r)==list(P3_ORDER[:3])
    assert r['three_way_state_authority'] is False


def test_all_three_down_pairs_are_returned_in_frozen_order():
    r=evaluate_extreme_open_state(base(B1_global_risk=-1.0,B2_china_offshore=-1.0,B4_driver_coherence=-1.0))
    assert r['primary_action']=='STATE_SET' and r['target_consensus']=='EXTREME_DOWN'
    assert fired(r)==list(P3_ORDER[3:])


def test_mixed_target_pairs_force_conflict_abstention_but_preserve_evidence_set():
    r=evaluate_extreme_open_state(base(B1_global_risk=1.0,B2_china_offshore=-1.0,B4_driver_coherence=-1.0,causal_prior_volatility_parent=-3.0))
    assert 'UP_B1_HIGH_X_VOL_HIGH' in fired(r)
    assert 'DOWN_B2_LOW_X_B4_LOW' in fired(r)
    assert r['primary_action']=='ABSTAIN_TARGET_CONFLICT'
    assert r['target_consensus'] is None


def test_missing_coordinate_is_not_imputed_and_other_complete_pair_can_fire():
    r=evaluate_extreme_open_state(base(B1_global_risk=None,B2_china_offshore=1.0,causal_prior_volatility_parent=-3.0))
    assert 'B1_global_risk' in r['missing_inputs']
    assert fired(r)==['UP_B2_HIGH_X_VOL_HIGH']


def test_interface_never_grants_trading_or_production_authority():
    r=evaluate_extreme_open_state(base(B1_global_risk=1.0,B2_china_offshore=1.0))
    assert r['position_authority'] is False
    assert r['instrument_mapping_authority'] is False
    assert r['order_execution_authority'] is False
    assert r['production_authority'] is False
