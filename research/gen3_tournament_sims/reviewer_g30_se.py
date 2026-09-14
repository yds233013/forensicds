import numpy as np
rng = np.random.default_rng(1)
N_ELIG = 1_585_000
TARGET_TOTAL = 220 * N_ELIG / 1000   # $220 per 1000 -> total $ difference
# D2 = fz4 declines, fz5 approves (only IPW-estimated part of the difference).
# Design rates after 02-16: band [thr,.75): 6%/3%; [.75,.90): 2%/1%; >=.90: .5%/.25% (<=500 / >500)
def run(N, fraud_share, band_mix, amt_fraud=(300,1500), amt_legit_mean=110, reps=3000):
    band = rng.choice(3, N, p=band_mix)
    fraud = rng.random(N) < fraud_share
    amt = np.where(fraud, rng.uniform(*amt_fraud, N), rng.lognormal(np.log(amt_legit_mean)-0.5, 1.0, N))
    lost = fraud & (rng.random(N) < 0.9*0.9)          # disputed & not reversed (approx)
    approve_cost = np.where(lost, amt + 25, np.where(fraud & (rng.random(N)<0.1), 25, 0))
    decline_cost = np.where(lost, 0, 0.11*amt)
    y = approve_cost - decline_cost
    hi = amt > 500
    rate = np.array([[0.06,0.03],[0.02,0.01],[0.005,0.0025]])[band, hi.astype(int)]
    truth = y.sum()
    ests = np.empty(reps)
    for r in range(reps):
        s = rng.random(N) < rate
        ests[r] = (y[s]/rate[s]).sum()
    return truth, ests.std(), (rate*lost).sum()
for N, q, mix in [(3000, 0.14, [0.5,0.4,0.1]), (6000, 0.07, [0.5,0.4,0.1]), (1500, 0.28, [0.5,0.4,0.1]),
                  (3000, 0.14, [0.8,0.2,0.0]), (20000, 0.025, [0.6,0.35,0.05])]:
    truth, sd, exp_sampled_losses = run(N, q, mix)
    print(f"N_D2={N:6d} fraud={q:.3f} bands={mix}: truth=${truth/N_ELIG*1000:6.0f}/1000  SE=${sd/N_ELIG*1000:5.0f}/1000  "
          f"expected sampled fraud-loss rows={exp_sampled_losses:5.1f}")
