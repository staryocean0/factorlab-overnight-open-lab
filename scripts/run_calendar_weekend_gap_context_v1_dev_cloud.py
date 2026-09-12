#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
IDENTITY="overnight_weekend_gap_conditioned_open_state_15m_v1"
YEARS=tuple(range(2015,2021))
BASELINE=["observed_gap_rvol","weekend","holiday_reopen","trend20_rvol","trend_gap_interaction","log_rvol20","r1","prev_daytime"]
CANDIDATE="weekend_gap_interaction"
TARGET="ret_0935_0950"
PROTOCOL=ROOT/"docs/governance/calendar_weekend_gap_context_v1_protocol.json"
STATE=ROOT/"docs/governance/calendar_weekend_gap_context_v1_state.json"
AUTHORITY=ROOT/"docs/governance/current_authority_v1.json"
LEDGER=ROOT/"docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
DATA=ROOT/"data/runtime_text_2015_2025"
OUTPUT=ROOT/"docs/research/cloud_calendar_weekend_gap_context_v1_dev_diagnostic.json"

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def rj(p:Path)->dict:return json.loads(p.read_text(encoding='utf-8'))

def residualize(y,x):
    d=np.column_stack([np.ones(len(x)),x]); c,*_=np.linalg.lstsq(d,y,rcond=None); return y-d@c

def r2(y,p):
    sst=float(np.sum((y-np.mean(y))**2)); return float('nan') if sst<=0 else 1-float(np.sum((y-p)**2))/sst

def diag(frame:pd.DataFrame,min_n:int,min_weekend:int)->dict:
    cols=[*BASELINE,CANDIDATE,TARGET]
    x=frame[["weekend",*cols]].copy()
    num=x[cols].apply(pd.to_numeric,errors='coerce'); mask=np.isfinite(num.to_numpy(float)).all(axis=1)
    x=x.loc[mask].copy(); n=len(x); weekend_n=int(pd.to_numeric(x['weekend'],errors='coerce').eq(1).sum())
    if n<min_n or weekend_n<min_weekend:return {'n':int(n),'weekend_n':weekend_n,'status':'insufficient'}
    xx=x[cols].apply(pd.to_numeric,errors='raise'); y=xx[TARGET].to_numpy(float); xb=xx[BASELINE].to_numpy(float); c=xx[CANDIDATE].to_numpy(float)
    db=np.column_stack([np.ones(n),xb]); dc=np.column_stack([np.ones(n),xb,c]); cb,*_=np.linalg.lstsq(db,y,rcond=None); cc,*_=np.linalg.lstsq(dc,y,rcond=None)
    rb,rc=r2(y,db@cb),r2(y,dc@cc); cr=residualize(c,xb); yr=residualize(y,xb)
    pc=float(np.corrcoef(cr,yr)[0,1]) if np.std(cr)>0 and np.std(yr)>0 else float('nan')
    z=xx.copy()
    for col in cols:
        sd=float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd==0:return {'n':int(n),'weekend_n':weekend_n,'status':'degenerate'}
        z[col]=(z[col]-float(z[col].mean()))/sd
    zd=np.column_stack([np.ones(n),z[[*BASELINE,CANDIDATE]].to_numpy(float)]); zc,*_=np.linalg.lstsq(zd,z[TARGET].to_numpy(float),rcond=None)
    return {'n':int(n),'weekend_n':weekend_n,'status':'ok','partial_corr':pc,'baseline_r2':rb,'candidate_r2':rc,'delta_r2':rc-rb,'standardized_candidate_coefficient':float(zc[-1])}

def load_frame()->tuple[pd.DataFrame,dict]:
    m=rj(DATA/'manifest.json'); outs=m['outputs']; pieces=[]; hashes={}
    if m.get('published_year_window') != [2015,2020]:raise RuntimeError('runtime publication drift')
    for year in YEARS:
        fp=DATA/f'factor_panel_{year}.csv'; cp=DATA/f'opening_clocks_{year}.csv'
        if sha256(fp)!=outs['factor_panel'][str(year)]['sha256'] or sha256(cp)!=outs['opening_clocks'][str(year)]['sha256']:raise RuntimeError(f'C4 shard digest drift {year}')
        f=pd.read_csv(fp); c=pd.read_csv(cp); f['trading_day']=pd.to_datetime(f['trading_day'],errors='raise').dt.normalize(); c['trading_day']=pd.to_datetime(c['trading_day'],errors='raise').dt.normalize()
        x=f.merge(c[['trading_day','close_0935','close_0950']],on='trading_day',how='inner',validate='one_to_one'); x['year']=year; pieces.append(x)
        hashes[str(year)]={'factor_sha256':sha256(fp),'clocks_sha256':sha256(cp)}
    x=pd.concat(pieces,ignore_index=True).sort_values('trading_day',kind='mergesort').reset_index(drop=True)
    if x['trading_day'].duplicated().any():raise RuntimeError('duplicate C4 day')
    rvol=pd.to_numeric(x['rvol20'],errors='coerce'); valid=np.isfinite(rvol)&rvol.gt(0); x=x.loc[valid].copy(); rvol=rvol.loc[valid]
    gap=pd.to_numeric(x['gap'],errors='coerce'); r20=pd.to_numeric(x['r20'],errors='coerce')
    x['observed_gap_rvol']=gap/rvol; x['trend20_rvol']=r20/(np.sqrt(20.0)*rvol); x['trend_gap_interaction']=x['observed_gap_rvol']*x['trend20_rvol']; x['log_rvol20']=np.log(rvol)
    x['weekend']=pd.to_numeric(x['weekend'],errors='coerce'); x['holiday_reopen']=pd.to_numeric(x['holiday_reopen'],errors='coerce'); x[CANDIDATE]=x['weekend']*x['observed_gap_rvol']; x[TARGET]=pd.to_numeric(x['close_0950'],errors='coerce')/pd.to_numeric(x['close_0935'],errors='coerce')-1.0
    return x,{'runtime_manifest_sha256':sha256(DATA/'manifest.json'),'year_shards':hashes}

def sign(v:float)->int:return 1 if v>0 else (-1 if v<0 else 0)

def main()->int:
    if OUTPUT.exists():raise RuntimeError(f'refusing overwrite {OUTPUT}')
    p=rj(PROTOCOL); s=rj(STATE); a=rj(AUTHORITY); l=rj(LEDGER)
    if p.get('research_identity')!=IDENTITY or s.get('research_identity')!=IDENTITY or s.get('outcome_opened') is not False:raise RuntimeError('C4 identity/state drift')
    if (a.get('active_research') or {}).get('identity')!=IDENTITY:raise RuntimeError('C4 not active')
    if p.get('baseline_controls')!=BASELINE or p.get('candidate_increment')!=[CANDIDATE] or p.get('target')!=TARGET:raise RuntimeError('C4 frozen design drift')
    if l.get('query_count')!=10:raise RuntimeError('unexpected ledger count before C4 DEV')
    x,source=load_frame(); suff=p['sufficiency_gates']; mn=int(suff['each_calendar_year_complete_cases_min']); mw=int(suff['each_calendar_year_weekend_complete_cases_min'])
    annual={str(y):diag(x.loc[x['year'].eq(y)],mn,mw) for y in YEARS}; pooled=diag(x,mn*len(YEARS),mw*len(YEARS)); sufficient=pooled.get('status')=='ok' and all(annual[str(y)].get('status')=='ok' for y in YEARS)
    if sufficient:
        pc=float(pooled['partial_corr']); coef=float(pooled['standardized_candidate_coefficient']); pooled_sign=sign(coef); same_nonzero=pooled_sign!=0 and sign(pc)==pooled_sign
        coefs=[float(annual[str(y)]['standardized_candidate_coefficient']) for y in YEARS]; dr2=[float(annual[str(y)]['delta_r2']) for y in YEARS]; match=sum(sign(v)==pooled_sign for v in coefs); med=float(np.median(coefs)); posdr=sum(v>0 for v in dr2)
        gates={'all_sufficiency_pass':True,'pooled_partial_corr_and_coefficient_same_nonzero_sign':same_nonzero,'pooled_sign':pooled_sign,'annual_coefficient_matching_pooled_sign_count':int(match),'annual_coefficient_matching_pooled_sign_min_pass':match>=int(p['progression_gates']['annual_standardized_coefficient_matching_pooled_sign_min']),'median_annual_coefficient':med,'median_annual_coefficient_matches_pooled_sign':sign(med)==pooled_sign,'pooled_delta_r2_positive':float(pooled['delta_r2'])>0,'annual_positive_delta_r2_count':int(posdr),'annual_positive_delta_r2_min_pass':posdr>=int(p['progression_gates']['annual_positive_delta_r2_count_min'])}
        progression=all(gates[k] for k in ['pooled_partial_corr_and_coefficient_same_nonzero_sign','annual_coefficient_matching_pooled_sign_min_pass','median_annual_coefficient_matches_pooled_sign','pooled_delta_r2_positive','annual_positive_delta_r2_min_pass'])
    else:gates={'all_sufficiency_pass':False}; progression=False
    decision='C4_DEV_INSUFFICIENT' if not sufficient else ('C4_DEV_PROGRESS_WEEKEND_GAP_15M_CONTINUOUS_INTERACTION' if progression else 'C4_DEV_NO_PROGRESS')
    payload={'schema_id':'overnight_calendar_weekend_gap_context_dev_diagnostic@1.0','session_date':'2026-09-12','research_identity':IDENTITY,'product_family':p['product_family'],'development_window':p['development_window'],'candidate':CANDIDATE,'target':TARGET,'diagnostics':{'pooled':pooled,'by_year':annual},'progression_gate_components':gates,'decision':decision,'source_integrity':source,'protocol':{'path':str(PROTOCOL.relative_to(ROOT)),'sha256':sha256(PROTOCOL)},'candidate_attempt_count':1,'weekday_search':False,'holiday_replacement_search':False,'threshold_search':False,'bucket_search':False,'alternate_horizon_search':False,'additional_upstream_search':False,'2021_2025_rows_opened':False,'reusable_blackbox_query_created':False,'production_authority':False}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print('C4_WEEKEND_GAP_DEV_DIAGNOSTIC_COMPLETE'); print(decision); return 0
if __name__=='__main__':raise SystemExit(main())
