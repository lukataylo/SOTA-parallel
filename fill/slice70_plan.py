"""Attribute the packed 70 mm slice as the 35 mm map was (nearest block within 75 m, more than 7.5 m away) and list its movers for single runs."""
import numpy as np
rc = np.load("shared/receptors.npz")["rc"]; op = np.load("shared/terrain_512.npz")["open"]; P = 30; cs = [int(c) for c in np.random.default_rng(2026).permutation(P * P)][:80]
base = np.load("results/air/final/slice70/base.npz")["peak"].astype(float); mv = []; moved = un = nw = 0
for t in range(160):
    k, c = divmod(t, 80); c = cs[c]; d = np.load("results/air/final/slice70/r%03d.npz" % t)["peak"].astype(float) - base
    B = [(i, j) for i in range(c // P or P, 101, P) for j in range(c % P or P, 101, P) if op[5 * i:5 * i + 5, 5 * j:5 * j + 5].any()]; nw += len(B)
    cen = np.array([(5 * i + 2, 5 * j + 2) for i, j in B], float); D = np.hypot(cen[:, None, 0] - rc[None, :, 0], cen[:, None, 1] - rc[None, :, 1]); near = D.argmin(0); dn = D.min(0); best = {}
    for q in np.flatnonzero(np.abs(d) >= 0.01):
        moved += 1
        if dn[q] > 75: un += 1; continue
        if dn[q] > 7.5 and abs(d[q]) > abs(best.get(near[q], (0, 0))[0]): best[near[q]] = (d[q], q)
    mv += [(k, B[n][0], B[n][1], int(q), float(e)) for n, (e, q) in best.items()]
mv.sort(key=lambda m: -abs(m[4])); print("70 mm slice: %d what-ifs in 160 runs; movers %d; moved receptors %d, unattributed %d" % (nw, len(mv), moved, un))
np.savez("shared/slice70_plan.npz", blocks=np.array([m[:3] for m in mv[:40]]).reshape(-1, 3), receptor=np.array([m[3] for m in mv]), effect=np.array([m[4] for m in mv]), all_blocks=np.array([m[:3] for m in mv]).reshape(-1, 3), whatifs=nw, moved=moved, unattributed=un)
