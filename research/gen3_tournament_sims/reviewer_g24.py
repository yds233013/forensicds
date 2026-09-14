import numpy as np
rng=np.random.default_rng(1)
n=130000
th={0:np.array([1,.7,.54,.43,.35]),1:np.array([1,.62,.45,.33,.26]),2:np.array([1,.52,.33,.22,.15])}
dev=rng.choice(3,n,p=[.45,.3,.25])
Ms=rng.integers(12,31,n)
Y6=np.zeros(n);Y7=np.zeros(n);V6=np.zeros(n);V7=np.zeros(n);U6=np.zeros(n);U7=np.zeros(n)
for i in range(n):
    M=Ms[i]; t=th[dev[i]]
    r=0.45/(1+np.exp(-(rng.normal(0,1.3,M)-0.2)))
    s6=r+rng.normal(0,0.12,M); s7=r+rng.normal(0,0.06,M)
    p6=np.argsort(-s6)[:5]; p7=np.argsort(-s7)[:5]
    V6[i]=(t*r[p6]).sum(); V7[i]=(t*r[p7]).sum()
    perm=rng.permutation(M)[:5]
    c=rng.random(5)< t*r[perm]
    Y6[i]=M*(c*(perm==p6)).sum(); Y7[i]=M*(c*(perm==p7)).sum()
    # item anywhere, position unaware, weight M/5
    U6[i]=(M/5)*(c*np.isin(perm,p6)).sum(); U7[i]=(M/5)*(c*np.isin(perm,p7)).sum()
print("truth",V6.mean(),V7.mean(),"lift",V7.mean()-V6.mean())
print("slot IPS",Y6.mean(),Y7.mean(),"sd",Y6.std(),"SE",Y6.std()/np.sqrt(n))
D=Y7-Y6
print("paired SE",D.std()/np.sqrt(n),"unpaired SE",np.sqrt(Y6.var()+Y7.var())/np.sqrt(n))
print("unaware",U6.mean(),U7.mean(),"SE",U6.std()/np.sqrt(n))
