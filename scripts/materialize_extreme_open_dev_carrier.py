#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from extreme_open_vnext_core import P1,P2,HORIZONS,UNAVAILABLE,FORMULAS,finite,tercile_edges,bucket,build_coordinates,transition_label

def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def source(root,rel):
 p=root/rel; blob=subprocess.check_output(['git','rev-parse',f'HEAD:{rel}'],cwd=root,text=True).strip(); return {'path':rel,'git_blob':blob,'sha256':sha256(p),'bytes':p.stat().st_size}
def event_counts(d):
 c=d.event_class.value_counts(); return {'n':int(len(d)),'extreme_up_count':int(c.get('EXTREME_UP',0)),'extreme_down_count':int(c.get('EXTREME_DOWN',0)),'none_count':int(c.get('NONE',0))}
def transition_counts(d,ev,col):
 v=pd.to_numeric(d[col],errors='coerce'); c=pd.Series([transition_label(ev,x) for x in v]).value_counts(); ok=v[np.isfinite(v)]
 return {'n':int(len(d)),'continuation_count':int(c.get('CONTINUATION',0)),'reversal_count':int(c.get('REVERSAL',0)),'neutral_count':int(c.get('NEUTRAL',0)),'missing_count':int(c.get('MISSING',0)),'valid_return_n':int(len(ok)),'sum_forward_return':float(ok.sum()) if len(ok) else 0.0,'sum_forward_return_sq':float(np.square(ok.to_numpy(float)).sum()) if len(ok) else 0.0}
def scopes(d): return [('pooled_2018_2020',d)]+[(str(y),d[d.year.eq(y)]) for y in (2018,2019,2020)]

def load_inputs(root):
 fs=[]; rows={}; sources=[]
 for y in range(2015,2021):
  rels=[f'data/runtime_text_2015_2025/factor_panel_{y}.csv',f'data/driver_runtime_text_2015_2020/driver_external_{y}.csv',f'data/runtime_text_2015_2025/opening_clocks_{y}.csv']; f,d,c=[pd.read_csv(root/r) for r in rels]
  for z in (f,d,c):
   z['trading_day']=pd.to_datetime(z.trading_day).dt.normalize()
   if z.trading_day.duplicated().any() or not z.trading_day.dt.year.eq(y).all(): raise RuntimeError(f'bad source dates {y}')
  j=f.merge(d[['trading_day','a50_channel_return','hkma_usdcny_closure_return']],on='trading_day',how='left',validate='one_to_one').merge(c[['trading_day','close_0935','close_0950','close_1035']],on='trading_day',how='left',validate='one_to_one'); j['year']=y; fs.append(j)
  rows[str(y)]={'factor_rows':len(f),'driver_rows':len(d),'clock_rows':len(c),'joined_rows':len(j)}; sources += [source(root,r) for r in rels]
 x=pd.concat(fs,ignore_index=True).sort_values('trading_day').reset_index(drop=True)
 if x.trading_day.duplicated().any() or x.trading_day.min()!=pd.Timestamp('2015-01-05') or x.trading_day.max()!=pd.Timestamp('2020-12-31'): raise RuntimeError('joined boundary/duplicate failure')
 return x,rows,sources

def materialize(root):
 auth=json.loads((root/'docs/governance/current_authority_v1.json').read_text()); plan=auth['planned_research']
 if plan['program_id']!='overnight_extreme_open_conditional_transition_program_v1' or plan['primary_event_threshold_bp']!=30 or plan['reusable_blackbox_2021_2025_open_authorized'] is not False: raise RuntimeError('authority drift')
 x,rows,sources=load_inputs(root); x=build_coordinates(x); fit=x[x.trading_day.between('2015-01-05','2017-12-31')]; ev=x[x.trading_day.between('2018-01-01','2020-12-31')].copy(); edges={}
 for c in sorted((set(P1)|set(P2))-set(UNAVAILABLE)):
  q1,q2,n=tercile_edges(fit[c]); edges[c]={'q_1_3':q1,'q_2_3':q2,'fit_n':n,'method':'linear empirical terciles','assignment':'LOW x<=q1; MID q1<x<=q2; HIGH x>q2'}; ev['bucket__'+c]=[bucket(v,q1,q2) for v in ev[c]]
 p1=[]
 for c in P1:
  if c in UNAVAILABLE: continue
  for scope,d in scopes(ev):
   eligible=d[finite(d[c]) & d.event_class.ne('MISSING')]; p1.append({'coordinate':c,'scope':scope,'cohort':'PARENT',**event_counts(eligible)})
   for b in ('LOW','MID','HIGH'): p1.append({'coordinate':c,'scope':scope,'cohort':b,**event_counts(eligible[eligible['bucket__'+c].eq(b)])})
 p2=[]
 for c in P2:
  for sign in ('EXTREME_UP','EXTREME_DOWN'):
   for hz in HORIZONS:
    for scope,d in scopes(ev):
     eligible=d[finite(d[c]) & d.event_class.eq(sign)]; p2.append({'coordinate':c,'event':sign,'horizon':hz,'scope':scope,'cohort':'PARENT',**transition_counts(eligible,sign,'ret_'+hz)})
     for b in ('LOW','MID','HIGH'): p2.append({'coordinate':c,'event':sign,'horizon':hz,'scope':scope,'cohort':b,**transition_counts(eligible[eligible['bucket__'+c].eq(b)],sign,'ret_'+hz)})
 miss={c:{'fit_missing':int((~finite(fit[c])).sum()),'eval_missing':int((~finite(ev[c])).sum())} for c in (set(P1)|set(P2))-set(UNAVAILABLE)}
 out={'schema_id':'overnight_extreme_open_dev_sufficient_statistics_carrier@1.0','program_id':plan['program_id'],'session_date':'2026-09-14','scientific_role':'mechanical_sufficient_statistics_only_no_adjudication','event_gate':{'threshold':0.003,'EXTREME_UP':'gap>=+0.003','EXTREME_DOWN':'gap<=-0.003'},'fit_window':'2015-01-05..2017-12-31','evaluation_window':'2018-01-01..2020-12-31','fit_window_target_outcomes_inspected_for_edges':False,'quantile_edges':edges,'coordinate_formulas':FORMULAS,'coordinate_availability':{c:UNAVAILABLE.get(c,'AVAILABLE_EXACT_FROZEN_OR_CAUSAL_RECONSTRUCTION') for c in set(P1)|set(P2)},'input_sources':sources,'row_counts':rows,'joined_duplicate_trading_day_count':int(x.trading_day.duplicated().sum()),'missingness':{'coordinates':miss,'evaluation_clocks':{c:int((~finite(ev[c])).sum()) for c in ('close_0935','close_0950','close_1035')}},'p1_preopen_event_propensity':p1,'p2_postopen_transition':p2,'policy_assertions':{'reusable_blackbox_2021_2025_opened':False,'candidate_selected':False,'candidate_adjudicated':False,'threshold_search':False,'clock_search':False,'two_way_intersections_opened':False,'production_authority':False}}
 raw=json.dumps(out,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(); out['canonical_payload_sha256']=hashlib.sha256(raw).hexdigest(); return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out if a.out.is_absolute() else root/a.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(materialize(root),indent=2,sort_keys=True,ensure_ascii=False)+'\n'); digest=sha256(out); out.with_suffix(out.suffix+'.sha256').write_text(f'{digest}  {out.name}\n'); print(json.dumps({'status':'MATERIALIZED_NO_ADJUDICATION','carrier':str(out.relative_to(root)),'sha256':digest,'unavailable':UNAVAILABLE,'production_authority':False},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
