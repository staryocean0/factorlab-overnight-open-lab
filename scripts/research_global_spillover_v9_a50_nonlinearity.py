#!/usr/bin/env python3
"""Execute the already-frozen v9 hypothesis; never search or refit diagnostics."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import research_global_spillover_v3_complete_clock as v3
import research_global_spillover_v6_daily_a50 as v6

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / 'docs/governance/global_spillover_v9_a50_nonlinearity_preregistration.json'
PARENT = '02bbb216057f7024b5a82a87c80805383bb02c83'
FREEZE = '9554809cec804545e0713be1be788b42d7803bd5'
OUT = ROOT / 'artifacts/research/v9_a50_nonlinearity'
X = 'a50_ordinary_preauction_closure_return'
Q = 'a50_ordinary_signed_square'
C0 = 'V6A_frozen_common_sample_comparator'
C1 = 'V9A_plus_A50_signed_square'
AUTHORITY = dict(fresh_oos=False, baseline_replacement=False, production=False,
                 registry_mutation=False, runtime_routing=False, merge_main=False)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def verify_frozen_sources() -> dict:
    """Bind all model inputs and imported implementations to actual parent bytes."""
    paths = [
        'scripts/research_global_spillover_v3_complete_clock.py',
        'scripts/research_global_spillover_v4_cnh.py',
        'scripts/research_global_spillover_v6_daily_a50.py',
        'docs/governance/baseline_receipt.json',
        'docs/governance/external_sgx_a50_ordinary_preauction_2015_2020_manifest.json',
        'data/manifest.json',
    ]
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'data/development').glob('*.parquet'))]
    digests = {}
    for path in paths:
        frozen = subprocess.check_output(['git', 'show', f'{PARENT}:{path}'], cwd=ROOT)
        current = (ROOT / path).read_bytes()
        if current != frozen:
            raise AssertionError(f'v6 frozen source drift: {path}')
        digests[path] = sha(ROOT / path)
    for name in ['preanalysis', 'preregistration']:
        path = f'docs/governance/global_spillover_v9_a50_nonlinearity_{name}.json'
        frozen = subprocess.check_output(['git', 'show', f'{FREEZE}:{path}'], cwd=ROOT)
        if (ROOT / path).read_bytes() != frozen:
            raise AssertionError(f'v9 preregistration drift: {path}')
        digests[path] = sha(ROOT / path)
    return digests


def add_signed_square(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    x = pd.to_numeric(result[X], errors='raise')
    holiday = pd.to_numeric(result['holiday_reopen'], errors='raise').ne(0)
    result[Q] = (x * x.abs()).where(~holiday, 0.0)
    # No imputation on an unavailable ordinary session.
    return result


def fit_once(frame: pd.DataFrame, features: list[str]) -> tuple[dict, pd.DataFrame, pd.DataFrame, Pipeline]:
    if frame['trading_day'].max() > pd.Timestamp('2020-12-31'):
        raise AssertionError('post-2020 row detected')
    tr = frame.loc[frame['trading_day'] <= pd.Timestamp('2018-12-31')].copy()
    te = frame.loc[frame['trading_day'].between('2019-01-01', '2020-12-31')].copy()
    def usable(part: pd.DataFrame) -> pd.DataFrame:
        values = part[features + ['gap']].apply(pd.to_numeric, errors='coerce')
        keep = values.notna().all(axis=1)
        if not np.isfinite(values.loc[keep].to_numpy(dtype=float)).all():
            raise AssertionError('non-finite model input')
        return part.loc[keep].copy().reset_index(drop=True)
    tr, te = usable(tr), usable(te)
    pipe = Pipeline([('sc', StandardScaler()), ('m', Ridge(alpha=1.0))])
    pipe.fit(tr[features].astype(float), tr['gap'].astype(float))
    pred = pipe.predict(te[features].astype(float))
    rows = te[['trading_day', 'holiday_reopen', 'us_interval_count']].copy()
    rows['y'], rows['pred'] = te['gap'].to_numpy(dtype=float), pred
    rows['sse'] = (rows['y'] - pred) ** 2
    metrics = {
        'n_train': len(tr), 'n_holdout': len(te),
        'holdout_r2': float(r2_score(rows['y'], pred)),
        'holdout_ic': v3._corr(rows['y'].to_numpy(), pred),
        'holdout_sse': float(rows['sse'].sum()),
        'holdout_sign_hit': float(np.mean((pred >= 0) == (rows['y'] >= 0))),
        'standardized_coefficients': dict(zip(features, map(float, pipe['m'].coef_), strict=True)),
    }
    return metrics, rows, tr, pipe


def check_replay(metrics: dict, frozen: dict) -> None:
    for key in ['n_train', 'n_holdout', 'holdout_r2', 'holdout_ic', 'holdout_sign_hit', 'holdout_sse']:
        tolerance = 0 if key.startswith('n_') else frozen['tolerance_metrics']
        if abs(metrics[key] - frozen['V6_' + key]) > tolerance:
            raise AssertionError(f'v6 replay mismatch: {key}')


def marginal_slope(pipe: Pipeline, features: list[str], x: np.ndarray) -> np.ndarray:
    i, j = features.index(X), features.index(Q)
    return pipe['m'].coef_[i] / pipe['sc'].scale_[i] + 2 * np.abs(x) * pipe['m'].coef_[j] / pipe['sc'].scale_[j]


def snapshot(pipe: Pipeline, features: list[str]) -> dict:
    return {
        'features': features, 'scaler_mean': pipe['sc'].mean_.tolist(),
        'scaler_scale': pipe['sc'].scale_.tolist(),
        'standardized_coefficients': pipe['m'].coef_.tolist(),
        'intercept': float(pipe['m'].intercept_), 'ridge_alpha': 1.0,
        'fit_window': '2015-2018', 'authority': AUTHORITY,
    }


def concentration(rows: pd.DataFrame) -> dict:
    gain = rows['sse_improvement'].to_numpy()
    positive = np.sort(gain[gain > 0])[::-1]
    total_positive = float(positive.sum())
    return {
        'n': len(rows), 'better_rows': int((gain > 0).sum()),
        'worse_rows': int((gain < 0).sum()), 'equal_rows': int((gain == 0).sum()),
        'total_sse_improvement': float(gain.sum()),
        'positive_sse_improvement': total_positive,
        'negative_sse_improvement': float(gain[gain < 0].sum()),
        'remove_best_rows_without_refit': {
            str(k): {
                'rows_removed': min(k, len(positive)),
                'remaining_sse_improvement': float(gain.sum() - positive[:k].sum()),
                'share_of_positive_gain_removed': float(positive[:k].sum() / total_positive) if total_positive else None,
            } for k in [1, 5, 10]
        },
    }


def forensics(rows: pd.DataFrame, train: pd.DataFrame, pipe: Pipeline, features: list[str], m0: dict, m1: dict) -> dict:
    ordinary = rows.loc[rows['holiday_reopen'].eq(0)].reset_index(drop=True)
    q, x, y = [ordinary[c].to_numpy() for c in [Q, X, 'y']]
    slope = marginal_slope(pipe, features, train.loc[train['holiday_reopen'].eq(0), X].to_numpy())
    redistribution = {
        f: {'comparator': b, 'candidate': m1['standardized_coefficients'][f],
            'change': m1['standardized_coefficients'][f] - b}
        for f, b in m0['standardized_coefficients'].items()
    }
    return {
        'selection_authority': False, 'refit': False,
        'ordinary_correlations': {
            'n': len(ordinary), 'q_with_target': v3._corr(q, y),
            'q_with_v6_fixed_residual': v3._corr(q, y - ordinary['pred_v6'].to_numpy()),
            'q_with_linear_A50': v3._corr(q, x),
            'next_row_q_with_current_target': v3._corr(q[1:], y[:-1]),
            'previous_row_q_with_current_target': v3._corr(q[:-1], y[1:]),
            'placebo_pair_count': len(ordinary) - 1,
            'row_definition': 'chronological fixed ordinary holdout sample, not necessarily adjacent calendar sessions',
        },
        'concentration': {'full': concentration(rows), 'ordinary': concentration(ordinary)},
        'shock_direction': {
            'positive': concentration(ordinary.loc[ordinary[X] > 0]),
            'negative': concentration(ordinary.loc[ordinary[X] < 0]),
            'zero': concentration(ordinary.loc[ordinary[X] == 0]),
        },
        'coefficient_redistribution': redistribution,
        'training_ordinary_marginal_slope': {
            'n': len(slope), 'min': float(slope.min()), 'median': float(np.median(slope)),
            'max': float(slope.max()), 'nonpositive_count': int((slope <= 0).sum()),
            'strictly_positive_everywhere_observed': bool((slope > 0).all()),
            'observed_abs_x_min': float(train.loc[train['holiday_reopen'].eq(0), X].abs().min()),
            'observed_abs_x_max': float(train.loc[train['holiday_reopen'].eq(0), X].abs().max()),
        },
    }


def main() -> None:
    sources = verify_frozen_sources()
    prereg = json.loads(PREREG.read_text())
    declaration_path = ROOT / 'docs/governance/global_spillover_v9_execution_declaration.json'
    declaration = json.loads(declaration_path.read_text())
    if declaration['new_selectable_candidates'] != 1 or [a['id'] for a in prereg['attempts']] != [C0, C1]:
        raise AssertionError('attempt family drift')
    guards = json.loads(v6.ORDINARY_MANIFEST_PATH.read_text())['guards']
    if guards['post_2020_rows'] or guards['target_ticks_at_or_after_091500'] or guards['settlement_S_used_as_trade']:
        raise AssertionError('frozen A50 timing/source guard failed')
    frame, coverage = v6.build_frame()
    frame = add_signed_square(frame)
    base = json.loads(v6.BASELINE_PATH.read_text())['features']
    features = base + ['us_nasdaq_closure_extra', 'us_vix_closure_extra', 'hkma_usdcny_closure_return', 'a50_holiday_closure_return', X]
    # The candidate cannot execute until the exact parent replay passes.
    m0, p0, tr0, pipe0 = fit_once(frame, features)
    check_replay(m0, prereg['required_replay'])
    m1, p1, tr1, pipe1 = fit_once(frame, features + [Q])
    if not tr0['trading_day'].equals(tr1['trading_day']) or not p0['trading_day'].equals(p1['trading_day']):
        raise AssertionError('v9 differs from the fixed v6 common sample')
    h = p0['holiday_reopen'].ne(0)
    subsets = {'ordinary': v6.compare_predictions(p0, p1, ~h), 'holiday': v6.compare_predictions(p0, p1, h)}
    annual = {str(y): v6.compare_predictions(p0, p1, p0['trading_day'].dt.year.eq(y)) for y in [2019, 2020]}
    labels = p0['trading_day'].dt.to_period('Q').astype(str)
    quarterly = {q: v6.compare_predictions(p0, p1, labels.eq(q)) for q in sorted(labels.unique())}
    if len(quarterly) != 8:
        raise AssertionError('not exactly eight holdout quarters')
    rows = p0.rename(columns={'pred': 'pred_v6', 'sse': 'sse_v6'})
    rows['pred_v9'], rows['sse_v9'] = p1['pred'], p1['sse']
    rows['sse_improvement'] = rows['sse_v6'] - rows['sse_v9']
    rows = rows.merge(frame[['trading_day', X, Q]], on='trading_day', validate='one_to_one')
    diagnostic = forensics(rows, tr1, pipe1, features + [Q], m0, m1)
    coherence = diagnostic['training_ordinary_marginal_slope']['strictly_positive_everywhere_observed']
    qgain = np.array([v['sse_improvement'] for v in quarterly.values()])
    # The v9 contract states "not worse" without a new statistical tolerance.
    # Apply its literal inequalities; do not import v6's -1e-12 relaxation.
    gates = {
        'holdout_r2': m1['holdout_r2'] > m0['holdout_r2'],
        'holdout_sse': m1['holdout_sse'] < m0['holdout_sse'],
        'holdout_ic': m1['holdout_ic'] > m0['holdout_ic'],
        'sign_hit': m1['holdout_sign_hit'] >= m0['holdout_sign_hit'] - 0.01,
        'ordinary_subset_sse': subsets['ordinary']['sse_improvement'] > 0,
        'ordinary_subset_ic': subsets['ordinary']['delta_ic'] >= 0,
        'annual_sse': all(v['sse_improvement'] >= 0 for v in annual.values()),
        'quarterly_total_sse_improvement': qgain.sum() > 0,
        'quarterly_median_sse_improvement': np.median(qgain) > 0,
        'quarterly_nonnegative_count': (qgain >= 0).sum() >= 5,
        'holiday_subset_sse': subsets['holiday']['sse_improvement'] >= 0,
        'economic_coherence_gate': coherence,
    }
    gates = {k: bool(v) for k, v in gates.items()}
    if set(gates) != set(prereg['progression_gates']) - {'all_required'}:
        raise AssertionError('missing or extra preregistered gate')
    # Nonselectable reference fits were declared before model execution.
    used = pd.concat([tr0, frame.loc[frame['trading_day'].isin(p0['trading_day'])]], ignore_index=True)
    benchmarks = {}
    for name, f in [('C0_original_features_common_sample', base), ('NASDAQ_only_common_sample', ['us_nasdaq'])]:
        bm, bp, bt, _ = fit_once(used, f)
        if not bp['trading_day'].equals(p0['trading_day']) or not bt['trading_day'].equals(tr0['trading_day']):
            raise AssertionError('benchmark sample drift')
        benchmarks[name] = bm
        rows[name + '_pred'] = bp['pred'].to_numpy()
    benchmarks['always_low_open'] = {'n_holdout': len(rows), 'sign_hit': float((rows['y'] < 0).mean())}
    benchmark_delta = {name: {
        'v9_delta_ic': m1['holdout_ic'] - bm['holdout_ic'],
        'v9_delta_sign_hit': m1['holdout_sign_hit'] - bm['holdout_sign_hit'],
        'v9_sse_improvement': bm['holdout_sse'] - m1['holdout_sse'],
    } for name, bm in benchmarks.items() if 'holdout_ic' in bm}
    for cid, model, fs in [(C0, pipe0, features), (C1, pipe1, features + [Q])]:
        dump(OUT / (cid + '_snapshot.json'), snapshot(model, fs))
    train_slope = tr1[['trading_day', 'holiday_reopen', X, Q]].copy()
    train_slope['marginal_slope'] = marginal_slope(pipe1, features + [Q], tr1[X].to_numpy())
    OUT.mkdir(parents=True, exist_ok=True)
    train_slope.to_csv(OUT / 'training_marginal_slopes.csv', index=False, float_format='%.17g', date_format='%Y-%m-%d')
    rows.to_csv(OUT / 'fixed_holdout_predictions.csv', index=False, float_format='%.17g', date_format='%Y-%m-%d')
    dump(OUT / 'forensics.json', diagnostic)
    report = {
        'schema_id': 'overnight_open_global_spillover_v9_results@1.0',
        'parent_commit': PARENT, 'preregistration_commit': FREEZE,
        'execution_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_sha256': sources,
        'implementation_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), declaration_path]},
        'runtime': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'sklearn': sklearn.__version__},
        'data_boundary': declaration['interval_roles'], 'post_2020_rows_read': 0,
        'common_sample': coverage,
        'sample_identity': {label: hashlib.sha256(part['trading_day'].dt.strftime('%Y-%m-%d').str.cat(sep='\n').encode()).hexdigest() for label, part in [('train', tr0), ('holdout', p0)]},
        'parent_replay_pass': True, 'candidates': {C0: m0, C1: m1},
        'subsets': subsets, 'annual': annual, 'quarterly': quarterly,
        'quarterly_summary': {'nonnegative_count': int((qgain >= 0).sum()), 'median_sse_improvement': float(np.median(qgain)), 'total_sse_improvement': float(qgain.sum())},
        'economic_coherence': diagnostic['training_ordinary_marginal_slope'],
        'diagnostic_benchmarks': benchmarks, 'v9_vs_diagnostic_benchmarks': benchmark_delta,
        'adjudication': {
            'gates': gates, 'all_preregistered_gates_pass': all(gates.values()),
            'selected_candidate': C1 if all(gates.values()) else None,
            'hard_valid_increment_retained': bool(coherence and m0['holdout_sse'] - m1['holdout_sse'] > prereg['required_replay']['tolerance_metrics']),
            'scientific_status': 'frozen_research_candidate_waiting_for_new_unseen_challenge' if all(gates.values()) else 'no_incremental_successor_beyond_V6',
            'economic_incoherence_rejection': not coherence,
            'new_selectable_candidates_executed': 1, 'additional_nonselectable_reference_fits': 2,
        },
        'authority': AUTHORITY,
        'artifacts': {str(p.relative_to(ROOT)): sha(p) for p in sorted(OUT.iterdir()) if p.name != 'results.json'},
    }
    dump(OUT / 'results.json', report)
    print(json.dumps({'candidates': report['candidates'], 'economic_coherence': report['economic_coherence'], 'adjudication': report['adjudication']}, indent=2))


if __name__ == '__main__':
    main()
