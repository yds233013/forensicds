import numpy as np
rng=np.random.default_rng(0)
# 1) stopping-time bias of profile scaling on sell-out days (uniform profile)
for lam in [6,12,25]:
  for I in [2,4,8,15]:
    est=[];tru=[]
    for _ in range(20000):
        G=rng.gamma(8,1/8); n=rng.poisson(lam*G); t=np.sort(rng.random(n))
        if n<=I: continue
        tau=t[I-1]      # sell out at I-th arrival
        est.append(I/tau); tru.append(n)
    if len(est)>200: print("lam",lam,"I",I,"sellout share",len(est)/20000,"est/true",np.mean(est)/np.mean(tru))
# 2) Jensen gap on WAPE: true realized demand vs best-possible expected demand on censored rows
n=400000
lam=rng.lognormal(1.5,0.9,n)
G=rng.gamma(8,1/8,n); D=rng.poisson(lam*G)
F3=lam*np.exp(rng.normal(0,0.25,n)); F4=lam*np.exp(rng.normal(-0.05,0.35,n))
inv=np.ceil(lam*rng.uniform(0.9,2.2,n))
cens=D>inv   # stockout days (selected on high demand)
print("censored row share",cens.mean(),"unit share",D[cens].sum()/D.sum())
# oracle-ish estimate: on censored rows, E[D | D>inv, lam] via simulation approx -> use conditional mean by MC per row is heavy; approximate with lam*G posterior ~ use D replaced by E[D|D>inv] computed quickly
# approximate E[D|D>inv] by rejection using poisson-gamma = negbin
from math import *
r=8; 
Dhat=D.astype(float).copy()
idx=np.where(cens)[0]
for i in idx[:]:
    m=lam[i]; p=r/(r+m)
    ks=np.arange(int(inv[i])+1, int(inv[i]+10*m+50))
    pm=rng  # placeholder
    lp=np.array([lgamma(k+r)-lgamma(r)-lgamma(k+1)+r*log(p)+k*log(1-p) for k in ks])
    w=np.exp(lp-lp.max()); Dhat[i]=(ks*w).sum()/w.sum()
def wape(F,D): return np.abs(F-D).sum()/D.sum()
print("WAPE v3 true",wape(F3,D),"with Dhat",wape(F3,Dhat))
print("WAPE v4 true",wape(F4,D),"with Dhat",wape(F4,Dhat))
