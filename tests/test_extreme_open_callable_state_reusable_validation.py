import pandas as pd
import extreme_open_callable_state as p4
import extreme_open_univariate_stats as stats
import run_extreme_open_callable_state_reusable_validation as p5


def protocol():
    return {
        'exact_state_set': list(p4.P3_ORDER),
        'scientific_gates_per_state': {'primary_two_sided_Fisher_BH_q_max': 0.10},
    }


def fake_results(*, fail_index=None, insufficient_index=None):
    rows=[]
    for i,sid in enumerate(p4.P3_ORDER):
        gates={'frozen_gate': i != fail_index}
        rows.append({
            'state_id':sid,
            'target':p4.P3[sid]['target'],
            'sufficient':i != insufficient_index,
            'pre_bh':gates,
            'primary_p':0.001,
            'left_p':0.001,
            'right_p':0.001,
        })
    return rows


def run_with(monkeypatch, rows):
    by_id={r['state_id']:r for r in rows}
    monkeypatch.setattr(p5,'build_internal_state_result',lambda frame,_p4,_stats,sid,_protocol:dict(by_id[sid]))
    return p5.evaluate_package(pd.DataFrame(),p4,stats,protocol())


def test_event_gate_boundary_is_exactly_30bp():
    assert p5.classify_event(0.003)=='EXTREME_UP'
    assert p5.classify_event(-0.003)=='EXTREME_DOWN'
    assert p5.classify_event(0.002999)=='NONE'
    assert p5.classify_event(-0.002999)=='NONE'


def test_exact_P4_state_order_is_six_and_target_balanced():
    assert len(p4.P3_ORDER)==6
    assert sum(p4.P3[s]['target']=='EXTREME_UP' for s in p4.P3_ORDER)==3
    assert sum(p4.P3[s]['target']=='EXTREME_DOWN' for s in p4.P3_ORDER)==3


def test_overall_PASS_requires_all_six_sufficient_and_scientifically_passing(monkeypatch):
    assert run_with(monkeypatch,fake_results())=='PASS'


def test_any_sufficient_scientific_failure_forces_overall_FAIL(monkeypatch):
    assert run_with(monkeypatch,fake_results(fail_index=2))=='FAIL'


def test_insufficient_state_without_scientific_failure_is_overall_INSUFFICIENT(monkeypatch):
    assert run_with(monkeypatch,fake_results(insufficient_index=4))=='INSUFFICIENT'


def test_FAIL_takes_precedence_over_other_state_insufficiency(monkeypatch):
    rows=fake_results(fail_index=1,insufficient_index=4)
    assert run_with(monkeypatch,rows)=='FAIL'
