"""Forecast for spatial localisation: if the solver ran only on the hydraulically closed unit around each undecided
receptor (the smallest tree node that, in the fill model, neither spills out nor receives a spill), how many cells is that?"""
import sys, numpy as np
sys.path.insert(0, "fill"); from fillmodel import FillModel
t = np.load("shared/terrain_512.npz"); z, op = t["z"].astype(np.float64), t["open"]
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
M = FillModel(z, op, edge & op); R = np.load("shared/receptors.npz"); rc = R["rc"]; THR = 0.10
S = np.load("shared/storms_main.npz"); P = S["net_depth_mm"][:300].astype(np.float64) * 1e-3
LL, _ = M.run(P); D = M.depth_at(LL, rc); sub = M.last_sub
par = M.parent; sib = np.full(M.N, -1); sib[M.ca[M.nb:]] = M.cb[M.nb:]; sib[M.cb[M.nb:]] = M.ca[M.nb:]
ncell = np.zeros(M.N, np.int64); np.add.at(ncell, M.lab[op], 1)
for n in range(M.nb, M.N): ncell[n] = ncell[M.ca[n]] + ncell[M.cb[n]]
leaf = M.lab[rc[:, 0], rc[:, 1]]; A = op.sum()
def unit(l, s):
    n = l
    while n != M.root and (sub[n, s] or sub[sib[n], s]): n = par[n]
    return n
for band in (0.02, 0.05):
    und = (np.abs(D - THR) < band) & (D > 0)
    frac = []; per_pair = []
    for s in range(len(P)):
        nodes = {unit(leaf[r], s) for r in np.flatnonzero(und[s])}
        for n in nodes: per_pair.append(ncell[n] / A)
        # union of cells: nodes on the same root path nest, so keep the maximal ones
        keep = [n for n in nodes if not any((m != n) and (M.lo[m] <= M.lo[n]) and (M.hi[n] <= M.hi[m]) for m in nodes)]
        frac.append(sum(ncell[n] for n in keep) / A)
    frac = np.array(frac); per_pair = np.array(per_pair)
    print("band +-%.0f cm: storms with any undecided receptor %.3f" % (band * 100, und.any(1).mean()))
    print("   cells to simulate as share of open ground, per storm: mean %.3f median %.3f p90 %.3f max %.3f  -> cell-count saving %.1fx" % (frac.mean(), np.median(frac), np.percentile(frac, 90), frac.max(), 1 / frac.mean()))
    print("   closed-unit size per undecided receptor: median %.4f p90 %.3f; units that are the whole domain: %.3f" % (np.median(per_pair), np.percentile(per_pair, 90), (per_pair > 0.99).mean()))
