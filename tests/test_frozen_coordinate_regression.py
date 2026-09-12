"""Synthetic inputs only. These tests do not revalidate scientific performance."""
import numpy as np
import pandas as pd
import pytest

import diagnose_driver_agreement_disagreement_dev as drivers
import diagnose_trend_conditioned_open_state_dev as trend
import diagnose_volatility_conditioned_open_state_dev as volatility


def driver_frame(n=90):
    return pd.DataFrame({'rvol20':np.full(n,0.02),'gap':np.full(n,0.01),'us_nasdaq':np.full(n,0.01),'us_vix_chg':np.full(n,-0.02),'a50_channel_return':np.full(n,0.015),'hkma_usdcny_closure_return':np.full(n,-0.005)})


def context_frame(rvol=None):
    v = [0.01,0.02,0.03] if rvol is None else rvol
    days = pd.date_range('2019-01-02',periods=len(v),freq='B')
    panel = pd.DataFrame({'trading_day':days,'gap':np.full(len(v),0.005),'r20':np.full(len(v),0.04),'rvol20':v,'r1':np.full(len(v),0.001),'prev_daytime':np.zeros(len(v)),'holiday_reopen':np.zeros(len(v))})
    future = pd.DataFrame({'trading_day':days.strftime('%Y-%m-%d'),'ret_0935_0950':np.zeros(len(v)),'ret_0935_1005':np.zeros(len(v)),'ret_0935_1035':np.zeros(len(v))})
    return panel,future


def test_rms_warmup_and_current_exclusion():
    values = pd.Series(np.arange(1,82,dtype=float))
    actual = drivers.trailing_rms_prev(values)
    assert actual.iloc[:20].isna().all()
    assert actual.iloc[20] == pytest.approx(np.sqrt(np.mean(values.iloc[:20]**2)))
    assert actual.iloc[80] == pytest.approx(np.sqrt(np.mean(values.iloc[20:80]**2)))


@pytest.mark.parametrize('cut',[20,35,60,75])
def test_future_perturbations_do_not_change_past_normalizers(cut):
    values = pd.Series(np.linspace(-0.04,0.06,90))
    changed = values.copy()
    changed.iloc[cut:] = 100
    pd.testing.assert_series_equal(drivers.trailing_rms_prev(values).iloc[:cut+1],drivers.trailing_rms_prev(changed).iloc[:cut+1])


@pytest.mark.parametrize('sign',[-1,1])
def test_frozen_driver_polarity_and_coherence(sign):
    frame = driver_frame()
    for col in ['us_nasdaq','us_vix_chg','a50_channel_return','hkma_usdcny_closure_return']:
        frame[col] *= sign
    out = drivers.build_coordinates(frame)
    last = out.iloc[-1]
    for coordinate in ['global_risk_z','china_offshore_z','fx_cny_z','driver_coherence']:
        assert last[coordinate] == pytest.approx(sign)
    assert last['opening_gap_rvol'] == pytest.approx(0.5)


def test_driver_coherence_is_bounded_for_synthetic_mixed_signals():
    frame = driver_frame(150)
    rng = np.random.default_rng(991)
    for col in ['us_nasdaq','us_vix_chg','a50_channel_return','hkma_usdcny_closure_return']:
        frame[col] = rng.normal(0,0.01,len(frame))
    values = drivers.build_coordinates(frame)['driver_coherence'].dropna()
    assert len(values) > 100
    assert values.abs().le(1+1e-12).all()


def test_zero_driver_denominators_remain_missing_not_false_neutral():
    frame = driver_frame()
    for col in ['us_nasdaq','us_vix_chg','a50_channel_return','hkma_usdcny_closure_return']:
        frame[col] = 0
    out = drivers.build_coordinates(frame)
    assert out['driver_coherence'].isna().all()


@pytest.mark.parametrize('bad',[0,-0.02,np.nan,np.inf])
def test_invalid_volatility_is_excluded_by_frozen_context_implementations(bad):
    panel,future = context_frame([0.02,bad,0.03])
    assert len(trend.build_dev_frame(panel,future)) == 2
    assert len(volatility.build_frame(panel,future)) == 2


def test_c1_normalization_and_interaction_match_frozen_formula():
    panel,future = context_frame()
    out = trend.build_dev_frame(panel,future)
    expected_gap = panel['gap']/panel['rvol20']
    expected_trend = panel['r20']/(np.sqrt(20)*panel['rvol20'])
    np.testing.assert_allclose(out['observed_gap_rvol'],expected_gap)
    np.testing.assert_allclose(out['trend20_rvol'],expected_trend)
    np.testing.assert_allclose(out['trend_gap_interaction'],expected_gap*expected_trend)


def test_c2_keeps_c1_control_and_exact_log_volatility_interaction():
    panel,future = context_frame()
    out = volatility.build_frame(panel,future)
    expected_gap = panel['gap']/panel['rvol20']
    np.testing.assert_allclose(out['vol_gap_interaction'],expected_gap*np.log(panel['rvol20']))
    assert 'trend_gap_interaction' in volatility.BASELINE_CONTROLS
    np.testing.assert_allclose(out['trend_gap_interaction'],trend.build_dev_frame(panel,future)['trend_gap_interaction'])


@pytest.mark.parametrize('implementation',[trend.short_horizon_returns_from_clocks,volatility.short_horizon_returns])
def test_target_clocks_on_synthetic_prices(implementation):
    bars = pd.DataFrame({'trading_day':['2019-01-02']*4,'clock':['09:35','09:50','10:05','10:35'],'close':[100,101,102,103]})
    out = implementation(bars).iloc[0]
    assert out['ret_0935_0950'] == pytest.approx(0.01)
    assert out['ret_0935_1005'] == pytest.approx(0.02)
    assert out['ret_0935_1035'] == pytest.approx(0.03)


@pytest.mark.parametrize('implementation',[trend.short_horizon_returns_from_clocks,volatility.short_horizon_returns])
def test_missing_exact_target_clock_fails_instead_of_interpolating(implementation):
    bars = pd.DataFrame({'trading_day':['2019-01-02']*3,'clock':['09:35','09:50','10:05'],'close':[100,101,102]})
    with pytest.raises(RuntimeError,match='clock'):
        implementation(bars)


def test_c2_development_loader_contract_does_not_admit_2021():
    panel,future = context_frame()
    panel['trading_day'] = pd.date_range('2021-01-04',periods=len(panel),freq='B')
    with pytest.raises(RuntimeError,match='boundary'):
        volatility.build_frame(panel,future)
