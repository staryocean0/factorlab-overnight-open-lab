#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from extreme_open_univariate_stats import (
    bh_adjust, base_gate_vector, effect_metrics, final_pass, fisher_two_sided,
    newcombe_hybrid_score_diff, prob, rest_counts,
)

YEARS=("2018","2019","2020")
BUCKETS=("LOW","MID","HIGH")
P1_TARGETS={"EXTREME_UP":"extreme_up_count","EXTREME_DOWN":"extreme_down_count"}
P2_TARGETS={"CONTINUATION":"continuation_count","REVERSAL":"reversal_count"}


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def indexed(rows, fields):
    out={}
    for row in rows:
        key=tuple(row[f] for f in fields)
        if key in out: raise RuntimeError(f'duplicate carrier key {key}')
        out[key]=row
    return out


def annual_probability_diffs(index, keyprefix, target_field, n_field='n'):
    diffs={}; ns={}
    for y in YEARS:
        parent=index[keyprefix+(y,"PARENT")]
        bucket=index[keyprefix+(y,keyprefix[-1])] if False else None
    return diffs,ns


def p1_hypothesis(index, coord, bucket, target, target_field):
    pooled_parent=index[(coord,"pooled_2018_2020","PARENT")]
    pooled_bucket=index[(coord,"pooled_2018_2020",bucket)]
    rn,rx=rest_counts(pooled_parent['n'],pooled_parent[target_field],pooled_bucket['n'],pooled_bucket[target_field])
    metrics=effect_metrics(pooled_bucket[target_field],pooled_bucket['n'],pooled_parent[target_field],pooled_parent['n'])
    ci=newcombe_hybrid_score_diff(pooled_bucket[target_field],pooled_bucket['n'],rx,rn)
    p=fisher_two_sided(pooled_bucket[target_field],pooled_bucket['n'],rx,rn)
    annual_n={}; annual_diff={}; annual={}
    for y in YEARS:
        parent=index[(coord,y,"PARENT")]; b=index[(coord,y,bucket)]
        r_n,r_x=rest_counts(parent['n'],parent[target_field],b['n'],b[target_field])
        pb=prob(b[target_field],b['n']); pr=prob(r_x,r_n)
        annual_n[y]=b['n']; annual_diff[y]=None if pb is None or pr is None else pb-pr
        annual[y]={"bucket_n":b['n'],"bucket_target":b[target_field],"rest_n":r_n,"rest_target":r_x,"p_bucket":pb,"p_rest":pr,"difference":annual_diff[y]}
    gates=base_gate_vector(pooled_bucket_n=pooled_bucket['n'],annual_bucket_n=annual_n,metrics=metrics,ci_lower=ci[0],annual_diffs=annual_diff)
    return {"phase":"P1","coordinate":coord,"bucket":bucket,"target":target,"pooled":{"bucket_n":pooled_bucket['n'],"bucket_target":pooled_bucket[target_field],"parent_n":pooled_parent['n'],"parent_target":pooled_parent[target_field],"rest_n":rn,"rest_target":rx,**metrics,"p_rest":prob(rx,rn),"bucket_minus_rest_ci95":{"lower":ci[0],"upper":ci[1]},"fisher_p":p},"annual":annual,"gates_pre_bh":gates,"fisher_p":p}


def p2_hypothesis(index, coord, bucket, event, horizon, target, target_field):
    parent=index[(coord,event,horizon,"pooled_2018_2020","PARENT")]
    b=index[(coord,event,horizon,"pooled_2018_2020",bucket)]
    pn=parent['valid_return_n']; bn=b['valid_return_n']; px=parent[target_field]; bx=b[target_field]
    rn,rx=rest_counts(pn,px,bn,bx)
    metrics=effect_metrics(bx,bn,px,pn)
    ci=newcombe_hybrid_score_diff(bx,bn,rx,rn); p=fisher_two_sided(bx,bn,rx,rn)
    annual_n={}; annual_diff={}; annual={}
    for y in YEARS:
        py=index[(coord,event,horizon,y,"PARENT")]; by=index[(coord,event,horizon,y,bucket)]
        pny=py['valid_return_n']; bny=by['valid_return_n']; pxy=py[target_field]; bxy=by[target_field]
        rny,rxy=rest_counts(pny,pxy,bny,bxy); pb=prob(bxy,bny); pr=prob(rxy,rny)
        annual_n[y]=bny; annual_diff[y]=None if pb is None or pr is None else pb-pr
        annual[y]={"bucket_valid_n":bny,"bucket_target":bxy,"rest_valid_n":rny,"rest_target":rxy,"p_bucket":pb,"p_rest":pr,"difference":annual_diff[y]}
    mean_return=None if bn<=0 else b['sum_forward_return']/bn
    desired_positive=(event=="EXTREME_UP" and target=="CONTINUATION") or (event=="EXTREME_DOWN" and target=="REVERSAL")
    return_gate=mean_return is not None and ((mean_return>0) if desired_positive else (mean_return<0))
    gates=base_gate_vector(pooled_bucket_n=bn,annual_bucket_n=annual_n,metrics=metrics,ci_lower=ci[0],annual_diffs=annual_diff)
    return {"phase":"P2","coordinate":coord,"bucket":bucket,"event":event,"horizon":horizon,"target":target,"pooled":{"bucket_valid_n":bn,"bucket_target":bx,"parent_valid_n":pn,"parent_target":px,"rest_valid_n":rn,"rest_target":rx,**metrics,"p_rest":prob(rx,rn),"bucket_minus_rest_ci95":{"lower":ci[0],"upper":ci[1]},"fisher_p":p,"bucket_mean_forward_return":mean_return},"annual":annual,"gates_pre_bh":gates,"return_direction_gate":return_gate,"fisher_p":p}


def apply_bh_and_pass(rows):
    q=bh_adjust([r['fisher_p'] for r in rows])
    for r,v in zip(rows,q):
        r['bh_q']=v
        r['bh_q_le_0_10']=v is not None and v<=0.10
        r['pass_all_gates']=final_pass(r['gates_pre_bh'],v,r.get('return_direction_gate'))
    return rows


def adjudicate(root: Path) -> dict:
    protocol=json.loads((root/'docs/governance/extreme_open_univariate_dev_v1_protocol.json').read_text())
    state=json.loads((root/'docs/governance/extreme_open_univariate_dev_v1_state.json').read_text())
    carrier_path=root/protocol['p0_carrier']['path']
    if sha256(carrier_path)!=protocol['p0_carrier']['sha256']: raise RuntimeError('carrier sha256 mismatch')
    if state['status']!='AUTHORIZED_NOT_YET_EXECUTED' or not state['P1_authorized'] or not state['P2_authorized'] or state['P3_authorized']: raise RuntimeError('state does not authorize exact P1/P2-only execution')
    carrier=json.loads(carrier_path.read_text())
    p1_index=indexed(carrier['p1_preopen_event_propensity'],('coordinate','scope','cohort'))
    p2_index=indexed(carrier['p2_postopen_transition'],('coordinate','event','horizon','scope','cohort'))
    p1=[]; p1_families={}
    for target,target_field in P1_TARGETS.items():
        family=[]
        for coord in protocol['p1_coordinates']:
            for bucket in BUCKETS: family.append(p1_hypothesis(p1_index,coord,bucket,target,target_field))
        apply_bh_and_pass(family); p1.extend(family); p1_families[target]=len(family)
    p2=[]; p2_families={}
    for event in ("EXTREME_UP","EXTREME_DOWN"):
        for horizon in protocol['fixed_horizons']:
            for target,target_field in P2_TARGETS.items():
                family=[]
                for coord in protocol['p2_coordinates']:
                    for bucket in BUCKETS: family.append(p2_hypothesis(p2_index,coord,bucket,event,horizon,target,target_field))
                apply_bh_and_pass(family); p2.extend(family); p2_families[f'{event}|{horizon}|{target}']=len(family)
    p1_surv=[{k:r[k] for k in ('coordinate','bucket','target')}|{"p_bucket":r['pooled']['p_bucket'],"p_parent":r['pooled']['p_parent'],"lift_pp":r['pooled']['lift_pp'],"risk_ratio":r['pooled']['risk_ratio'],"bh_q":r['bh_q']} for r in p1 if r['pass_all_gates']]
    p2_surv=[{k:r[k] for k in ('coordinate','bucket','event','horizon','target')}|{"p_bucket":r['pooled']['p_bucket'],"p_parent":r['pooled']['p_parent'],"lift_pp":r['pooled']['lift_pp'],"risk_ratio":r['pooled']['risk_ratio'],"bh_q":r['bh_q'],"mean_forward_return":r['pooled']['bucket_mean_forward_return']} for r in p2 if r['pass_all_gates']]
    return {"schema_id":"overnight_extreme_open_univariate_dev_receipt@1.0","session_date":"2026-09-14","research_identity":protocol['research_identity'],"protocol":"docs/governance/extreme_open_univariate_dev_v1_protocol.json","carrier":protocol['p0_carrier']['path'],"carrier_sha256":protocol['p0_carrier']['sha256'],"execution_boundary":{"P1":True,"P2":True,"P3":False,"reusable_blackbox_2021_2025_opened":False,"threshold_search":False,"clock_search":False,"candidate_family_mutation":False,"strategy_pnl_selection":False,"production_authority":False},"family_sizes":{"P1":p1_families,"P2":p2_families},"P1_hypotheses":p1,"P2_hypotheses":p2,"P1_survivors":p1_surv,"P2_survivors":p2_surv,"summary":{"P1_hypothesis_count":len(p1),"P2_hypothesis_count":len(p2),"P1_survivor_count":len(p1_surv),"P2_survivor_count":len(p2_surv)},"production_authority":False}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1]); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out if a.out.is_absolute() else root/a.out; out.parent.mkdir(parents=True,exist_ok=True); result=adjudicate(root); out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n'); print(json.dumps(result['summary'],sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
