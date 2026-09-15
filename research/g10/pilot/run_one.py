import copy, sys, time
import numpy as np
import g10_world as G
import pilot_estimators as P
spec = copy.deepcopy(G.VISIBLE_SPEC)
if len(sys.argv) > 1: spec["seed"] = int(sys.argv[1])
t = time.time(); w = G.generate(spec); X = P.arrays(w); print("gen+arrays", round(time.time()-t,1))
t = time.time(); ests, info = P.run_all(X); print("estimators", round(time.time()-t,1), "alpha_c1", np.round(info["alpha_c1"][[np.where(X["A"]["cat"]==c)[0][0] for c in range(8)]],2))
T = P.truth(X)
keys = list(T)
print(f"{'metric':42}{'truth':>10}", *[f"{k[:10]:>11}" for k in ests])
for k in keys:
    row = [P.graded(X, ests[m])[k] for m in ests] if False else None
G_all = {m: P.graded(X, e) for m, e in ests.items()}
for k in keys:
    tv = T[k]
    cells = []
    for m in ests:
        v = G_all[m][k]
        cells.append(f"{v - tv:+10.2f}" if (k.startswith("cat") or k.startswith("bias")) else f"{100*(v/tv-1):+9.1f}%")
    print(f"{k[:42]:42}{tv:10.2f}", *cells)
