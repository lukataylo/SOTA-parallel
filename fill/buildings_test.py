"""Sensitivity: buildings as floodable footprints raised 0.3 m (the national map's choice), with rain falling on them,
in place of solid walls with roof rain discarded. Does the ground that controls each building change?
Gate committed in docs/mythos/6_decisions_after_research.md: if more than 20% of at-risk buildings change their controlling ground, test it in the solver too.
Each footprint is set to the median height of the open ground touching it, plus 0.3 m (the bare-earth map has pits under buildings)."""
import sys, time, numpy as np
from scipy.ndimage import label, binary_dilation
sys.path.insert(0, "fill"); from sweep import Sweep
T = np.load("shared/terrain_512.npz"); dtm, op = T["dtm"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]
lab, nb = label(~op); z = dtm.copy(); ring = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
for b in range(1, nb + 1):
    m = lab == b; edge = binary_dilation(m, ring) & op
    z[m] = (np.median(dtm[edge]) if edge.any() else np.median(dtm[m])) + 0.3
cap = lambda x: np.minimum(np.where(np.isfinite(x), x, 130.5), 130.5)
A = Sweep.from_files(); B = Sweep(z.astype(np.float32), np.ones_like(op), rc)
ca, cb = A.c0, B.c0; fa, fb = np.isfinite(ca), np.isfinite(cb)
print("at-risk buildings: walls %d, floodable footprints %d, both %d; newly at risk %d; no longer at risk %d" % (fa.sum(), fb.sum(), (fa & fb).sum(), (~fa & fb).sum(), (fa & ~fb).sum()))
d = (cb - ca)[fa & fb]; print("critical rain where both exist, footprints minus walls, mm: median %.1f, p10 %.1f, p90 %.1f; rank correlation %.2f" % (np.median(d), np.percentile(d, 10), np.percentile(d, 90), np.corrcoef(np.argsort(np.argsort(ca[fa & fb])), np.argsort(np.argsort(cb[fa & fb])))[0, 1]))
b5 = np.load("results/air/bet5_curves.npz"); locs = [tuple(x) for x in b5["locs"]]; t0 = time.time()
def active(S):
    out = {}
    for (r, c) in locs:
        m = np.zeros(len(rc), bool)
        for dz in (0.05, -0.05): m |= np.abs(cap(S.patch(int(r), int(c), dz, 2)) - cap(S.c0)) >= 1.0
        out[(r, c)] = m
    return out
aa, ab = active(A), active(B); print("patch tests at %d locations under both, %.0f s" % (len(locs), time.time() - t0))
ctrlA = {b: {l for l in locs if aa[l][b]} for b in np.flatnonzero(fa)}; ctrlB = {b: {l for l in locs if ab[l][b]} for b in np.flatnonzero(fa)}
have = [b for b in ctrlA if ctrlA[b]]
same = sum(1 for b in have if ctrlA[b] == ctrlB[b]); overlap = sum(1 for b in have if ctrlA[b] & ctrlB[b]); lost = sum(1 for b in have if not (ctrlA[b] & ctrlB[b]))
print("buildings with controlling ground under walls: %d | identical set under footprints: %d | some of the same ground: %d | none of the same ground: %d (%.0f%%; gate is 20%%)" % (len(have), same, overlap, lost, 100 * lost / len(have)))
pa = sum(int(aa[l].sum()) for l in locs); kept = sum(int((aa[l] & ab[l]).sum()) for l in locs); new = sum(int((~aa[l] & ab[l]).sum()) for l in locs)
print("active (location, building) pairs: %d under walls; %d of them still active under footprints (%.0f%%); %d new" % (pa, kept, 100 * kept / pa, new))
np.savez("results/air/buildings_test.npz", c_walls=ca, c_footprints=cb, lost=lost, have=len(have))
