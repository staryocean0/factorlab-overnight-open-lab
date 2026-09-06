import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import research_global_spillover_v9_a50_nonlinearity as v9


def synthetic_frame():
    days = list(pd.date_range('2017-01-01', periods=40)) + list(pd.date_range('2019-01-01', periods=8))
    x = np.linspace(-0.025, 0.025, len(days))
    return v9.add_signed_square(pd.DataFrame({
        'trading_day': days, 'holiday_reopen': 0, 'us_interval_count': 1,
        v9.X: x, 'gap': 0.6 * x + 3 * x * abs(x),
    }))


def test_holiday_is_zero_but_unavailable_ordinary_is_not_imputed():
    f = pd.DataFrame({v9.X: [-0.02, 0.02, np.nan, np.nan, 0.03], 'holiday_reopen': [0, 0, 0, 1, 1]})
    q = v9.add_signed_square(f)[v9.Q]
    np.testing.assert_allclose(q.iloc[:2], [-0.0004, 0.0004])
    assert np.isnan(q.iloc[2])
    assert (q.iloc[3:] == 0).all()


def test_raw_marginal_derivative_matches_finite_difference():
    features = [v9.X, v9.Q]
    pipe = {'m': SimpleNamespace(coef_=np.array([0.007, -0.0005])),
            'sc': SimpleNamespace(scale_=np.array([0.01, 0.0001]))}
    x = np.array([-0.025, -0.01, 0, 0.01, 0.025])
    def contribution(z):
        return 0.007 * z / 0.01 - 0.0005 * z * abs(z) / 0.0001
    eps = 1e-8
    numerical = (contribution(x + eps) - contribution(x - eps)) / (2 * eps)
    np.testing.assert_allclose(v9.marginal_slope(pipe, features, x), numerical, atol=1e-6, rtol=1e-6)


def test_holdout_extremes_cannot_change_scaler_coefficients_or_training_gate():
    f = synthetic_frame()
    features = [v9.X, v9.Q]
    _, p, train, pipe = v9.fit_once(f, features)
    changed = f.copy()
    hold = changed['trading_day'].dt.year.eq(2019)
    changed.loc[hold, [v9.X, v9.Q, 'gap']] = [100, 10000, -100]
    _, _, train2, pipe2 = v9.fit_once(changed, features)
    np.testing.assert_array_equal(pipe['sc'].mean_, pipe2['sc'].mean_)
    np.testing.assert_array_equal(pipe['m'].coef_, pipe2['m'].coef_)
    np.testing.assert_array_equal(v9.marginal_slope(pipe, features, train[v9.X].to_numpy()),
                                  v9.marginal_slope(pipe2, features, train2[v9.X].to_numpy()))
    # The portable snapshot reproduces the materialized predictions without fit.
    s = v9.snapshot(pipe, features)
    values = f.loc[hold, features].to_numpy()
    restored = ((values - np.array(s['scaler_mean'])) / np.array(s['scaler_scale'])) @ np.array(s['standardized_coefficients']) + s['intercept']
    np.testing.assert_allclose(restored, p['pred'], atol=1e-14)


def test_post2020_input_rejected_before_fit():
    f = synthetic_frame()
    f.loc[f.index[-1], 'trading_day'] = pd.Timestamp('2021-01-01')
    with pytest.raises(AssertionError, match='post-2020'):
        v9.fit_once(f, [v9.X, v9.Q])


def test_parent_replay_failure_stops_before_candidate_execution(monkeypatch):
    monkeypatch.setattr(v9, 'verify_frozen_sources', lambda: {})
    monkeypatch.setattr(v9.v6, 'build_frame', lambda: (synthetic_frame(), {}))
    calls = []
    def broken_fit(frame, features):
        calls.append(features)
        return {'n_train': 899}, None, None, None
    monkeypatch.setattr(v9, 'fit_once', broken_fit)
    with pytest.raises(AssertionError, match='v6 replay mismatch'):
        v9.main()
    assert len(calls) == 1
    assert v9.Q not in calls[0]


def test_tail_diagnostics_use_fixed_losses_without_refit():
    rows = pd.DataFrame({'sse_improvement': [4., 3., -5., 1.]})
    c = v9.concentration(rows)
    assert c['total_sse_improvement'] == 3
    assert c['remove_best_rows_without_refit']['1']['remaining_sse_improvement'] == -1
    assert c['remove_best_rows_without_refit']['5']['remaining_sse_improvement'] == -5
