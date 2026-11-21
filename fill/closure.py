"""Transit closure: depth(t) at a receptor = exact fill depth at cumulative net rain V(t) + a * q(t)^0.6,
where q is the net rain rate passed through a one-parameter lag. Exponent 0.6 is Manning sheet flow (depth ~ discharge^(3/5)).
Two numbers per receptor (a, lag). Fit on 12 of the 16 time-series storms; test on the other 4 and on the 48 pilot storms never used."""
import sys, numpy as np
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
PG = np.linspace(0, 0.14, 281); M = FillModel(z, op, edge & op); LL, _ = M.run(PG); FD = M.depth_at(LL, rc)        # (P, receptors)
S = np.load("shared/storms_pilot.npz"); ts = np.load("results/pro/pilot_timeseries.npz"); bf = np.load("results/pro/bruteforce_pilot.npz")
_ts = np.load("results/pro/pilot_timeseries.npz"); tt = _ts["t_s"].astype(np.float64); NT = len(tt); DT = 30.0; TAUS = np.array([60, 150, 300, 600, 1200, 2400.0]); B = 0.6
def drivers(i):
    rate = np.maximum(S["profile"][i] - S["loss_mm_h"][i], 0) / 3.6e6            # m/s, per 60 s
    r = np.where(tt < 3600.0, rate[np.minimum((np.maximum(tt - 1e-6, 0) // 60).astype(int), 59)], 0.0)   # rate over the 30 s before each sample
    V = np.cumsum(r) * DT
    Q = np.zeros((len(TAUS), NT))
    for k, tau in enumerate(TAUS):
        a = np.exp(-DT / tau); q = 0.0
        for n in range(NT): q = a * q + (1 - a) * r[n]; Q[k, n] = q
    return V, Q
def fill_at(V): return np.stack([np.interp(V, PG, FD[:, r]) for r in range(FD.shape[1])], 1)      # (NT, receptors)
idx = ts["storm_index"]; dep = ts["depth"].astype(np.float64); tend = ts["t_end_s"]
rng = np.random.default_rng(1); perm = rng.permutation(len(idx)); tr, te = perm[:12], perm[12:]
drv = {int(i): drivers(int(i)) for i in range(len(S["depth_mm"]))}
nr = FD.shape[1]; A = np.zeros(nr); K = np.zeros(nr, int)
for r in range(nr):
    best = (np.inf, 0.0, 0)
    for k in range(len(TAUS)):
        xs, ys = [], []
        for j in tr:
            V, Q = drv[int(idx[j])]; ok = np.isfinite(dep[j, :, r]) & (tt <= tend[j])
            xs.append(Q[k][ok] ** B); ys.append(dep[j, ok, r] - np.interp(V[ok], PG, FD[:, r]))
        x, y = np.concatenate(xs), np.concatenate(ys); a = max(float(x @ y / max(x @ x, 1e-30)), 0.0); e = ((y - a * x) ** 2).sum()
        if e < best[0]: best = (e, a, k)
    A[r], K[r] = best[1], best[2]
def predict_peak(i, tmax):
    V, Q = drv[int(i)]; ok = tt <= tmax
    return (fill_at(V[ok]) + A[None] * (Q[K][:, ok].T ** B)).max(0)
def score(name, storms, peaks):
    pred = np.stack([predict_peak(i, S["duration_s"][i] + 1200.0) for i in storms]); fillonly = np.stack([fill_at(np.array([S["net_depth_mm"][i] * 1e-3]))[0] for i in storms])
    sw = peaks >= THR; ever = sw.any(0) | (pred >= THR).any(0)
    for nm, P in (("fill only", fillonly), ("fill + transit", pred)):
        e = np.abs(P - peaks)[:, ever]
        print("  %-15s %s: agreement %.4f | misses %4d | false alarms %4d | of %d wet | abs peak error cm on at-risk receptors: median %.2f p90 %.2f p99 %.1f" % (
            nm, name, ((P >= THR) == sw).mean(), (sw & (P < THR)).sum(), (~sw & (P >= THR)).sum(), sw.sum(), np.median(e) * 100, np.percentile(e, 90) * 100, np.percentile(e, 99) * 100))
print("fitted transit coefficient a: nonzero for %d of %d receptors; lag choices (s) used: %s" % ((A > 0).sum(), nr, dict(zip(*np.unique(TAUS[K[A > 0]], return_counts=True)))))
score("train (12 storms)", idx[tr], ts["peak_depth"][tr].astype(np.float64))
score("held out (4 storms)", idx[te], ts["peak_depth"][te].astype(np.float64))
rest = np.array([i for i in bf["storm_index"] if i not in set(idx.tolist())])
pk = bf["peak_depth"].astype(np.float64)[np.searchsorted(bf["storm_index"], rest)]
score("48 unseen pilot storms", rest, pk)
np.savez("results/air/closure.npz", a=A, tau_s=TAUS[K], exponent=B, train=idx[tr], test=idx[te])
