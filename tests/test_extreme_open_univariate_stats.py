import math
from extreme_open_univariate_stats import wilson_interval,newcombe_hybrid_score_diff,bh_adjust,rest_counts,effect_metrics,base_gate_vector,final_pass

def test_wilson_and_newcombe_are_bounded_and_directional():
 l,u=wilson_interval(80,100); assert 0<l<0.8<u<1
 dl,du=newcombe_hybrid_score_diff(80,100,40,100); assert dl>0 and du>dl

def test_newcombe_identical_rates_straddles_zero():
 l,u=newcombe_hybrid_score_diff(50,100,50,100); assert l<0<u

def test_bh_adjust_known_monotonic_example():
 q=bh_adjust([0.001,0.02,0.03,0.2]); assert abs(q[0]-0.004)<1e-12; assert abs(q[1]-0.04)<1e-12; assert abs(q[2]-0.04)<1e-12; assert abs(q[3]-0.2)<1e-12

def test_rest_counts_fail_closed():
 assert rest_counts(100,30,40,20)==(60,10)
 try: rest_counts(10,2,11,1)
 except ValueError: pass
 else: raise AssertionError('invalid subset must fail')

def test_effect_gate_is_or_not_and():
 m=effect_metrics(9,30,15,100)
 assert math.isclose(m['lift_pp'],15.0)
 gates=base_gate_vector(pooled_bucket_n=30,annual_bucket_n={'2018':10,'2019':10,'2020':10},metrics=m,ci_lower=0.01,annual_diffs={'2018':0.01,'2019':0.02,'2020':0.03})
 assert gates['material_effect'] is True
 assert final_pass(gates,0.05) is True

def test_return_direction_gate_is_required_when_supplied():
 gates={'a':True}
 assert final_pass(gates,0.05,True) is True
 assert final_pass(gates,0.05,False) is False
