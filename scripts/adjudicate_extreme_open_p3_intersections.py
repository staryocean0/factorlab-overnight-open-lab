#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from extreme_open_univariate_stats import bh_adjust, effect_metrics, fisher_two_sided, newcombe_hybrid_score_diff, prob

YEARS=('2018','2019','2020')
TARGET_FIELD={'EXTREME_UP':'extreme_up_count','EXTREME_DOWN':'extreme_down_count'}

def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def idx(rows):
 out={}
 for r in rows:
  k=(r['candidate_id'],r['scope'],r['cohort'])
  if k in out: raise RuntimeError(f'duplicate P3 key {k}')
  out[k]=r
 return out

def compare(a,ax,b,bx):
 pa=prob(ax,a); pb=prob(bx,b); ci=newcombe_hybrid_score_diff(ax,a,bx,b); p=fisher_two_sided(ax,a,bx,b)
 return {'left_n':a,'left_target':ax,'right_n':b,'right_target':bx,'p_left':pa,'p_right':pb,'difference':None if pa is None or pb is None else pa-pb,'ci95':{'lower':ci[0],'upper':ci[1]},'fisher_p':p}

def material_vs_stronger(pint,pleft,pright):
 vals=[x for x in (pleft,pright) if x is not None]
 if pint is None or len(vals)!=2: return {'stronger_constituent_probability':None,'incremental_lift_pp':None,'incremental_risk_ratio':None,'pass':False}
 strongest=max(vals); lift=100*(pint-strongest); rr=None if strongest<=0 else pint/strongest
 return {'stronger_constituent_probability':strongest,'incremental_lift_pp':lift,'incremental_risk_ratio':rr,'pass':bool(lift>=5.0 or (rr is not None and rr>=1.15))}

def build_candidate(index,cid,target):
 field=TARGET_FIELD[target]
 def row(scope,cohort): return index[(cid,scope,cohort)]
 p=row('pooled_2018_2020','PARENT'); inter=row('pooled_2018_2020','INTERSECTION'); rest=row('pooled_2018_2020','REST'); lf=row('pooled_2018_2020','LEFT_FULL'); rf=row('pooled_2018_2020','RIGHT_FULL'); le=row('pooled_2018_2020','LEFT_EXCLUSIVE'); re=row('pooled_2018_2020','RIGHT_EXCLUSIVE')
 parent_effect=effect_metrics(inter[field],inter['n'],p[field],p['n'])
 primary=compare(inter['n'],inter[field],rest['n'],rest[field]); inc_l=compare(inter['n'],inter[field],le['n'],le[field]); inc_r=compare(inter['n'],inter[field],re['n'],re[field])
 pleft=prob(lf[field],lf['n']); pright=prob(rf[field],rf['n']); extra=material_vs_stronger(parent_effect['p_bucket'],pleft,pright)
 annual={}; primary_pos=True; left_pos=True; right_pos=True; int_n_ok=True; lex_n_ok=True; rex_n_ok=True
 for y in YEARS:
  iy=row(y,'INTERSECTION'); ry=row(y,'REST'); ley=row(y,'LEFT_EXCLUSIVE'); rey=row(y,'RIGHT_EXCLUSIVE')
  pc=compare(iy['n'],iy[field],ry['n'],ry[field]); lc=compare(iy['n'],iy[field],ley['n'],ley[field]); rc=compare(iy['n'],iy[field],rey['n'],rey[field])
  annual[y]={'intersection_n':iy['n'],'left_exclusive_n':ley['n'],'right_exclusive_n':rey['n'],'primary_difference':pc['difference'],'left_incremental_difference':lc['difference'],'right_incremental_difference':rc['difference']}
  int_n_ok &= iy['n']>=5; lex_n_ok &= ley['n']>=5; rex_n_ok &= rey['n']>=5
  primary_pos &= pc['difference'] is not None and pc['difference']>0
  left_pos &= lc['difference'] is not None and lc['difference']>0
  right_pos &= rc['difference'] is not None and rc['difference']>0
 gates={
  'intersection_pooled_n':inter['n']>=30,
  'intersection_annual_n':int_n_ok,
  'left_exclusive_pooled_n':le['n']>=30,
  'left_exclusive_annual_n':lex_n_ok,
  'right_exclusive_pooled_n':re['n']>=30,
  'right_exclusive_annual_n':rex_n_ok,
  'positive_parent_enrichment':parent_effect['p_bucket'] is not None and parent_effect['p_parent'] is not None and parent_effect['p_bucket']>parent_effect['p_parent'],
  'parent_material_effect':(parent_effect['lift_pp'] is not None and parent_effect['lift_pp']>=12.5) or (parent_effect['risk_ratio'] is not None and parent_effect['risk_ratio']>=1.5),
  'primary_newcombe_lower_gt_zero':primary['ci95']['lower'] is not None and primary['ci95']['lower']>0,
  'primary_annual_positive':primary_pos,
  'higher_than_both_full_constituents':parent_effect['p_bucket'] is not None and pleft is not None and pright is not None and parent_effect['p_bucket']>pleft and parent_effect['p_bucket']>pright,
  'incremental_material_over_stronger_constituent':extra['pass'],
  'left_increment_newcombe_lower_gt_zero':inc_l['ci95']['lower'] is not None and inc_l['ci95']['lower']>0,
  'right_increment_newcombe_lower_gt_zero':inc_r['ci95']['lower'] is not None and inc_r['ci95']['lower']>0,
  'left_increment_annual_positive':left_pos,
  'right_increment_annual_positive':right_pos,
 }
 return {'candidate_id':cid,'target':target,'left_coordinate':inter['left_coordinate'],'left_bucket':inter['left_bucket'],'right_coordinate':inter['right_coordinate'],'right_bucket':inter['right_bucket'],'parent_effect':parent_effect,'left_full_probability':pleft,'right_full_probability':pright,'incremental_over_stronger_constituent':extra,'primary_comparison':primary,'left_incremental_comparison':inc_l,'right_incremental_comparison':inc_r,'annual':annual,'gates_pre_bh':gates,'primary_fisher_p':primary['fisher_p'],'left_increment_fisher_p':inc_l['fisher_p'],'right_increment_fisher_p':inc_r['fisher_p']}

def adjudicate(root):
 protocol=json.loads((root/'docs/governance/extreme_open_preopen_intersections_dev_v1_protocol.json').read_text()); state=json.loads((root/'docs/governance/extreme_open_preopen_intersections_dev_v1_state.json').read_text())
 if state['status']!='AUTHORIZED_NOT_YET_MATERIALIZED_OR_EXECUTED' or state['candidate_count']!=6 or state['P4_authorized']: raise RuntimeError('P3 state authorization drift')
 carrier_path=root/'data/extreme_open_p3_intersection_sufficient_statistics_v1.json'; carrier=json.loads(carrier_path.read_text())
 if not carrier['P1_parity_all_match'] or carrier['candidate_count']!=6: raise RuntimeError('P3 carrier parity/count failure')
 index=idx(carrier['records']); rows=[]
 targets={c['candidate_id']:c['target'] for c in protocol['candidates']}
 for c in protocol['candidates']: rows.append(build_candidate(index,c['candidate_id'],c['target']))
 # primary BH: 3 candidates per target
 for target in ('EXTREME_UP','EXTREME_DOWN'):
  fam=[r for r in rows if r['target']==target]; qs=bh_adjust([r['primary_fisher_p'] for r in fam])
  for r,q in zip(fam,qs): r['primary_bh_q']=q; r['primary_bh_pass']=q is not None and q<=0.10
  # incremental family: 3 candidates x 2 constituent-exclusive tests
  ps=[]; refs=[]
  for r in fam:
   ps.extend([r['left_increment_fisher_p'],r['right_increment_fisher_p']]); refs.extend([(r,'left'),(r,'right')])
  iq=bh_adjust(ps)
  for (r,side),q in zip(refs,iq): r[side+'_increment_bh_q']=q; r[side+'_increment_bh_pass']=q is not None and q<=0.10
 for r in rows:
  r['pass_all_gates']=bool(all(r['gates_pre_bh'].values()) and r['primary_bh_pass'] and r['left_increment_bh_pass'] and r['right_increment_bh_pass'])
 survivors=[{'candidate_id':r['candidate_id'],'target':r['target'],'p_intersection':r['parent_effect']['p_bucket'],'p_parent':r['parent_effect']['p_parent'],'parent_lift_pp':r['parent_effect']['lift_pp'],'parent_risk_ratio':r['parent_effect']['risk_ratio'],'incremental_lift_pp_over_stronger_constituent':r['incremental_over_stronger_constituent']['incremental_lift_pp'],'incremental_risk_ratio_over_stronger_constituent':r['incremental_over_stronger_constituent']['incremental_risk_ratio'],'primary_bh_q':r['primary_bh_q'],'left_increment_bh_q':r['left_increment_bh_q'],'right_increment_bh_q':r['right_increment_bh_q']} for r in rows if r['pass_all_gates']]
 return {'schema_id':'overnight_extreme_open_p3_intersections_dev_receipt@1.0','session_date':'2026-09-14','research_identity':protocol['research_identity'],'protocol':'docs/governance/extreme_open_preopen_intersections_dev_v1_protocol.json','carrier':'data/extreme_open_p3_intersection_sufficient_statistics_v1.json','carrier_sha256':sha256(carrier_path),'P1_parity_all_match':carrier['P1_parity_all_match'],'hypotheses':rows,'survivors':survivors,'summary':{'candidate_count':len(rows),'survivor_count':len(survivors)},'execution_boundary':{'P3_preopen_only':True,'P2_postopen_intersections_opened':False,'candidate_search':False,'edge_refit':False,'reusable_blackbox_2021_2025_opened':False,'P4_authorized':False,'production_authority':False},'production_authority':False}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out if a.out.is_absolute() else root/a.out; out.parent.mkdir(parents=True,exist_ok=True); r=adjudicate(root); out.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n'); print(json.dumps(r['summary'],sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
