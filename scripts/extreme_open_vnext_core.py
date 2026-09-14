from __future__ import annotations
import math
import numpy as np
import pandas as pd

THRESHOLD=0.003
HORIZONS={"09:35_to_09:50":"close_0950","09:35_to_10:35":"close_1035"}
P1=("V6A_expected_open_state","B1_global_risk","B2_china_offshore","B4_driver_coherence","causal_prior_trend_parent","causal_prior_volatility_parent")
P2=("gap_rvol","abs_gap_rvol","C1_15m_trend_gap_interaction","C2_60m_volatility_gap_interaction","B4_driver_coherence")
UNAVAILABLE={"V6A_expected_open_state":"UNAVAILABLE_WITH_REASON: frozen V6A fits through 2018-12-31; no separately frozen leakage-free V6A prediction carrier exists for the required 2018-2020 evaluation, so no proxy/refit is substituted."}
FORMULAS={
 "B1_global_risk":"0.5*(us_nasdaq/RMS60_prev(us_nasdaq)-us_vix_chg/RMS60_prev(us_vix_chg))",
 "B2_china_offshore":"a50_channel_return/RMS60_prev(a50_channel_return)",
 "B4_driver_coherence":"(B1+B2+fx_z)/(abs(B1)+abs(B2)+abs(fx_z)); fx_z=-hkma_usdcny_closure_return/RMS60_prev(hkma_usdcny_closure_return)",
 "causal_prior_trend_parent":"r20/(sqrt(20)*rvol20)","causal_prior_volatility_parent":"log(rvol20)",
 "gap_rvol":"gap/rvol20","abs_gap_rvol":"abs(gap_rvol)",
 "C1_15m_trend_gap_interaction":"causal_prior_trend_parent*gap_rvol",
 "C2_60m_volatility_gap_interaction":"gap_rvol*causal_prior_volatility_parent","forward_return":"close_end/close_0935-1"}

def rms_prev(s):
 x=pd.to_numeric(s,errors="coerce"); return np.sqrt(x.pow(2).shift(1).rolling(60,min_periods=20).mean())
def safe_div(a,b):
 a=pd.to_numeric(a,errors="coerce"); b=pd.to_numeric(b,errors="coerce"); z=pd.Series(np.nan,index=a.index,dtype=float); m=np.isfinite(a)&np.isfinite(b)&b.ne(0); z.loc[m]=a.loc[m]/b.loc[m]; return z
def finite(s): return np.isfinite(pd.to_numeric(s,errors="coerce").to_numpy(float))
def event_class(v):
 if not np.isfinite(v): return "MISSING"
 if v>=THRESHOLD:return "EXTREME_UP"
 if v<=-THRESHOLD:return "EXTREME_DOWN"
 return "NONE"
def forward_return(a,b): return np.nan if (not np.isfinite(a) or not np.isfinite(b) or a==0) else b/a-1
def transition_label(ev,r):
 if not np.isfinite(r):return "MISSING"
 if r==0:return "NEUTRAL"
 return "CONTINUATION" if ((ev=="EXTREME_UP" and r>0) or (ev=="EXTREME_DOWN" and r<0)) else "REVERSAL"
def tercile_edges(s):
 x=pd.to_numeric(s,errors="coerce"); x=x[np.isfinite(x)]; q=x.quantile([1/3,2/3],interpolation="linear"); return float(q.iloc[0]),float(q.iloc[1]),int(len(x))
def bucket(v,q1,q2):
 if not np.isfinite(v):return None
 return "LOW" if v<=q1 else ("MID" if v<=q2 else "HIGH")
def build_coordinates(x):
 x=x.copy()
 for c in ["gap","r20","rvol20","us_nasdaq","us_vix_chg","a50_channel_return","hkma_usdcny_closure_return","close_0935","close_0950","close_1035"]: x[c]=pd.to_numeric(x[c],errors="coerce")
 for c in ["us_nasdaq","us_vix_chg","a50_channel_return","hkma_usdcny_closure_return"]: x[c+"_rms"]=rms_prev(x[c])
 x["B1_global_risk"]=.5*(safe_div(x.us_nasdaq,x.us_nasdaq_rms)+safe_div(-x.us_vix_chg,x.us_vix_chg_rms)); x["B2_china_offshore"]=safe_div(x.a50_channel_return,x.a50_channel_return_rms); fx=safe_div(-x.hkma_usdcny_closure_return,x.hkma_usdcny_closure_return_rms)
 den=x.B1_global_risk.abs()+x.B2_china_offshore.abs()+fx.abs(); x["B4_driver_coherence"]=safe_div(x.B1_global_risk+x.B2_china_offshore+fx,den)
 rv=x.rvol20.where(x.rvol20.gt(0)); x["causal_prior_trend_parent"]=safe_div(x.r20,math.sqrt(20)*rv); x["causal_prior_volatility_parent"]=np.log(rv); x["gap_rvol"]=safe_div(x.gap,rv); x["abs_gap_rvol"]=x.gap_rvol.abs(); x["C1_15m_trend_gap_interaction"]=x.causal_prior_trend_parent*x.gap_rvol; x["C2_60m_volatility_gap_interaction"]=x.gap_rvol*x.causal_prior_volatility_parent
 x["event_class"]=[event_class(v) for v in x.gap]
 for k,end in HORIZONS.items(): x["ret_"+k]=[forward_return(a,b) for a,b in zip(x.close_0935,x[end])]
 return x
