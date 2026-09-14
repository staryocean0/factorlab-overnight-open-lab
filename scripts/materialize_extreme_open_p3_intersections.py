#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from extreme_open_vnext_core import build_coordinates, bucket

YEARS=range(2015,2021)
EVAL_YEARS=(2018,2019,2020)
CANDIDATES=(
 ('UP_B1_HIGH_X_B2_HIGH','EXTREME_UP','B1_global_risk','HIGH','B2_china_offshore','HIGH'),
 ('UP_B1_HIGH_X_VOL_HIGH','EXTREME_UP','B1_global_risk','HIGH','causal_prior_volatility_parent','HIGH'),
 ('UP_B2_HIGH_X_VOL_HIGH','EXTREME_UP','B2_china_offshore','HIGH','causal_prior_volatility_parent','HIGH'),
 ('DOWN_B1_LOW_X_B2_LOW','EXTREME_DOWN','B1_global_risk','LOW','B2_china_offshore','LOW'),
 ('DOWN_B1_LOW_X_B4_LOW','EXTREME_DOWN','B1_global_risk','LOW','B4_driver_coherence','LOW'),
 ('DOWN_B2_LOW_X_B4_LOW','EXTREME_DOWN','B2_china_offshore','LOW','B4_driver_coherence','LOW'),
)
TARGET_FIELD={'EXTREME_UP':'extreme_up_count','EXTREME_DOWN':'extreme_down_count'}

def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def source(root,rel):
 p=root/rel; blob=subprocess.check_output(['git','rev-parse',f'HEAD:{rel}'],cwd=root,text=True).strip(); return {'path':rel,'git_blob':blob,'sha256':sha256(p),'bytes':p.stat().st_size}
def event_counts(d):
 c=d.event_class.value_counts(); return {'n':int(len(d)),'extreme_up_count':int(c.get('EXTREME_UP',0)),'extreme_down_count':int(c.get('EXTREME_DOWN',0)),'none_count':int(c.get('NONE',0))}
def scopes(d): return [('pooled_2018_2020',d)]+[(str(y),d[d.year.eq(y)]) for y in EVAL_YEARS]

def load_inputs(root):
 frames=[]; sources=[]
 for y in YEARS:
  frel=f'data/runtime_text_2015_2025/factor_panel_{y}.csv'; drel=f'data/driver_runtime_text_2015_2020/driver_external_{y}.csv'
  f=pd.read_csv(root/frel); d=pd.read_csv(root/drel)
  for z in (f,d):
   z['trading_day']=pd.to_datetime(z.trading_day).dt.normalize()
   if z.trading_day.duplicated().any() or not z.trading_day.dt.year.eq(y).all(): raise RuntimeError(f'bad source dates {y}')
  j=f.merge(d[['trading_day','a50_channel_return','hkma_usdcny_closure_return']],on='trading_day',how='left',validate='one_to_one')
  for c in ('close_0935','close_0950','close_1035'): j[c]=np.nan
  j['year']=y; frames.append(j); sources += [source(root,frel),source(root,drel)]
 x=pd.concat(frames,ignore_index=True).sort_values('trading_day').reset_index(drop=True)
 if x.trading_day.duplicated().any() or x.trading_day.min()!=pd.Timestamp('2015-01-05') or x.trading_day.max()!=pd.Timestamp('2020-12-31'): raise RuntimeError('joined boundary failure')
 return build_coordinates(x),sources

def p0_index(carrier):
 out={}
 for r in carrier['p1_preopen_event_propensity']:
  out[(r['coordinate'],r['scope'],r['cohort'])]=r
 return out

def main_materialize(root):
 protocol=json.loads((root/'docs/governance/extreme_open_preopen_intersections_dev_v1_protocol.json').read_text())
 state=json.loads((root/'docs/governance/extreme_open_preopen_intersections_dev_v1_state.json').read_text())
 if state['status']!='AUTHORIZED_NOT_YET_MATERIALIZED_OR_EXECUTED' or state['candidate_count']!=6 or state['intersection_outcomes_opened'] is not False: raise RuntimeError('P3 state not cleanly authorized')
 if protocol['candidate_count']!=6 or protocol['reusable_blackbox_2021_2025_open_authorized'] is not False: raise RuntimeError('P3 protocol drift')
 p0_path=root/'data/extreme_open_vnext_dev_sufficient_statistics_v1.json'; p0=json.loads(p0_path.read_text()); edges=p0['quantile_edges']; p0i=p0_index(p0)
 x,sources=load_inputs(root); ev=x[x.trading_day.dt.year.isin(EVAL_YEARS)].copy()
 needed=sorted({z for c in CANDIDATES for z in (c[2],c[4])})
 for coord in needed:
  e=edges[coord]; ev['bucket__'+coord]=[bucket(v,e['q_1_3'],e['q_2_3']) for v in ev[coord]]
 # exact P1 parity before any intersection output is accepted
 parity=[]
 for coord in needed:
  for label in sorted({c[3] for c in CANDIDATES if c[2]==coord}|{c[5] for c in CANDIDATES if c[4]==coord}):
   for scope,d in scopes(ev):
    got=event_counts(d[d['bucket__'+coord].eq(label)])
    exp=p0i[(coord,scope,label)]
    ok=all(got[k]==exp[k] for k in ('n','extreme_up_count','extreme_down_count','none_count'))
    parity.append({'coordinate':coord,'bucket':label,'scope':scope,'match':ok,'got':got,'expected':{k:exp[k] for k in ('n','extreme_up_count','extreme_down_count','none_count')}})
    if not ok: raise RuntimeError(f'P1 parity mismatch {coord} {label} {scope}')
 records=[]
 for cid,target,left,llabel,right,rlabel in CANDIDATES:
  for scope,d in scopes(ev):
   eligible=d[d[left].notna() & d[right].notna() & d.event_class.ne('MISSING')].copy()
   lm=eligible['bucket__'+left].eq(llabel); rm=eligible['bucket__'+right].eq(rlabel); im=lm&rm
   cohorts={
    'PARENT':eligible,
    'INTERSECTION':eligible[im],
    'LEFT_FULL':eligible[lm],
    'RIGHT_FULL':eligible[rm],
    'LEFT_EXCLUSIVE':eligible[lm & ~rm],
    'RIGHT_EXCLUSIVE':eligible[rm & ~lm],
    'REST':eligible[~im],
   }
   for name,sub in cohorts.items(): records.append({'candidate_id':cid,'target':target,'left_coordinate':left,'left_bucket':llabel,'right_coordinate':right,'right_bucket':rlabel,'scope':scope,'cohort':name,**event_counts(sub)})
 out={'schema_id':'overnight_extreme_open_p3_intersection_sufficient_statistics@1.0','session_date':'2026-09-14','research_identity':protocol['research_identity'],'scientific_role':'mechanical_P3_sufficient_statistics_only_no_adjudication','candidate_count':6,'candidate_order':[c[0] for c in CANDIDATES],'evaluation_window':'2018-01-01..2020-12-31','edge_authority':'data/extreme_open_vnext_dev_sufficient_statistics_v1.json','edge_authority_sha256':sha256(p0_path),'P1_parity':parity,'P1_parity_all_match':all(r['match'] for r in parity),'records':records,'input_sources':sources,'policy_assertions':{'candidate_search':False,'edge_refit':False,'P2_postopen_intersections_opened':False,'three_way_intersections_opened':False,'mixed_target_intersections_opened':False,'reusable_blackbox_2021_2025_opened':False,'production_authority':False}}
 raw=json.dumps(out,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(); out['canonical_payload_sha256']=hashlib.sha256(raw).hexdigest(); return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out if a.out.is_absolute() else root/a.out; out.parent.mkdir(parents=True,exist_ok=True); payload=main_materialize(root); out.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+'\n'); digest=sha256(out); out.with_suffix(out.suffix+'.sha256').write_text(f'{digest}  {out.name}\n'); print(json.dumps({'status':'P3_MATERIALIZED_NO_ADJUDICATION','sha256':digest,'parity':payload['P1_parity_all_match']},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
