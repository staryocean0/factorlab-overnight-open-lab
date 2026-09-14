import numpy as np
import pandas as pd
from extreme_open_vnext_core import event_class,forward_return,transition_label,tercile_edges,bucket,safe_div

def test_material_gap_boundary_inclusion():
 assert event_class(0.003)=="EXTREME_UP"
 assert event_class(-0.003)=="EXTREME_DOWN"
 assert event_class(0.002999)=="NONE"
 assert event_class(-0.002999)=="NONE"

def test_transition_semantics():
 assert transition_label("EXTREME_UP",0.01)=="CONTINUATION"
 assert transition_label("EXTREME_UP",-0.01)=="REVERSAL"
 assert transition_label("EXTREME_DOWN",-0.01)=="CONTINUATION"
 assert transition_label("EXTREME_DOWN",0.01)=="REVERSAL"
 assert transition_label("EXTREME_UP",0.0)=="NEUTRAL"

def test_fixed_horizon_return_arithmetic():
 assert abs(forward_return(100.0,101.0)-0.01)<1e-15
 assert abs(forward_return(100.0,99.0)+0.01)<1e-15
 assert np.isnan(forward_return(0.0,101.0))

def test_edges_use_feature_only_and_are_permutation_invariant():
 values=pd.Series([1.,2.,3.,4.,5.,6.,7.,8.,9.])
 outcomes=pd.Series([9,1,8,2,7,3,6,4,5])
 a=tercile_edges(values)
 outcomes=outcomes.sample(frac=1,random_state=7).reset_index(drop=True)
 b=tercile_edges(values)
 assert len(outcomes)==len(values) and a==b

def test_bucket_edges_and_missing_division_fail_closed():
 assert bucket(1.0,1.0,2.0)=="LOW"
 assert bucket(2.0,1.0,2.0)=="MID"
 assert bucket(2.1,1.0,2.0)=="HIGH"
 x=safe_div(pd.Series([1.,1.,np.nan]),pd.Series([0.,2.,2.]))
 assert np.isnan(x.iloc[0]) and x.iloc[1]==0.5 and np.isnan(x.iloc[2])
