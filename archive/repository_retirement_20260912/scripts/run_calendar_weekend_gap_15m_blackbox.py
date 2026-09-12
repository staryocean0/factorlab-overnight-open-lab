#!/usr/bin/env python3
"""Compact reusable BLACKBOX controller for frozen C4 weekend-gap 15m interaction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
IDENTITY="overnight_weekend_gap_conditioned_open_state_15m_blackbox_v1"
BB_START=pd.Timestamp("2021-01-01"); BB_END=pd.Timestamp("2025-12-31")
BASELINE=["observed_gap_rvol","weekend","holiday_reopen","trend20_rvol","trend_gap_interaction","log_rvol20","r1","prev_daytime"]
CANDIDATE="weekend_gap_interaction"; TARGET="ret_0935_0950"
SYMBOL="000852.SH"

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def residualize(y,x):
    d=np.column_stack([np.ones(len(x)),x]); c,*_=np.linalg.lstsq(d,y,rcond=None); return y-d@c

def partial_corr(frame:pd.DataFrame)->float:
    xb=frame[BASELINE].to_numpy(float); cr=residualize(frame[CANDIDATE].to_numpy(float),xb); yr=residualize(frame[TARGET].to_numpy(float),xb)
    if np.std(cr)==0 or np.std(yr)==0:raise RuntimeError('degenerate C4 partial correlation')
    v=float(np.corrcoef(cr,yr)[0,1]);
    if not np.isfinite(v):raise RuntimeError('nonfinite C4 partial correlation')
    return v

def stdcoef(frame:pd.DataFrame)->float:
    cols=[*BASELINE,CANDIDATE,TARGET]; z=frame[cols].astype(float).copy()
    for col in cols:
        sd=float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd==0:raise RuntimeError('degenerate C4 regression')
        z[col]=(z[col]-float(z[col].mean()))/sd
    d=np.column_stack([np.ones(len(z)),z[[*BASELINE,CANDIDATE]].to_numpy(float)]); c,*_=np.linalg.lstsq(d,z[TARGET].to_numpy(float),rcond=None); return float(c[-1])

def boot_support(frame:pd.DataFrame,block:int,resamples:int,seed:int)->float:
    n=len(frame)
    if n<block:raise RuntimeError('C4 sample below bootstrap block')
    rng=np.random.default_rng(seed); starts=np.arange(0,n-block+1); pos=0
    for _ in range(resamples):
        idx=[]
        while len(idx)<n:
            s=int(rng.choice(starts)); idx.extend(range(s,s+block))
        pos+=int(stdcoef(frame.iloc[np.array(idx[:n])])>0)
    return pos/resamples

def extract_clocks(path:Path,days:pd.Series)->pd.DataFrame:
    min_day=str(pd.to_datetime(days).min().date()); max_day=str(pd.to_datetime(days).max().date())
    b=pd.read_parquet(path,columns=['symbol','trading_day','timestamp','close'],filters=[('symbol','==',SYMBOL),('trading_day','>=',min_day),('trading_day','<=',max_day)]).copy()
    b=b.loc[b['symbol'].astype(str).eq(SYMBOL)].copy(); b['trading_day']=pd.to_datetime(b['trading_day'],errors='raise').dt.normalize(); ts=b['timestamp'].astype(str); b['clock']=ts.str.slice(11,16)
    e=b.loc[b['clock'].isin(['09:35','09:50']),['trading_day','clock','close']].copy()
    if e.duplicated(['trading_day','clock']).any():raise RuntimeError('duplicate C4 exact clock')
    w=e.pivot(index='trading_day',columns='clock',values='close').reset_index().rename(columns={'09:35':'close_0935','09:50':'close_0950'})
    spine=pd.DataFrame({'trading_day':pd.to_datetime(days).dt.normalize().drop_duplicates().sort_values().to_numpy()})
    return spine.merge(w,on='trading_day',how='left',validate='one_to_one')

def verify_clock_parity(clocks:pd.DataFrame,reference_root:Path)->None:
    refs=[]
    for y in (2019,2020):
        r=pd.read_csv(reference_root/f'opening_clocks_{y}.csv',usecols=['trading_day','close_0935','close_0950']); r['trading_day']=pd.to_datetime(r['trading_day'],errors='raise').dt.normalize(); refs.append(r)
    ref=pd.concat(refs,ignore_index=True); got=clocks.loc[clocks['trading_day'].dt.year.isin([2019,2020]),['trading_day','close_0935','close_0950']]
    m=ref.merge(got,on='trading_day',how='outer',suffixes=('_ref','_got'),indicator=True)
    if not m['_merge'].eq('both').all():raise RuntimeError('C4 clock parity row mismatch')
    for col in ['close_0935','close_0950']:
        a=pd.to_numeric(m[f'{col}_ref'],errors='coerce'); b=pd.to_numeric(m[f'{col}_got'],errors='coerce')
        if not (a.isna().to_numpy()==b.isna().to_numpy()).all():raise RuntimeError('C4 clock parity NaN mismatch')
        mask=a.notna(); diff=np.abs(a[mask].to_numpy(float)-b[mask].to_numpy(float))
        if len(diff) and float(diff.max())>1e-9:raise RuntimeError('C4 clock parity numeric mismatch')

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--panel',type=Path,required=True); ap.add_argument('--minute-bars',type=Path,required=True); ap.add_argument('--source-manifest',type=Path,required=True); ap.add_argument('--reconstruction-contract',type=Path,required=True); ap.add_argument('--runtime-text-root',type=Path,required=True); ap.add_argument('--protocol',type=Path,required=True); ap.add_argument('--receipt-out',type=Path,required=True); args=ap.parse_args()
    p=json.loads(args.protocol.read_text(encoding='utf-8'))
    if p.get('research_identity')!=IDENTITY or p.get('candidate')!=CANDIDATE or p.get('target')!=TARGET or p.get('baseline_controls')!=BASELINE or p.get('frozen_expected_sign')!='positive':raise RuntimeError('C4 BLACKBOX design drift')
    panel=pd.read_parquet(args.panel).copy(); panel['trading_day']=pd.to_datetime(panel['trading_day'],errors='raise').dt.normalize(); panel=panel.sort_values('trading_day',kind='mergesort').reset_index(drop=True)
    needed={'trading_day','gap','r20','rvol20','weekend','holiday_reopen','r1','prev_daytime'}
    if needed.difference(panel.columns):raise RuntimeError('C4 reconstructed panel missing inputs')
    clocks=extract_clocks(args.minute_bars,panel['trading_day']); verify_clock_parity(clocks,args.runtime_text_root)
    x=panel.merge(clocks,on='trading_day',how='left',validate='one_to_one'); rv=pd.to_numeric(x['rvol20'],errors='coerce'); gap=pd.to_numeric(x['gap'],errors='coerce'); r20=pd.to_numeric(x['r20'],errors='coerce')
    x['observed_gap_rvol']=gap/rv; x['trend20_rvol']=r20/(np.sqrt(20.0)*rv); x['trend_gap_interaction']=x['observed_gap_rvol']*x['trend20_rvol']; x['log_rvol20']=np.where(rv.gt(0),np.log(rv),np.nan); x['weekend']=pd.to_numeric(x['weekend'],errors='coerce'); x['holiday_reopen']=pd.to_numeric(x['holiday_reopen'],errors='coerce'); x[CANDIDATE]=x['weekend']*x['observed_gap_rvol']; x[TARGET]=pd.to_numeric(x['close_0950'],errors='coerce')/pd.to_numeric(x['close_0935'],errors='coerce')-1.0
    cols=[*BASELINE,CANDIDATE,TARGET]; num=x[cols].apply(pd.to_numeric,errors='coerce'); complete=np.isfinite(num.to_numpy(float)).all(axis=1)&rv.gt(0); bb=x.loc[x['trading_day'].between(BB_START,BB_END)&complete].copy().sort_values('trading_day',kind='mergesort').reset_index(drop=True); bb['year']=bb['trading_day'].dt.year.astype(int)
    suff=p['internal_sufficiency_gates']; years=range(2021,2026); sufficient=len(bb)>=int(suff['pooled_complete_cases_min']) and all(int(bb['year'].eq(y).sum())>=int(suff['each_calendar_year_complete_cases_min']) and int((bb['year'].eq(y)&bb['weekend'].eq(1)).sum())>=int(suff['each_calendar_year_weekend_complete_cases_min']) for y in years)
    if not sufficient:decision='INSUFFICIENT'
    else:
        pc=partial_corr(bb); coef=stdcoef(bb); annual=[stdcoef(bb.loc[bb['year'].eq(y)]) for y in years]; g=p['internal_scientific_gates']; boot=g['moving_block_bootstrap']; support=boot_support(bb,int(boot['block_length_trading_days']),int(boot['resamples']),int(boot['seed']))
        passed=[pc>0,coef>0,sum(v>0 for v in annual)>=int(g['positive_calendar_year_coefficient_count_min']),float(np.median(annual))>0,support>=float(boot['positive_coefficient_support_min'])]; decision='PASS' if all(passed) else 'FAIL'
    psha=sha256(args.protocol); ssha=sha256(args.source_manifest); rsha=sha256(args.reconstruction_contract); qid=hashlib.sha256('|'.join([IDENTITY,psha,ssha,rsha]).encode()).hexdigest()[:20]
    receipt={'schema_id':'overnight_calendar_weekend_gap_15m_blackbox_receipt@1.0','query_id':qid,'research_identity':IDENTITY,'parent_development_identity':'overnight_weekend_gap_conditioned_open_state_15m_v1','comparator':'same_frozen_15m_baseline_without_weekend_gap_interaction','decision':decision,'reconstructed_panel_2015_2020_parity':'PASS','target_clock_2019_2020_parity':'PASS','public_detail_release':False,'internal_metrics_persisted':False,'yearly_results_persisted':False,'counts_persisted':False,'bootstrap_results_persisted':False,'failure_attribution_persisted':False,'protocol_sha256':psha,'source_manifest_sha256':ssha,'reconstruction_contract_sha256':rsha,'blackbox_reusable_after_query':True,'blackbox_consumed':False,'reuse_is_independent_oos':False,'production_authority':False}
    args.receipt_out.parent.mkdir(parents=True,exist_ok=True); args.receipt_out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(decision); return 0
if __name__=='__main__':raise SystemExit(main())
