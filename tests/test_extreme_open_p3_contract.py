from adjudicate_extreme_open_p3_intersections import material_vs_stronger, compare
from materialize_extreme_open_p3_intersections import CANDIDATES


def test_candidate_family_is_exactly_six_and_target_separated():
    assert len(CANDIDATES) == 6
    assert sum(c[1] == 'EXTREME_UP' for c in CANDIDATES) == 3
    assert sum(c[1] == 'EXTREME_DOWN' for c in CANDIDATES) == 3
    assert len({c[0] for c in CANDIDATES}) == 6


def test_incremental_materiality_is_or_gate():
    # +5pp passes even when RR < 1.15.
    x = material_vs_stronger(0.55, 0.50, 0.49)
    assert x['pass'] is True
    # 1.15x passes even when absolute lift is <5pp.
    y = material_vs_stronger(0.23, 0.20, 0.19)
    assert y['incremental_lift_pp'] < 5.0
    assert y['incremental_risk_ratio'] >= 1.15
    assert y['pass'] is True
    z = material_vs_stronger(0.51, 0.50, 0.49)
    assert z['pass'] is False


def test_disjoint_incremental_comparison_detects_positive_separation():
    c = compare(40, 24, 80, 20)
    assert c['difference'] > 0
    assert c['ci95']['lower'] > 0
    assert c['fisher_p'] < 0.05
