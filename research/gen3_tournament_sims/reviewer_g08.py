import numpy as np, os
pass
from sklearn.ensemble import HistGradientBoostingRegressor as H
rng=np.random.default_rng(0)
n=30000
reg=rng.integers(0,6,n); h=rng.integers(1,8,n); dow=rng.integers(0,7,n); hol=(rng.random(n)<.03).astype(int)
temp=rng.normal(10,7,n); base=1000*(1+reg)
lags=base[:,None]*(1+0.1*np.sin(temp/5))[:,None]*(1+rng.normal(0,.02,(n,7)))
lags[rng.random((n,7))<.05]=np.nan
roll=np.nanmean(lags,1)
X=np.column_stack([lags,roll,temp,np.maximum(0,15.5-temp),dow,hol,h,reg])
y=base*(1+0.1*np.sin(temp/5))*(1+0.05*(dow>4))*(1+rng.normal(0,.03,n))
kw=dict(loss="absolute_error",max_iter=400,learning_rate=0.05,max_leaf_nodes=31,min_samples_leaf=50,l2_regularization=0.5,early_stopping=False,random_state=11)
Xt=X[:2000]
p0=H(**kw).fit(X,y).predict(Xt)
perm=rng.permutation(n)
p1=H(**kw).fit(X[perm],y[perm]).predict(Xt)
cols=list(range(X.shape[1])); cols[0],cols[1]=cols[1],cols[0]
p2=H(**kw).fit(X[:,cols],y).predict(Xt[:,cols])
Xf=X.astype(np.float32)
p3=H(**kw).fit(Xf,y).predict(Xt.astype(np.float32))
print('row shuffle maxdiff',np.abs(p0-p1).max(),'rel',np.abs(p0-p1).max()/np.abs(p0).mean())
print('col swap maxdiff',np.abs(p0-p2).max())
print('float32 maxdiff',np.abs(p0-p3).max())
