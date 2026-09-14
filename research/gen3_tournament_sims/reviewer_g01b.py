import numpy as np
from scipy.special import expit, logit
from g01 import wauc
rng=np.random.default_rng(7)
def run(N=32000):
    s=rng.beta(2,3,N); s=np.clip(s,1e-4,1-1e-4)
    inbound=rng.random(N)<.12
    pb=np.clip(s+0.10*inbound,0,1)
    tau=np.where(s>=.75,.45,np.where(s>=.55,.55,0))
    pe=expit(logit(np.clip(pb,1e-4,1-1e-4))+tau)
    U=rng.random(N); yb=(U<pb).astype(float); ye=(U<pe).astype(float)
    period1=rng.random(N)<.55
    hr=np.where(period1,.10,.05)
    above=s>=.55
    hold=above&(rng.random(N)<hr)
    early=above&~hold
    reached=early&(rng.random(N)<.85)
    yobs=np.where(reached,ye,yb)
    truth=wauc(s,yb,np.ones(N))
    m=~early
    r9=wauc(s[m],yb[m],np.ones(m.sum()))
    w=np.where(hold,1/hr,1.0)
    ipw=wauc(s[m],yb[m],w[m])
    r7=wauc(s,yobs,np.ones(N))
    b4=above&(s<.75)
    band4_truth=yb[b4].mean(); nhold=(hold&b4).sum()
    band4_hold=yb[hold&b4].mean()
    band4_r7=yobs[b4].mean()
    b5=s>=.75
    return truth,r9,ipw,r7,band4_truth,band4_hold,band4_r7,nhold,yb[b5].mean(),yobs[b5].mean(),(hold&b5).sum(), s[b4].mean(), s[b5].mean()
R=np.array([run() for _ in range(200)])
names="truth r9 ipw r7 b4truth b4hold b4r7 nhold4 b5truth b5r7 nhold5 meanS4 meanS5".split()
for n,c in zip(names,R.T): print(f"{n:8s} mean {c.mean():.4f} sd {c.std():.4f}")
print("ipw-truth sd",(R[:,2]-R[:,0]).std(), "r9-truth mean",(R[:,1]-R[:,0]).mean(), "r7-truth",(R[:,3]-R[:,0]).mean())
print("b4 hold-truth sd",(R[:,5]-R[:,4]).std(),"r7 b4 err",(R[:,6]-R[:,4]).mean(),"b5 r7 err",(R[:,9]-R[:,8]).mean())
