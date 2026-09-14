import numpy as np
from g21 import km
rng=np.random.default_rng(5)
n=400000
for S180 in (0.487,0.539):
  lam=-np.log(S180)/180
  t0=rng.uniform(0,304,n); fu=304-t0
  T=rng.exponential(1/lam,n)
  # oracle design rule: churned (confirmed) if T<=fu-30 -> event at T; unresolved if fu-30<T<=fu -> censor at T; ongoing -> censor at fu
  E1=(T<=fu-30).astype(int); C1=np.where(T<=fu,T,fu); C1=np.where(E1==1,T,C1)
  # admin: censor at fu-30 for all
  fu2=np.maximum(fu-30,0); E2=(T<=fu2).astype(int); C2=np.minimum(T,fu2)
  # unresolved as churned
  E3=(T<=fu).astype(int); C3=np.minimum(T,fu)
  w=np.ones(n)
  for h in (90,180):
    print(S180,h,'truth',round(np.exp(-lam*h),4),'censor_unresolved_at_end',round(km(C1,E1,w,h),4),'admin_asof-30',round(km(C2,E2,w,h),4),'unresolved_as_churn(no returns)',round(km(C3,E3,w,h),4))
