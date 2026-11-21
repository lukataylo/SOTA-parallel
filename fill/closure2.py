"""Flexible transit closure: per receptor, a small boosted model of overshoot = solver depth - fill(V(t)) on (V, fill depth, lagged net rain rates).
Same split as closure.py: fit on 12 time-series storms, test on 4 held out and on 48 pilot storms never seen."""
import sys, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
PG = np.linspace(0, 0.14, 281); M = FillModel(z, op, edge & op); LL, _ = M.run(PG); FD = M.depth_at(LL, rc)
S = np.load("shared/storms_pilot.npz"); ts = np.load("results/pro/pilot_timeseries.npz"); bf = np.load("results/pro/bruteforce_pilot.npz")
tt = ts["t_s"].astype(np.float64); NT = len(tt); DT = 30.0; TAUS = [60, 300, 900, 2400.0]
def drivers(i):
    rate = np.maximum(S["profile"][i] - S["loss_mm_h"][i], 0) / 3.6e6
    r = np.where(tt < 3600.0, rate[np.minimum((np.maximum(tt - 1e-6, 0) // 60).astype(int), 59)], 0.0); V = np.cumsum(r) * DT; Q = []
    for tau in TAUS:
        a = np.exp(-DT / tau); q = 0.0; o = np.zeros(NT)
        for n in range(NT): q = a * q + (1 - a) * r[n]; o[n] = q
        Q.append(o * 3.6e6)
    return V, np.array(Q)
drv = {i: drivers(i) for i in range(len(S["depth_mm"]))}
idx = ts["storm_index"]; dep = ts["depth"].astype(np.float64); tend = ts["t_end_s"]
perm = np.random.default_rng(1).permutation(len(idx)); tr, te = perm[:12], perm[12:]
def feats(i, r, ok):
    V, Q = drv[int(i)]; return np.c_[V[ok] * 1e3, np.interp(V[ok], PG, FD[:, r]) * 100, Q[:, ok].T]
models = {}
risk = np.flatnonzero((dep[tr].reshape(-1, dep.shape[2]).__ge__(0.03) & np.isfinite(dep[tr].reshape(-1, dep.shape[2]))).any(0) | (FD >= 0.03).any(0))
for r in risk:
    X, y = [], []
    for j in tr:
        ok = np.isfinite(dep[j, :, r]) & (tt <= tend[j]); V = drv[int(idx[j])][0]
        X.append(feats(idx[j], r, ok)); y.append(dep[j, ok, r] - np.interp(V[ok], PG, FD[:, r]))
    models[r] = HistGradientBoostingRegressor(max_iter=120, max_depth=3, learning_rate=0.1, min_samples_leaf=10).fit(np.concatenate(X), np.concatenate(y))
def predict_peak(i):
    V, _ = drv[int(i)]; ok = tt <= S["duration_s"][i] + 1200.0; base = np.stack([np.interp(V[ok], PG, FD[:, r]) for r in range(FD.shape[1])], 1)
    for r in risk: base[:, r] = np.maximum(base[:, r] + models[r].predict(feats(i, r, ok)), 0)
    return base.max(0)
def score(name, storms, peaks):
    P = np.stack([predict_peak(i) for i in storms]); sw = peaks >= THR; ever = sw.any(0) | (P >= THR).any(0); e = np.abs(P - peaks)[:, ever]
    nearthr = np.abs(peaks - THR) < 0.02
    print("  %-22s agreement %.4f | misses %4d | false alarms %4d | of %d wet | abs peak error cm at-risk: median %.2f p90 %.2f p99 %.1f | errors that are within 2 cm of the threshold in the solver: %d of %d" % (
        name, ((P >= THR) == sw).mean(), (sw & (P < THR)).sum(), (~sw & (P >= THR)).sum(), sw.sum(), np.median(e) * 100, np.percentile(e, 90) * 100, np.percentile(e, 99) * 100, (((P >= THR) != sw) & nearthr).sum(), ((P >= THR) != sw).sum()))
    return P
print("receptors modelled:", len(risk))
score("train (12)", idx[tr], ts["peak_depth"][tr].astype(np.float64)); score("held out (4)", idx[te], ts["peak_depth"][te].astype(np.float64))
rest = np.array([i for i in bf["storm_index"] if i not in set(idx.tolist())]); pk = bf["peak_depth"].astype(np.float64)[np.searchsorted(bf["storm_index"], rest)]
P = score("48 unseen pilot storms", rest, pk)
np.savez("results/air/closure2_pred.npz", storms=rest, pred=P, solver=pk)
