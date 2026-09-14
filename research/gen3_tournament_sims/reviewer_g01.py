import numpy as np
from scipy.special import expit, logit
rng=np.random.default_rng(1)
def wauc(s,y,w):
    o=np.argsort(s); s,y,w=s[o],y[o],w[o]
    wn=np.cumsum(w*(1-y)); # weight of negatives with score <= current
    pos=y==1
    return (w[pos]*(wn[pos]-0)).sum()/ (w[y==1].sum()*w[y==0].sum())
for a,b in [(2,3),(1.5,2.5),(1.2,2),(1,1.8)]:
    s=rng.beta(a,b,200000); y=rng.random(200000)<s
    print(a,b,'AUC',round(wauc(s,y.astype(float),np.ones_like(s)),3),'share>=.55',round((s>=.55).mean(),3),'band4',round(((s>=.55)&(s<.75)).mean(),3))
