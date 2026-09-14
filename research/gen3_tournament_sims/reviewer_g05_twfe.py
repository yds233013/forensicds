import numpy as np, reviewer_g05_sim as G
def twfe(d):
    S=d['S']; T=G.T; y=d['y']
    sid=np.repeat(np.arange(S),T); tt=np.tile(np.arange(T),S)
    D=(tt+1>=d['planned'][sid]).astype(float); Y=y.ravel().copy()
    def dm(v):
        v=v.copy()
        for _ in range(200):
            v-=(np.bincount(sid,v,S)/T)[sid]; v-=(np.bincount(tt,v,T)/S)[tt]
        return v
    Dt=dm(D); return (Dt@dm(Y))/(Dt@Dt)
orig=G.gen
for scale, mult in [(16,1.0),(40,2.0),(80,3.5),(200,8.0)]:
    def gen2(seed, **kw):
        d=orig(seed, **kw)
        # rebuild tau with slower ramp, same m_s proxy: rescale existing tau
        rng=np.random.default_rng(seed+99)
        t=np.arange(1,G.T+1); e=t[None,:]-d['actual'][:,None]
        A=np.array([G.WAVES[w][2] if w>=0 else 0 for w in d['wave']])
        with np.errstate(over='ignore', invalid='ignore'):
            new=np.where(e>=0, mult*A[:,None]*(1-np.exp(-(np.maximum(e,0)+1)/scale)),0.0)
        d['y']=d['y']-d['tau']+new; d['tau']=new; return d
    d=gen2(0)
    sid=np.repeat(np.arange(d['S']),G.T); tt=np.tile(np.arange(G.T),d['S'])
    e=(tt+1)-d['actual'][sid]; m=(e>=0)&(e<=25)&(~d['noncomp'].ravel())&(d['wave'][sid]>=0)
    print(f"ramp scale {scale:3d}, A x{mult}: truth(0-25)={d['tau'].ravel()[m].mean():.4f}  max tau={d['tau'].max():.3f}  static TWFE={twfe(d):+.4f}")
