import time, sys, numpy as np
sys.path.insert(0, "fill"); from fillmodel import FillModel
t = np.load("shared/terrain_512.npz"); z, op = t["z"], t["open"]
outlet = np.zeros_like(op); outlet[0] = op[0]; outlet[-1] = op[-1]; outlet[:, 0] = op[:, 0]; outlet[:, -1] = op[:, -1]
t0 = time.time(); M = FillModel(z, op, outlet); tb = time.time() - t0
print("build s %.1f  leaves %d  open cells %d  outlet-basin area %d  finite-cap nodes %d" % (tb, M.nb, op.sum(), M.area[0], np.isfinite(M.cap).sum()))
P = np.linspace(0, 0.12, 121)
t0 = time.time(); LL, out = M.run(P); tr = time.time() - t0
print("run s %.2f for %d storms" % (tr, len(P)))
A = op.sum()
for s in (5, 20, 60, 120):
    d = M.depth_field(LL, s); stored = d.sum()
    print("P %5.1f mm: rain %9.1f m3 stored %9.1f out %9.1f imbalance %.2e  wet>10cm cells %d max depth %.2f" % (P[s]*1e3, P[s]*A, stored, out[s], (P[s]*A - stored - out[s]) / max(P[s]*A, 1e-9), (d > 0.1).sum(), d.max()))
R = np.load("shared/receptors.npz"); D = M.depth_at(LL, R["rc"])
print("monotone in P:", bool((np.diff(D, axis=0) >= -1e-6).all()), " min diff %.2e" % np.diff(D, axis=0).min())
fl = D >= 0.10; crit = np.where(fl.any(0), P[np.argmax(fl, 0)] * 1e3, np.inf)
print("receptors that flood at some P<=120mm: %d of %d" % (np.isfinite(crit).sum(), len(crit)))
print("critical net depth mm quantiles (finite):", np.round(np.percentile(crit[np.isfinite(crit)], [0, 10, 25, 50, 75, 90, 100]), 1))
print("site crit:", crit[-1], "site depth at 120mm %.3f" % D[-1, -1], "receptors in outlet basin:", int((M.lab[R['rc'][:,0], R['rc'][:,1]] == 0).sum()))
np.savez("results/air/fill_curve.npz", P=P, D=D, crit=crit)
