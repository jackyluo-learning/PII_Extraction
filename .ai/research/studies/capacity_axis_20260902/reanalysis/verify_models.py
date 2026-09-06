"""Worked-case checks for censoring, clustering intervals and discrete p-values."""
import numpy as np
import pandas as pd
from scipy.optimize import check_grad
from lifelines import WeibullAFTFitter
from censored_models import weibull_fit
from recompute import wilson,mover,bootstrap_p

# Simulated thresholds include true right-censoring and interval observations.
rng=np.random.default_rng(1001);x=rng.uniform(-.5,.5,150);truth=np.exp(1.+.7*x)*rng.weibull(2.,len(x))
grid=np.array([.5,1.,2.,3.,4.]);lo=[];hi=[]
for t in truth:
 j=np.searchsorted(grid,t);lo.append(grid[j-1] if j else 0.);hi.append(grid[j] if j<len(grid) else np.inf)
lo=np.array(lo);hi=np.array(hi)
f=WeibullAFTFitter().fit_interval_censoring(pd.DataFrame({'lower':np.maximum(lo,1e-9),'upper':hi,'x':x}),'lower','upper')
ref=np.array([f.params_.loc[('lambda_','Intercept')],f.params_.loc[('lambda_','x')],f.params_.loc[('rho_','Intercept')]])
ours,nll=weibull_fit(x,lo,hi,start=ref)
assert np.isinf(hi).any() and (lo==0).any()
assert np.allclose(ref,ours,atol=2e-3,rtol=2e-3),(ref,ours)
assert abs(nll+f.log_likelihood_)<1e-4
assert .10<wilson(0,50/1.5)[1]<.11
assert mover(0,0,50/1.5,50/1.5)[0]<0<mover(0,0,50/1.5,50/1.5)[1]
assert np.allclose(wilson(1,50/1.5),1-wilson(0,50/1.5)[::-1])
# A boundary must be counted despite tiny binary-representation differences.
assert bootstrap_p(np.array([0.,4/150]),2/150)==1.
print({'right_censored_worked_case':int(np.isinf(hi).sum()),'max_solver_parameter_difference':float(np.max(np.abs(ref-ours))),'log_likelihood_difference':float(nll+f.log_likelihood_),'degenerate_intervals':'PASS','discrete_boundary_p':'PASS'})
