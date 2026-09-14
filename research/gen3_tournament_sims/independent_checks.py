import numpy as np
rng=np.random.default_rng(7)
# G21: constant hazard with S(180)=0.487; follow-up F~U(0,304); churn is confirmed only 30d after it happens
lam=-np.log(0.487)/180; n=400000
t=rng.exponential(1/lam,n); F=rng.uniform(0,304,n)
def km(time,event,at):
    o=np.argsort(time); time=time[o]; event=event[o]
    s=1.0; N=len(time); i=0
    ut,idx=np.unique(time,return_index=True)
    # vectorized-ish KM
    ev_times=np.unique(time[event==1]); ev_times=ev_times[ev_times<=at]
    at_risk=N-np.searchsorted(time,ev_times,side='left')
    d=np.array([0]*len(ev_times))
    cnt=np.bincount(np.searchsorted(ev_times,time[event==1][time[event==1]<=at]),minlength=len(ev_times))
    return np.prod(1-cnt/at_risk)
# rule A: censor unresolved at spell_end F (events with t in (F-30,F] lost)
evA=(t<=F-30); timeA=np.where(evA,t,F)
# rule B: administrative censoring at F-30
Fb=np.maximum(F-30,0); evB=(t<=Fb); timeB=np.where(evB,t,Fb)
for name,(tm,ev) in {"censor_at_spell_end":(timeA,evA.astype(int)),"censor_at_asof_minus_30":(timeB,evB.astype(int))}.items():
    print("G21",name,"S90=%.3f S180=%.3f"%(km(tm,ev,90),km(tm,ev,180)),"truth S90=%.3f S180=0.487"%np.exp(-lam*90))
# G10: profile-scaling estimator I/T on sell-out days; analytic E=I/(I-1) for Gamma(I) sellout time
for I in (4,8,15):
    lamd=I*1.3
    T=rng.gamma(I,1/lamd,200000); m=T<1
    est=I/T[m]
    print("G10 I=%d  mean(est)/lambda on sellout days = %.3f  (I/(I-1)=%.3f)"%(I,est.mean()/lamd,I/(I-1)))
# G26 arithmetic
print("G26 blended activation %.4f"%((5260*0.415+3020*0.23)/8280), "surge rate needed for 40.3%%: %.3f"%((0.403*8280-5260*0.415)/3020))
