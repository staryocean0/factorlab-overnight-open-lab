#!/usr/bin/env python3
"""Frozen open-development diagnostic for separately preregistered B2/B3 single-driver coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEARS = tuple(range(2015, 2021))
TARGET = "opening_gap_rvol"
BASELINE = ["r1","r20","abs_r1","prev_gap","overnight_trend_5","prev_daytime","prev_last_hour","prev_afternoon","log_rvol20","weekend","holiday_reopen"]
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
DRIVER_ROOT = ROOT / "data/driver_runtime_text_2015_2020"
DRIVER_RECEIPT = ROOT / "docs/research/driver_runtime_text_carrier_parity_receipt_v1.json"
AUTHORITY = ROOT / "docs/governance/current_authority_v1.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
CONFIG = {
    "overnight_china_offshore_driver_v1": {
        "candidate": "china_offshore_z", "raw": "a50_channel_return", "sign": 1.0,
        "product_family": "OFP-B2_china_specific_offshore_driver",
        "output": "docs/research/cloud_china_offshore_driver_v1_dev_diagnostic.json",
        "state": "docs/governance/china_offshore_driver_v1_state.json", "expected_ledger_count": 8,
    },
    "overnight_fx_cny_driver_v1": {
        "candidate": "fx_cny_z", "raw": "hkma_usdcny_closure_return", "sign": -1.0,
        "product_family": "OFP-B3_fx_macro_overnight_driver",
        "output": "docs/research/cloud_fx_cny_driver_v1_dev_diagnostic.json",
        "state": "docs/governance/fx_cny_driver_v1_state.json", "expected_ledger_count": 9,
    },
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20), b''): h.update(block)
    return h.hexdigest()

def read_json(path: Path) -> dict: return json.loads(path.read_text(encoding='utf-8'))

def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x=pd.to_numeric(s, errors='coerce'); return np.sqrt(x.pow(2).shift(1).rolling(window=60,min_periods=20).mean())

def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    d=np.column_stack([np.ones(len(x)),x]); coef,*_=np.linalg.lstsq(d,y,rcond=None); return y-d@coef

def r2(y: np.ndarray,p: np.ndarray)->float:
    sst=float(np.sum((y-np.mean(y))**2)); return float('nan') if sst<=0 else 1-float(np.sum((y-p)**2))/sst

def diag(frame: pd.DataFrame,candidate:str,min_n:int)->dict:
    cols=[*BASELINE,candidate,TARGET]; x=frame[cols].apply(pd.to_numeric,errors='coerce').dropna()
    if len(x)<min_n:return {'n':int(len(x)),'status':'insufficient'}
    y=x[TARGET].to_numpy(float); xb=x[BASELINE].to_numpy(float); c=x[candidate].to_numpy(float)
    db=np.column_stack([np.ones(len(x)),xb]); dc=np.column_stack([np.ones(len(x)),xb,c])
    bb,*_=np.linalg.lstsq(db,y,rcond=None); bc,*_=np.linalg.lstsq(dc,y,rcond=None); rb,rc=r2(y,db@bb),r2(y,dc@bc)
    cr=residualize(c,xb); yr=residualize(y,xb); pc=None if np.std(cr)==0 or np.std(yr)==0 else float(np.corrcoef(cr,yr)[0,1])
    z=x.copy()
    for col in cols:
        sd=float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd==0:return {'n':int(len(x)),'status':'degenerate'}
        z[col]=(z[col]-float(z[col].mean()))/sd
    zd=np.column_stack([np.ones(len(z)),z[[*BASELINE,candidate]].to_numpy(float)]); zcoef,*_=np.linalg.lstsq(zd,z[TARGET].to_numpy(float),rcond=None)
    return {'n':int(len(x)),'status':'ok','partial_corr':pc,'baseline_r2':rb,'candidate_r2':rc,'delta_r2':rc-rb,'standardized_candidate_coefficient':float(zcoef[-1])}

def load_frame()->tuple[pd.DataFrame,dict]:
    fm=read_json(FACTOR_ROOT/'manifest.json'); dm=read_json(DRIVER_ROOT/'manifest.json'); dr=read_json(DRIVER_RECEIPT)
    if fm.get('published_year_window') != [2015,2020]:raise RuntimeError('factor carrier boundary drift')
    if dm.get('published_window') != '2015-01-05..2020-12-31':raise RuntimeError('driver carrier boundary drift')
    if dm.get('withheld_years') != [2021,2022,2023,2024,2025]:raise RuntimeError('driver withheld years drift')
    if dr.get('a50_clock_integrity')!='PASS' or dr.get('hkma_causal_timing_integrity')!='PASS':raise RuntimeError('driver carrier integrity not PASS')
    if dr.get('2021_2025_text_shards_generated') is not False:raise RuntimeError('post-2020 driver text exposure')
    pieces=[]; hashes={}
    for year in YEARS:
        fp=FACTOR_ROOT/f'factor_panel_{year}.csv'; dp=DRIVER_ROOT/f'driver_external_{year}.csv'; f=pd.read_csv(fp); d=pd.read_csv(dp)
        f['trading_day']=pd.to_datetime(f['trading_day'],errors='raise').dt.normalize(); d['trading_day']=pd.to_datetime(d['trading_day'],errors='raise').dt.normalize()
        x=f.merge(d[['trading_day','a50_channel_return','hkma_usdcny_closure_return']],on='trading_day',how='inner',validate='one_to_one'); x['year']=year; pieces.append(x)
        hashes[str(year)]={'factor_panel_sha256':sha256(fp),'driver_external_sha256':sha256(dp)}
    out=pd.concat(pieces,ignore_index=True).sort_values('trading_day',kind='mergesort').reset_index(drop=True)
    if out['trading_day'].duplicated().any():raise RuntimeError('duplicate driver day')
    if out['trading_day'].min()!=pd.Timestamp('2015-01-05') or out['trading_day'].max()!=pd.Timestamp('2020-12-31'):raise RuntimeError('driver DEV boundary drift')
    return out, {'factor_manifest_sha256':sha256(FACTOR_ROOT/'manifest.json'),'driver_manifest_sha256':sha256(DRIVER_ROOT/'manifest.json'),'driver_receipt_sha256':sha256(DRIVER_RECEIPT),'year_shards':hashes}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',type=Path,required=True); args=ap.parse_args(); args.protocol=args.protocol.resolve()
    protocol=read_json(args.protocol); identity=protocol.get('research_identity')
    if identity not in CONFIG:raise RuntimeError('unsupported single-driver identity')
    cfg=CONFIG[identity]; candidate=cfg['candidate']; output=ROOT/cfg['output']; state=read_json(ROOT/cfg['state']); authority=read_json(AUTHORITY); ledger=read_json(LEDGER)
    if output.exists():raise RuntimeError(f'refusing overwrite {output}')
    if state.get('research_identity')!=identity or state.get('outcome_opened') is not False:raise RuntimeError('single-driver state drift')
    if (authority.get('active_research') or {}).get('identity')!=identity:raise RuntimeError('identity not active')
    if protocol.get('candidate_increment') != [candidate] or protocol.get('target')!=TARGET or protocol.get('baseline_controls')!=BASELINE or protocol.get('expected_direction')!='positive':raise RuntimeError('single-driver frozen design drift')
    if ledger.get('query_count')!=int(cfg['expected_ledger_count']):raise RuntimeError('unexpected ledger count before single-driver DEV')
    raw,source=load_frame(); raw['rvol20']=pd.to_numeric(raw['rvol20'],errors='coerce'); raw=raw.loc[np.isfinite(raw['rvol20'])&raw['rvol20'].gt(0)].copy()
    raw[cfg['raw']]=pd.to_numeric(raw[cfg['raw']],errors='coerce'); raw[f"{cfg['raw']}_rms60_prev"]=trailing_rms_prev(raw[cfg['raw']]); raw[candidate]=float(cfg['sign'])*raw[cfg['raw']]/raw[f"{cfg['raw']}_rms60_prev"]
    raw['log_rvol20']=np.log(raw['rvol20']); raw[TARGET]=pd.to_numeric(raw['gap'],errors='coerce')/raw['rvol20']
    annual_min=int(protocol['sufficiency_gates']['each_calendar_year_complete_cases_min']); pooled_min=int(protocol['sufficiency_gates']['pooled_complete_cases_min'])
    diagnostics={'pooled':diag(raw,candidate,pooled_min),'by_year':{str(y):diag(raw.loc[raw['year'].eq(y)],candidate,annual_min) for y in YEARS}}
    pooled=diagnostics['pooled']; annual=diagnostics['by_year']; sufficient=pooled.get('status')=='ok' and all(annual[str(y)].get('status')=='ok' for y in YEARS)
    if sufficient:
        coefs=[float(annual[str(y)]['standardized_candidate_coefficient']) for y in YEARS]; dr2=[float(annual[str(y)]['delta_r2']) for y in YEARS]
        gates={'all_sufficiency_pass':True,'pooled_partial_corr_positive':float(pooled['partial_corr'])>0,'pooled_standardized_coefficient_positive':float(pooled['standardized_candidate_coefficient'])>0,'positive_annual_coefficient_count':int(sum(v>0 for v in coefs)),'minimum_positive_annual_coefficient_count_pass':sum(v>0 for v in coefs)>=int(protocol['progression_gates']['positive_calendar_year_coefficient_count_min']),'median_annual_coefficient':float(np.median(coefs)),'median_annual_coefficient_positive':float(np.median(coefs))>0,'pooled_delta_r2_positive':float(pooled['delta_r2'])>0,'positive_annual_delta_r2_count':int(sum(v>0 for v in dr2)),'minimum_positive_annual_delta_r2_count_pass':sum(v>0 for v in dr2)>=int(protocol['progression_gates']['positive_calendar_year_delta_r2_count_min'])}
        progression=all(gates[k] for k in ['pooled_partial_corr_positive','pooled_standardized_coefficient_positive','minimum_positive_annual_coefficient_count_pass','median_annual_coefficient_positive','pooled_delta_r2_positive','minimum_positive_annual_delta_r2_count_pass'])
    else:gates={'all_sufficiency_pass':False}; progression=False
    prefix='B2' if identity.startswith('overnight_china') else 'B3'; decision=f'{prefix}_DEV_INSUFFICIENT' if not sufficient else (f'{prefix}_DEV_PROGRESS_CONTINUOUS_COORDINATE' if progression else f'{prefix}_DEV_NO_PROGRESS')
    receipt={'schema_id':'overnight_single_external_driver_dev_diagnostic@1.0','session_date':'2026-09-12','research_identity':identity,'product_family':cfg['product_family'],'development_window':'2015-01-05..2020-12-31','candidate':candidate,'target':TARGET,'baseline_controls':BASELINE,'diagnostics':diagnostics,'progression_gate_components':gates,'decision':decision,'source_integrity':source,'protocol':{'path':str(args.protocol.relative_to(ROOT)),'sha256':sha256(args.protocol)},'candidate_attempt_count':1,'threshold_search':False,'bucket_search':False,'normalization_search':False,'channel_add_drop_search':False,'alternate_target_search':False,'strategy_PnL_optimization':False,'2021_2025_rows_opened':False,'reusable_blackbox_query_created':False,'production_authority':False}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print('SINGLE_EXTERNAL_DRIVER_DEV_DIAGNOSTIC_COMPLETE'); print(decision); return 0

if __name__=='__main__':raise SystemExit(main())
