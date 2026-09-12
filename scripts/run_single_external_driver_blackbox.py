#!/usr/bin/env python3
"""Compact reusable BLACKBOX controller for separately frozen B2/B3 driver coordinates."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")
TARGET = "opening_gap_rvol"
BASELINE = ["r1","r20","abs_r1","prev_gap","overnight_trend_5","prev_daytime","prev_last_hour","prev_afternoon","log_rvol20","weekend","holiday_reopen"]
CONFIG = {
    "overnight_china_offshore_open_gap_v1": {"candidate":"china_offshore_z","raw":"a50_channel_return","sign":1.0,"parent":"overnight_china_offshore_driver_v1"},
    "overnight_fx_cny_open_gap_v1": {"candidate":"fx_cny_z","raw":"hkma_usdcny_closure_return","sign":-1.0,"parent":"overnight_fx_cny_driver_v1"},
}


def sha256(path: Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def load_b4_module():
    p=ROOT/'scripts/run_driver_coherence_open_gap_blackbox.py'
    spec=importlib.util.spec_from_file_location('b4_blackbox_authority',p)
    if spec is None or spec.loader is None:raise RuntimeError('cannot load frozen B4 source assembly')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def residualize(y:np.ndarray,x:np.ndarray)->np.ndarray:
    d=np.column_stack([np.ones(len(x)),x]); coef,*_=np.linalg.lstsq(d,y,rcond=None); return y-d@coef


def partial_corr(frame:pd.DataFrame,candidate:str)->float:
    xb=frame[BASELINE].to_numpy(float); cr=residualize(frame[candidate].to_numpy(float),xb); yr=residualize(frame[TARGET].to_numpy(float),xb)
    if np.std(cr)==0 or np.std(yr)==0:raise RuntimeError('degenerate partial correlation')
    v=float(np.corrcoef(cr,yr)[0,1])
    if not np.isfinite(v):raise RuntimeError('nonfinite partial correlation')
    return v


def standardized_coef(frame:pd.DataFrame,candidate:str)->float:
    cols=[*BASELINE,candidate,TARGET]; z=frame[cols].astype(float).copy()
    for col in cols:
        sd=float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd==0:raise RuntimeError('degenerate standardized regression')
        z[col]=(z[col]-float(z[col].mean()))/sd
    d=np.column_stack([np.ones(len(z)),z[[*BASELINE,candidate]].to_numpy(float)])
    coef,*_=np.linalg.lstsq(d,z[TARGET].to_numpy(float),rcond=None); return float(coef[-1])


def moving_block_support(frame:pd.DataFrame,candidate:str,block:int,resamples:int,seed:int)->float:
    n=len(frame)
    if n<block:raise RuntimeError('sample below bootstrap block')
    rng=np.random.default_rng(seed); starts=np.arange(0,n-block+1); pos=0
    for _ in range(resamples):
        idx=[]
        while len(idx)<n:
            s=int(rng.choice(starts)); idx.extend(range(s,s+block))
        coef=standardized_coef(frame.iloc[np.array(idx[:n])],candidate); pos+=int(coef>0)
    return pos/resamples


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--panel',type=Path,required=True)
    ap.add_argument('--hkma',type=Path,required=True)
    ap.add_argument('--holiday-a50',type=Path,required=True)
    ap.add_argument('--ordinary-a50',type=Path,required=True)
    ap.add_argument('--high-open-source-manifest',type=Path,required=True)
    ap.add_argument('--external-source-manifest',type=Path,required=True)
    ap.add_argument('--reconstruction-contract',type=Path,required=True)
    ap.add_argument('--protocol',type=Path,required=True)
    ap.add_argument('--receipt-out',type=Path,required=True)
    args=ap.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding='utf-8')); identity=protocol.get('research_identity')
    if identity not in CONFIG:raise RuntimeError('unsupported external driver BLACKBOX identity')
    cfg=CONFIG[identity]; candidate=cfg['candidate']
    if protocol.get('candidate')!=candidate or protocol.get('target')!=TARGET or protocol.get('baseline_controls')!=BASELINE:raise RuntimeError('external driver BLACKBOX design drift')
    norm=protocol.get('normalization',{})
    if norm!={"method":"lagged_trailing_RMS","window":60,"min_periods":20,"shift":1,"current_observation_excluded":True}:raise RuntimeError('normalization drift')
    external=json.loads(args.external_source_manifest.read_text(encoding='utf-8'))
    required_assertions=['same_contract_all_events','no_future_volume_or_oi_selection','no_mid_window_roll','no_forward_fill_or_interpolation','blackbox_not_used_for_fit_or_rule_selection']
    if not all(external.get('assertions',{}).get(k) is True for k in required_assertions):raise RuntimeError('external source assertions fail')
    b4=load_b4_module()
    panel=pd.read_parquet(args.panel).copy(); panel['trading_day']=pd.to_datetime(panel['trading_day'],errors='raise').dt.normalize(); panel=panel.sort_values('trading_day',kind='mergesort').reset_index(drop=True)
    needed={"trading_day","gap","r1","r20","abs_r1","prev_gap","overnight_trend_5","prev_daytime","prev_last_hour","prev_afternoon","rvol20","weekend","holiday_reopen","us_nasdaq","us_vix_chg"}
    if needed.difference(panel.columns):raise RuntimeError('reconstructed panel missing inputs')
    panel['previous_china_day']=panel['trading_day'].shift(1)
    df=b4.add_hkma(panel,args.hkma); df,ordinary_coverage,clock_ok=b4.attach_a50(df,args.holiday_a50,args.ordinary_a50)
    if not clock_ok:raise RuntimeError('A50 causal clock integrity failed')
    df['rvol20']=pd.to_numeric(df['rvol20'],errors='coerce')
    df[cfg['raw']]=pd.to_numeric(df[cfg['raw']],errors='coerce')
    rms=b4.trailing_rms_prev(df[cfg['raw']]); df[candidate]=float(cfg['sign'])*df[cfg['raw']]/rms
    df['log_rvol20']=np.where(df['rvol20'].gt(0),np.log(df['rvol20']),np.nan); df[TARGET]=pd.to_numeric(df['gap'],errors='coerce')/df['rvol20']
    cols=[*BASELINE,candidate,TARGET]; numeric=df[cols].apply(pd.to_numeric,errors='coerce'); complete=numeric.notna().all(axis=1)&np.isfinite(numeric.to_numpy(float)).all(axis=1)&df['rvol20'].gt(0)
    bb=df.loc[df['trading_day'].between(BB_START,BB_END)&complete].copy().sort_values('trading_day',kind='mergesort').reset_index(drop=True); bb['year']=bb['trading_day'].dt.year.astype(int)
    suff=protocol['internal_sufficiency_gates']; years=range(2021,2026)
    sufficient=len(bb)>=int(suff['pooled_complete_cases_min']) and all(int(bb['year'].eq(y).sum())>=int(suff['each_calendar_year_complete_cases_min']) for y in years)
    if 'ordinary_A50_coverage_minimum' in suff:sufficient=sufficient and ordinary_coverage>=float(suff['ordinary_A50_coverage_minimum'])
    if not sufficient:decision='INSUFFICIENT'
    else:
        pc=partial_corr(bb,candidate); coef=standardized_coef(bb,candidate); annual=[standardized_coef(bb.loc[bb['year'].eq(y)],candidate) for y in years]
        g=protocol['internal_scientific_gates']; boot=g['moving_block_bootstrap']; support=moving_block_support(bb,candidate,int(boot['block_length_trading_days']),int(boot['resamples']),int(boot['seed']))
        passed=[pc>0,coef>0,sum(v>0 for v in annual)>=int(g['positive_calendar_year_coefficient_count_min']),float(np.median(annual))>0,support>=float(boot['positive_coefficient_support_min'])]
        decision='PASS' if all(passed) else 'FAIL'
    psha=sha256(args.protocol); hsha=sha256(args.high_open_source_manifest); esha=sha256(args.external_source_manifest); rsha=sha256(args.reconstruction_contract)
    qid=hashlib.sha256('|'.join([identity,psha,hsha,esha,rsha]).encode()).hexdigest()[:20]
    receipt={'schema_id':'overnight_single_external_driver_blackbox_receipt@1.0','query_id':qid,'research_identity':identity,'parent_development_identity':cfg['parent'],'comparator':f'same_domestic_baseline_without_{candidate}','decision':decision,'public_detail_release':False,'internal_metrics_persisted':False,'yearly_results_persisted':False,'counts_persisted':False,'bootstrap_results_persisted':False,'failure_attribution_persisted':False,'protocol_sha256':psha,'high_open_source_manifest_sha256':hsha,'external_source_manifest_sha256':esha,'reconstruction_contract_sha256':rsha,'blackbox_reusable_after_query':True,'blackbox_consumed':False,'reuse_is_independent_oos':False,'production_authority':False}
    args.receipt_out.parent.mkdir(parents=True,exist_ok=True); args.receipt_out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(decision); return 0

if __name__=='__main__':raise SystemExit(main())
