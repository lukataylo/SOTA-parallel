"""Bet 5: exact response curves of critical rainfall to patch height, -20..+20 cm, for every active (location, building) pair.
Pass line in docs/BETS.md: dead band + one-sided slope + saturation fits within 0.5 mm at all 41 heights for >= 80% of pairs."""
import sys, time, numpy as np
sys.path.insert(0, "fill"); from sweep import Sweep
d = np.load("results/air/decisive.npz"); c0, jobs, C = d["c0"], d["jobs"], d["crit_patch"]; cap = lambda x: np.minimum(np.where(np.isfinite(x), x, 130.5), 130.5)
act = (np.abs(cap(C) - cap(c0)[None]) >= 1.0) | (np.isfinite(C) != np.isfinite(c0)[None])
pairs = sorted({(int(jobs[j][0]), int(jobs[j][1]), int(r)) for j, r in zip(*np.nonzero(act))}); locs = sorted({p[:2] for p in pairs})
print("active (location, building) pairs: %d at %d locations" % (len(pairs), len(locs)), flush=True)
S = Sweep.from_files(); H = np.arange(-20, 21); t0 = time.time(); curves = {}
for k, (r, c) in enumerate(locs):
    curves[(r, c)] = np.array([cap(S.c0) if h == 0 else cap(S.patch(r, c, h / 100.0, 2)) for h in H])      # (41, receptors)
    if k % 20 == 19: print("  %d/%d locations, %.0fs" % (k + 1, len(locs), time.time() - t0), flush=True)
wall = time.time() - t0; nev = len(locs) * 40
print("%d exact evaluations in %.0f s (%.0f ms each)" % (nev, wall, 1e3 * wall / nev))
Y = np.array([curves[(r, c)][:, b] - curves[(r, c)][20, b] for r, c, b in pairs])                           # (pairs, 41) shift in mm
def fit_side(h, y):
    """h >= 0 (cm, ascending from 0), y shift. Best dead band a, slope m, saturation s: y = clip(m*(h-a), toward s)."""
    best = (np.inf, 0, 0, 0)
    for a in range(0, 21):
        hh = np.maximum(h - a, 0)
        for sidx in range(len(h)):                                            # saturation reached at h[sidx]
            s = y[sidx:].mean() if sidx < len(h) else y[-1]; span = hh[sidx] if sidx < len(h) else hh[-1]
            m = s / span if span > 0 else 0.0
            pred = np.where(np.arange(len(h)) >= sidx, s, m * hh); e = np.abs(pred - y).max()
            if e < best[0]: best = (e, a, m, s)
    return best
res = []
for y in Y:
    up = fit_side(H[20:], y[20:]); dn = fit_side(-H[20::-1], y[20::-1]); res.append((max(up[0], dn[0]), up[1], up[2], up[3], dn[1], dn[2], dn[3]))
res = np.array(res); ok = res[:, 0] <= 0.5 + 1e-9
print("THREE-NUMBER FIT within 0.5 mm at all 41 heights: %d of %d pairs = %.0f%% (pass line 80%%, kill below 60%%) -> %s" % (ok.sum(), len(res), 100 * ok.mean(), "PASS" if ok.mean() >= 0.8 else ("KILL" if ok.mean() < 0.6 else "BETWEEN")))
print("   max fit error mm: median %.2f, p90 %.2f, max %.1f; within 1 mm: %.0f%%; within 2 mm: %.0f%%" % (np.median(res[:, 0]), np.percentile(res[:, 0], 90), res[:, 0].max(), 100 * (res[:, 0] <= 1).mean(), 100 * (res[:, 0] <= 2).mean()))
one = ((np.abs(Y[:, 20:]).max(1) >= 1) ^ (np.abs(Y[:, :21]).max(1) >= 1))
mono = np.array([(np.all(np.diff(y) >= -1e-9) or np.all(np.diff(y) <= 1e-9)) for y in Y])
print("   shape of the curves: respond in one direction only: %d of %d; monotone across -20..+20 cm: %d; dead band >= 2 cm on the responding side: %d; saturate before 20 cm: %d" % (one.sum(), len(Y), mono.sum(), ((res[:, 1] >= 2) | (res[:, 4] >= 2)).sum(), ((np.abs(Y[:, -1] - Y[:, -6]) < 0.5) & (np.abs(Y[:, 0] - Y[:, 5]) < 0.5)).sum()))
print("   size of the largest shift over -20..+20 cm, mm: median %.1f, p90 %.1f; at +-5 cm: median %.1f" % (np.median(np.abs(Y).max(1)), np.percentile(np.abs(Y).max(1), 90), np.median(np.maximum(np.abs(Y[:, 25]), np.abs(Y[:, 15])))))
# tolerance map: for each location, the smallest |height change| (cm) that moves any building's critical rain by >= 1 mm
tol = {loc: next((abs(h) for h in sorted(H, key=abs) if h != 0 and (np.abs(curves[loc][h + 20] - curves[loc][20]) >= 1.0).any()), np.inf) for loc in locs}
tv = np.array(list(tol.values()))
print("TOLERANCE at the %d active locations: smallest change that moves some building by 1 mm of rain: 1 cm at %d, 2 cm at %d, 3-5 cm at %d, 6-20 cm at %d" % (len(tv), (tv == 1).sum(), (tv == 2).sum(), ((tv >= 3) & (tv <= 5)).sum(), ((tv >= 6) & (tv <= 20)).sum()))
np.savez_compressed("results/air/bet5_curves.npz", H=H, pairs=np.array(pairs), Y=Y, fit=res, locs=np.array(locs), tol=tv, wall_s=wall)
