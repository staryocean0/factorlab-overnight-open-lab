#!/usr/bin/env python3
"""Verify sealed evidence from fixed outputs, with zero estimator fits."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'docs/governance/global_spillover_v9_a50_nonlinearity_receipt.json'
OUT = ROOT / 'artifacts/research/v9_a50_nonlinearity'


def main():
    receipt = json.loads(RECEIPT.read_text())
    for path, digest in receipt['evidence_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    result = json.loads((OUT / 'results.json').read_text())
    ci = json.loads((OUT / 'ci_logged_results.json').read_text())
    rows = pd.read_csv(OUT / 'fixed_holdout_predictions.csv', float_precision='round_trip')
    tr = pd.read_csv(OUT / 'training_marginal_slopes.csv', float_precision='round_trip')
    assert len(rows) == 461 and len(tr) == 900
    assert not rows.trading_day.duplicated().any() and not tr.trading_day.duplicated().any()
    assert rows.trading_day.between('2019-01-01', '2020-12-31').all()
    assert tr.trading_day.between('2015-01-01', '2018-12-31').all()
    y = rows.y.to_numpy()
    for name, pred_col in [('V6A_frozen_common_sample_comparator', 'pred_v6'), ('V9A_plus_A50_signed_square', 'pred_v9')]:
        pred = rows[pred_col].to_numpy()
        sse = float(np.sum((y-pred)**2))
        metrics = {'holdout_sse': sse, 'holdout_r2': 1-sse/float(np.sum((y-y.mean())**2)),
                   'holdout_ic': float(np.corrcoef(y, pred)[0,1]),
                   'holdout_sign_hit': float(np.mean((y>=0)==(pred>=0)))}
        for k,v in metrics.items():
            assert abs(v-result['candidates'][name][k]) <= 1e-12, (name,k)
            assert abs(v-ci['candidates'][name][k]) <= 1e-12, ('CI',name,k)
    q = 'a50_ordinary_signed_square'
    x = 'a50_ordinary_preauction_closure_return'
    for df in [rows, tr]:
        ordinary = df.holiday_reopen.eq(0)
        np.testing.assert_allclose(df.loc[ordinary,q], df.loc[ordinary,x]*df.loc[ordinary,x].abs(), atol=1e-16, rtol=1e-12)
        assert df.loc[~ordinary,q].eq(0).all()
    snapshot = json.loads((OUT / 'V9A_plus_A50_signed_square_snapshot.json').read_text())
    i,j = snapshot['features'].index(x), snapshot['features'].index(q)
    b,s = snapshot['standardized_coefficients'], snapshot['scaler_scale']
    np.testing.assert_allclose(tr.marginal_slope, b[i]/s[i]+2*tr[x].abs()*b[j]/s[j], atol=1e-12,rtol=1e-12)
    assert (tr.loc[tr.holiday_reopen.eq(0),'marginal_slope'] > 0).all()
    gain = (rows.y-rows.pred_v6)**2-(rows.y-rows.pred_v9)**2
    np.testing.assert_allclose(gain, rows.sse_improvement, atol=1e-14)
    assert sum(v['sse_improvement'] >= 0 for v in result['quarterly'].values()) == 4
    assert result['adjudication'] == ci['adjudication']
    assert result['adjudication']['hard_valid_increment_retained']
    assert not result['adjudication']['all_preregistered_gates_pass']
    assert result['adjudication']['selected_candidate'] is None
    assert not any(result['authority'].values())
    assert not any(snapshot['authority'].values())
    audit = json.loads((ROOT / 'artifacts/research/v9_target_integrity/results.json').read_text())
    assert audit['internal_endpoint_parity_pass'] and audit['checks']['gap']['compared_rows'] == 1461
    print('V9 closeout verified: fixed-output metrics, CI parity, causal formula, hashes, failed promotion and authority; zero fits.')


if __name__ == '__main__':
    main()
