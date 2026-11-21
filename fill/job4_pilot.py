"""Job 4: score the fill model against the solver pilot, and test whether a few solver runs predict the rest.
Run when results/pro/bruteforce_pilot.npz exists:  uv run --with numpy --with scikit-learn python fill/job4_pilot.py
"""
import numpy as np
b = np.load("results/pro/bruteforce_pilot.npz", allow_pickle=True)
idx = b["storm_index"] if "storm_index" in b.files else np.arange(b["peak_depth"].shape[0])
pk = b["peak_depth"].astype(np.float64); fin = b["final_depth"].astype(np.float64) if "final_depth" in b.files else None
S = np.load("shared/storms_pilot.npz"); THR = 0.10
F = np.load("results/air/fill_pilot.npz")["fill_depth"].astype(np.float64)[idx]
net = S["net_depth_mm"][idx].astype(np.float64); dur = S["duration_s"][idx] / 60.0; kind = S["kind"][idx]; peak_rate = S["profile"][idx].max(1)
sw, fw = pk >= THR, F >= THR
print("PILOT: %d storms x %d receptors" % pk.shape)
print("fill vs solver peak: agreement %.3f | solver wet %d | misses (solver wet, fill dry) %d | false alarms %d" % ((sw == fw).mean(), sw.sum(), (sw & ~fw).sum(), (~sw & fw).sum()))
if fin is not None:
    sf = fin >= THR
    print("fill vs solver FINAL depth: agreement %.3f | misses %d | false alarms %d | solver final minus fill cm p10 %.1f median %.1f p90 %.1f" % ((sf == fw).mean(), (sf & ~fw).sum(), (~sf & fw).sum(), *(np.percentile(fin - F, [10, 50, 90]) * 100)))
d = pk - F
print("solver peak minus fill, cm: p10 %.1f median %.1f p90 %.1f p99 %.1f max %.1f" % tuple(np.r_[np.percentile(d, [10, 50, 90, 99]), d.max()] * 100))
dry = F == 0
print("zero-fill pairs %d; solver flooded %d of them; receptors with zero fill in every storm that the solver flooded at least once: %d" % (dry.sum(), (sw & dry).sum(), (dry.all(0) & sw.any(0)).sum()))
miss, fa = sw & ~fw, ~sw & fw
lo = (THR - F[miss]).max() if miss.any() else 0.0; hi = (F[fa] - THR).max() if fa.any() else 0.0
und = (F > THR - lo - 1e-9) & (F < THR + hi + 1e-9)
print("fill-depth band that catches every error: %.1f cm below to %.1f cm above -> undecided pairs %.3f, storms fully decided %.3f, site alone decided %.3f" % (lo * 100, hi * 100, und.mean(), (~und.any(1)).mean(), (~und[:, -1]).mean()))
# is the solver's answer monotone in net rain, per receptor?
o = np.argsort(net); swo = sw[o]
viol = ((swo[:-1] & ~swo[1:]).sum(0))          # wet storm followed (in net-depth order) by a dry one
print("receptors whose solver decision is not monotone in net depth: %d of %d (total reversals %d)" % ((viol > 0).sum(), pk.shape[1], viol.sum()))

# --- can a few solver runs predict the rest? per-receptor regression on storm parameters, leave-out test
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
X = np.c_[net, peak_rate, dur, kind]
rng = np.random.default_rng(0)
def trial(ntrain, model, reps=5):
    acc = []; errs = []
    for _ in range(reps):
        p = rng.permutation(len(net)); tr, te = p[:ntrain], p[ntrain:]
        pred = np.zeros((len(te), pk.shape[1]))
        for r in range(pk.shape[1]):
            if pk[tr, r].max() < 0.02: continue                       # never wet in training: predict dry
            m = model(); m.fit(X[tr], pk[tr, r]); pred[:, r] = m.predict(X[te])
        acc.append(((pred >= THR) == sw[te]).mean()); errs.append(np.abs(pred - pk[te]))
    e = np.concatenate([x.ravel() for x in errs])
    return np.mean(acc), np.percentile(e, 50) * 100, np.percentile(e, 99) * 100
base = max(sw.mean(), 1 - sw.mean())
print("predicting unseen storms from n simulated ones (decision agreement; abs error cm median, p99). Always-dry baseline %.3f; fill model %.3f" % (base, (sw == fw).mean()))
for n in (8, 16, 32, 48):
    if n >= len(net) - 4: continue
    a = trial(n, lambda: GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.08, monotonic_cst=[1, 1, 0, 0]))
    k = trial(n, lambda: KNeighborsRegressor(n_neighbors=min(3, n), weights="distance"))
    # physics-informed: regress on fill depth as an extra feature is not possible per receptor without it; add it
    print("  n=%2d: boosted trees %.3f (%.1f, %.1f) | nearest neighbours %.3f (%.1f, %.1f)" % (n, *a, *k))
