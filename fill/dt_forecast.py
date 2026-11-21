"""What sets the solver's time step? dt ~ 0.7*dx/sqrt(g*hmax). If the deepest ponds were handled separately, what would hmax be?"""
import sys, numpy as np
from scipy.ndimage import label
sys.path.insert(0, "fill"); from fillmodel import FillModel
t = np.load("shared/terrain_512.npz"); z, op = t["z"].astype(np.float64), t["open"]
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
M = FillModel(z, op, edge & op)
P = np.array([10, 25, 50, 75, 100]) * 1e-3; LL, _ = M.run(P)
dt = lambda h: min(1.0, 0.7 / np.sqrt(9.81 * max(h, 1e-6)))
for s, p in enumerate(P):
    d = M.depth_field(LL, s); w = d[op]; wet = w > 0.01
    q = np.percentile(w[wet], [50, 90, 99, 99.9])
    row = "net %3.0f mm: wet cells %6d | depth m: median %.2f p90 %.2f p99 %.2f p99.9 %.2f max %.2f | dt now %.2f s" % (p * 1e3, wet.sum(), *q, w.max(), dt(w.max()))
    for cut in (0.5, 0.75, 1.0):
        deep = d > cut; lab, n = label(deep)
        row += " | lump >%.2fm: %d cells in %d ponds -> dt %.2f (%.1fx)" % (cut, deep.sum(), n, dt(cut), dt(cut) / dt(w.max()))
    print(row)
