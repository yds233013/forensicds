import numpy as np
rng=np.random.default_rng(3)
def km(T,E,w,h):
    T=np.ceil(T).astype(int)
    D=np.bincount(T[E==1],weights=w[E==1],minlength=600)
    C=np.bincount(T,weights=w,minlength=600)
    atrisk=np.cumsum(C[::-1])[::-1]
    with np.errstate(invalid='ignore',divide='ignore'):
        q=np.where(atrisk>0,D/atrisk,0)
    return np.prod(1-q[:h+1])
def gen(n,start,end,S180):
    t0=rng.uniform(start,end,n); lam=-np.log(S180)/180
    ev=rng.exponential(1/lam,n); fu=548-t0
    return np.minimum(ev,fu),(ev<=fu).astype(int)
specs={('v1','h'):(2500,0,244,0.315),('v2','h'):(9600,244,548,0.487),('v1','o'):(47500,0,244,0.38),('v2','o'):(70400,244,548,0.539)}
wv={'v1':50/130,'v2':80/130}; P={('v1','h'):.05,('v2','h'):.12,('v1','o'):.95,('v2','o'):.88}
res=[]
for rep in range(200):
    parts={k:gen(*v) for k,v in specs.items()}
    row=[]
    for arm in 'ho':
        row.append(sum(wv[v]*km(*parts[(v,arm)],np.ones(specs[(v,arm)][0]),180) for v in wv))
    for ipw in (False,True):
        for arm in 'ho':
            T=np.concatenate([parts[('v1',arm)][0],parts[('v2',arm)][0]]);E=np.concatenate([parts[('v1',arm)][1],parts[('v2',arm)][1]])
            w=np.concatenate([np.full(specs[('v1',arm)][0],1/P[('v1',arm)] if ipw else 1),np.full(specs[('v2',arm)][0],1/P[('v2',arm)] if ipw else 1)])
            row.append(km(T,E,w,180))
    res.append(row)
R=np.array(res)
th=50/130*.315+80/130*.487; to=50/130*.38+80/130*.539
print('truth h',round(th,4),'o',round(to,4),'diff',round(to-th,4))
for nm,c in zip(['strat_h','strat_o','pool_h','pool_o','ipw_h','ipw_o'],R.T): print(nm,round(c.mean(),4),'bias',round(c.mean()-(th if nm.endswith('h') else to),4),'sd',round(c.std(),4))
print('diff strat',round((R[:,1]-R[:,0]).mean(),4),'pool',round((R[:,3]-R[:,2]).mean(),4),'ipw pooled',round((R[:,5]-R[:,4]).mean(),4))
