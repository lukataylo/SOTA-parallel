"""Fresh intervention cases, remote patches only (>= 8 m from the building), with storms placed using the
transit-corrected prediction of the solver's peak, not the fill model's critical depth.
Prediction for the changed terrain: emulator peak on the unchanged terrain + (fill depth changed - fill depth unchanged) at the same rain.
None of the earlier 20 (patch, receptor) pairs is reused. Predictions are written before the solver runs."""
import sys, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10; LOSS = 12.0; DUR = 40
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
PG = np.linspace(0, 0.14, 281)
def fd(z): M = FillModel(z, op, outlet); LL, _ = M.run(PG); return M.depth_at(LL, rc)
FD = fd(z0)
S = np.load("shared/storms_pilot.npz"); ts = np.load("results/pro/pilot_timeseries.npz"); tt = ts["t_s"].astype(np.float64); NT = len(tt); DTs = 30.0; TAUS = [60, 300, 900, 2400.0]
def drivers(profile, loss):
    rate = np.maximum(profile - loss, 0) / 3.6e6
    r = np.where(tt < 3600.0, rate[np.minimum((np.maximum(tt - 1e-6, 0) // 60).astype(int), 59)], 0.0); V = np.cumsum(r) * DTs; Q = []
    for tau in TAUS:
        a = np.exp(-DTs / tau); q = 0.0; o = np.zeros(NT)
        for n in range(NT): q = a * q + (1 - a) * r[n]; o[n] = q
        Q.append(o * 3.6e6)
    return V, np.array(Q)
def feats(V, Q, r, ok): return np.c_[V[ok] * 1e3, np.interp(V[ok], PG, FD[:, r]) * 100, Q[:, ok].T]
idx = ts["storm_index"]; dep = ts["depth"].astype(np.float64); tend = ts["t_end_s"]
def model_for(r):                                   # trained on all 16 time-series storms
    X, y = [], []
    for j in range(len(idx)):
        V, Q = drivers(S["profile"][idx[j]], S["loss_mm_h"][idx[j]]); ok = np.isfinite(dep[j, :, r]) & (tt <= tend[j])
        X.append(feats(V, Q, r, ok)); y.append(dep[j, ok, r] - np.interp(V[ok], PG, FD[:, r]))
    return HistGradientBoostingRegressor(max_iter=120, max_depth=3, learning_rate=0.1, min_samples_leaf=10).fit(np.concatenate(X), np.concatenate(y))
def profile_for_gross(depth_mm):
    m = DUR; t = (np.arange(m) + 0.5) / m; w = np.where(t <= 0.5, t / 0.5, (1 - t) / 0.5); w /= w.sum(); p = np.zeros(60); p[:m] = w * depth_mm * 60.0; return p
GROSS = np.linspace(8, 150, 143); PROF = np.array([profile_for_gross(g) for g in GROSS]); NET = np.maximum(PROF - LOSS, 0).sum(1) / 60.0
d = np.load("results/air/decisive.npz"); c0, jobs, C = d["c0"], d["jobs"], d["crit_patch"]; cap = lambda x: np.where(np.isfinite(x), x, 200.0)
old = np.load("shared/interventions.npz"); used = {(int(r), tuple(rect)) for r, rect in zip(old["receptor"], old["rect"].tolist())}
shift = cap(C) - cap(c0)[None]; cands = []
for j in range(len(jobs)):
    rr, cc, dz, rad = jobs[j]; rect = (int(max(rr - 2, 0)), int(rr + 3), int(max(cc - 2, 0)), int(cc + 3))
    for r in np.flatnonzero(np.abs(shift[j]) >= 3.0):
        dist = np.hypot(rc[r, 0] - rr, rc[r, 1] - cc)
        if dist >= 8 and (int(r), rect) not in used: cands.append((abs(shift[j, r]), j, int(r), rect, dist))
cands.sort(reverse=True); print("remote candidates:", len(cands))
models = {}; out = []; per_r = {}; seenj = set()
for s, j, r, rect, dist in cands:
    if per_r.get(r, 0) >= 3 or j in seenj or len(out) >= 24: continue
    if r not in models: models[r] = model_for(r)
    zc = z0.copy(); sl = (slice(rect[0], rect[1]), slice(rect[2], rect[3])); zc[sl] = np.where(op[sl], zc[sl] + jobs[j][2], zc[sl]); FDc = fd(zc)[:, r]
    base = np.zeros(len(GROSS)); chg = np.zeros(len(GROSS))
    for g in range(len(GROSS)):
        V, Q = drivers(PROF[g], LOSS); ok = tt <= DUR * 60 + 1200.0
        b = np.maximum(np.interp(V[ok], PG, FD[:, r]) + models[r].predict(feats(V, Q, r, ok)), 0)
        base[g] = b.max(); chg[g] = np.maximum(b + np.interp(V[ok], PG, FDc) - np.interp(V[ok], PG, FD[:, r]), 0).max()
    lo, hi = np.minimum(base, chg), np.maximum(base, chg)
    strad = (lo < THR) & (hi >= THR)
    if not strad.any(): continue
    margin = np.where(strad, np.minimum(THR - lo, hi - THR), -1); g = int(margin.argmax())
    if margin[g] < 0.012: continue                                  # want at least 1.2 cm predicted clearance on both sides
    out.append(dict(receptor=r, rect=rect, dz=jobs[j][2], profile=PROF[g].astype(np.float32), net_mm=NET[g], dist=dist, pred_base=base[g], pred_changed=chg[g])); per_r[r] = per_r.get(r, 0) + 1; seenj.add(j)
    print("%2d receptor %3d | patch %s %+.0f cm, %.0f m away | storm net %.1f mm | predicted peak %.3f -> %.3f m (%s -> %s)" % (len(out) - 1, r, rect, jobs[j][2] * 100, dist, NET[g], base[g], chg[g], "wet" if base[g] >= THR else "dry", "wet" if chg[g] >= THR else "dry"), flush=True)
n = len(out)
np.savez("shared/interventions_retest.npz", receptor=np.array([o["receptor"] for o in out]), rect=np.array([o["rect"] for o in out]), dz=np.array([o["dz"] for o in out]),
         profile=np.array([o["profile"] for o in out]), net_mm=np.array([o["net_mm"] for o in out]), distance_m=np.array([o["dist"] for o in out]),
         pred_peak_base_m=np.array([o["pred_base"] for o in out]), pred_peak_changed_m=np.array([o["pred_changed"] for o in out]),
         loss_mm_h=np.full(n, LOSS, np.float32), duration_s=np.full(n, DUR * 60.0, np.float32), t_end_s=np.full(n, DUR * 60.0 + 1200.0, np.float32), profile_dt_s=np.float32(60.0), threshold_m=np.float32(THR))
print("cases written:", n, "distinct receptors:", len(per_r))
