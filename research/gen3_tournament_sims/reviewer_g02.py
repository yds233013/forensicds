import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as H
from sklearn.linear_model import LogisticRegression
rng=np.random.default_rng(3)
segs=["retail","office","food","contr","manuf","hosp"]
bseg=np.log(np.array([.07,.055,.11,.10,.08,.075]))
def mix(b):
    m=np.array([.25,.2,.14,.12,.15,.14])
    if b>=4: m=np.array([.20,.16,.19,.21,.12,.12])
    return m/m.sum()
form_share=[0,0,0,0,.55,.96]
def gen(n,b,book=False):
    seg=rng.choice(6,n,p=mix(b if not book else 5))
    form=(rng.random(n)<(1.0 if book else form_share[b])).astype(int)
    seas=((seg==2)&(rng.random(n)<((.38 if book else (.34 if b==5 else 0))))).astype(int)
    size=rng.choice(3,n,p=[.5,.35,.15]); spr=(rng.random(n)<.4).astype(int); pc=rng.poisson(.3,n)
    age=rng.uniform(0,60,n)
    loglam=bseg[seg]+np.array([0,.35,.8])[size]-.25*spr+.18*pc+.03*form-.45*seas+0.006*(age-30)+rng.normal(0,.3,n)*0
    e=np.where(seas==1,rng.uniform(.25,.5,n),np.where(rng.random(n)<.07,rng.uniform(.1,1,n),1.0))
    lam=np.exp(loglam); N=rng.poisson(lam*e)
    return pd.DataFrame(dict(seg=seg,form=form,seas=seas,sz=size,spr=spr,pc=pc,age=age,e=e,lam=lam,y=(N>0).astype(int),batch=b))
rates=[.1,.1,.1,.1,.1,.25]
tr=[];va=[]
for b in range(6):
    d=gen(90000,b); split=rng.random(len(d))<.8
    for part,lst in [(d[split],tr),(d[~split],va)]:
        keep=(part.y==1)|(rng.random(len(part))<rates[b])
        p=part[keep].copy(); p["w"]=np.where(p.y==1,1,1/rates[b]); lst.append(p)
tr=pd.concat(tr); va=pd.concat(va)
book=gen(60000,5,book=True)
X=lambda d: np.c_[d.seg,d.form,d.seas,d.sz,d.spr,d.pc,d.age,np.log(d.e)]
kw=dict(max_iter=300,learning_rate=.06,max_leaf_nodes=31,random_state=7,categorical_features=[0],early_stopping=False)
mu=H(**kw).fit(X(tr),tr.y)
mw=H(**kw).fit(X(tr),tr.y,sample_weight=tr.w)
logit=lambda p: np.log(np.clip(p,1e-9,1-1e-9)/(1-np.clip(p,1e-9,1-1e-9)))
su_va=logit(mu.predict_proba(X(va))[:,1]); su_bk=logit(mu.predict_proba(X(book))[:,1])
def platt(s,y,w=None):
    lr=LogisticRegression(C=1e6).fit(s[:,None],y,sample_weight=w); return lambda z: lr.predict_proba(z[:,None])[:,1]
pl=platt(su_va,va.y); plw=platt(su_va,va.y,va.w)
def corr(p,k): o=p/(1-p)*k; return o/(1+o)
truthF=lambda d: d.groupby("seg").apply(lambda g:(g.lam*g.e).sum()/g.e.sum())
def seg_err(p,name):
    mu_=-np.log(1-p); b=book.assign(mu=mu_)
    est=b.groupby("seg").apply(lambda g:g.mu.sum()/g.e.sum()); t=truthF(book)
    tot=b.mu.sum()/(book.lam*book.e).sum()-1
    print(f"{name:28s} overall {tot:+.3f} ", " ".join(f"{segs[i]}:{est[i]/t[i]-1:+.3f}" for i in range(6)))
p_pl=pl(su_bk)
seg_err(corr(p_pl,.10),"faulty odds*0.10")
seg_err(corr(p_pl,.25),"R1 latest 0.25")
eff=(tr.w[tr.y==0].count()/tr.w[tr.y==0].sum())
seg_err(corr(p_pl,eff),f"R2 eff {eff:.3f}")
seg_err(plw(su_bk),"R3 weighted Platt")
seg_err(mw.predict_proba(X(book))[:,1],"oracle weighted HGB")
