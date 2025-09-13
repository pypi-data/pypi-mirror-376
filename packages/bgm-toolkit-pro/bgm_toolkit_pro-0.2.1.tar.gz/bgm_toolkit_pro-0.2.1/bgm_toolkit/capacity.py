import numpy as np
def apply_soft_capacity(D, shares, capacities, lam=0.5):
    D=np.asarray(D,float).copy()
    if capacities is None: return D
    demand=shares.sum(axis=0); cap=np.asarray(capacities,float)
    util=np.divide(demand,cap,out=np.zeros_like(demand),where=cap>0)
    over=np.clip(util-1.0,0.0,None)
    factor=1.0+lam*over
    return D*factor[None,:]
def apply_hard_capacity_once(shares, capacities):
    S=np.asarray(shares,float).copy()
    if capacities is None: return S
    colsum=S.sum(axis=0); cap=np.asarray(capacities,float)
    scale=np.ones_like(colsum); mask=(cap>0)&(colsum>cap)
    scale[mask]=cap[mask]/colsum[mask]
    S=S*scale[None,:]
    row=S.sum(axis=1,keepdims=True); row[row==0]=1.0
    return S/row
