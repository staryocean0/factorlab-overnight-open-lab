#!/usr/bin/env python3
"""Post-result, nonselectable minute-to-panel measurement audit. No model fit."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'docs/governance/global_spillover_v9_target_integrity_audit_plan.json'
OUT = ROOT / 'artifacts/research/v9_target_integrity'


def main():
    plan = json.loads(PLAN.read_text())
    bp = ROOT / 'data/development/1m_official.parquet'
    pp = ROOT / 'data/development/csi1000_open_pit_panel.parquet'
    bars = pd.read_parquet(bp)
    panel = pd.read_parquet(pp).sort_values('trading_day').set_index('trading_day')
    if panel.index.duplicated().any() or bars[['trading_day', 'bar_end_shanghai']].duplicated().any():
        raise AssertionError('duplicate dates/minute endpoints')
    for days in [bars['trading_day'], pd.Series(panel.index)]:
        if pd.to_datetime(days).max() > pd.Timestamp('2020-12-31'):
            raise AssertionError('post-2020 input')
    time = pd.to_datetime(bars['bar_end_shanghai']).dt.strftime('%H:%M:%S')
    opens = bars.loc[time.eq('09:31:00')].set_index('trading_day')['open']
    closes = bars.loc[time.eq('15:00:00')].set_index('trading_day')['close']
    if opens.index.duplicated().any() or closes.index.duplicated().any():
        raise AssertionError('ambiguous daily endpoint')
    daily = pd.DataFrame(index=sorted(bars['trading_day'].unique()))
    daily.index.name = 'trading_day'
    daily['raw_open_0931'] = opens
    daily['raw_close_1500'] = closes
    daily['raw_prev_close'] = daily['raw_close_1500'].shift(1)
    daily['raw_gap'] = daily['raw_open_0931'] / daily['raw_prev_close'] - 1
    compared = panel[['open_0931', 'close_1500', 'prev_close', 'gap']].join(daily)
    checks = {}
    for col in ['open_0931', 'close_1500', 'prev_close', 'gap']:
        mask = compared['raw_' + col].notna()
        err = (compared[col] - compared['raw_' + col]).abs()
        tol = plan['tolerance']['gap_atol' if col == 'gap' else 'raw_price_atol']
        bad = mask & (compared[col].isna() | (err > tol))
        compared[col + '_abs_error'] = err
        checks[col] = {'compared_rows': int(mask.sum()), 'unresolved_rows': int((~mask).sum()),
                       'mismatch_rows': int(bad.sum()), 'max_abs_error': float(err[mask].max()),
                       'mismatch_dates': compared.index[bad].tolist()}
    missing = daily.index[daily[['raw_open_0931', 'raw_close_1500']].isna().any(axis=1)].tolist()
    passed = not missing and all(v['mismatch_rows'] == 0 for v in checks.values())
    OUT.mkdir(parents=True, exist_ok=True)
    compared.to_csv(OUT / 'daily_endpoint_parity.csv', float_format='%.17g')
    dates = ['2020-02-04', '2020-03-13', '2020-04-20']
    report = {
        'schema_id': 'overnight_open_v9_target_integrity_result@1.0',
        'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [bp, pp, Path(__file__)]},
        'raw_minute_rows': len(bars), 'raw_china_days': len(daily), 'panel_rows': len(panel),
        'symbol_values': sorted(bars['symbol'].unique().tolist()),
        'missing_0931_or_1500_days': missing,
        'checks': checks, 'internal_endpoint_parity_pass': passed,
        'trigger_event_parity': compared.loc[dates].reset_index().to_dict('records'),
        'interpretation': 'Internal endpoint identity only; no independent upstream vendor/exchange price validation.',
        'authority': plan['authority'], 'refits': 0, 'post_2020_rows_read': 0,
    }
    (OUT / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
