"""Go/no-go, Air side. (1) critical net rain depth per receptor from the fill model; (2) which small patch of ground,
raised or lowered 5 cm, moves it most; (3) spread of critical depth under terrain noise; (4) write 20 predicted flips.
Run: uv run --with numpy --with scipy python fill/decisive.py
"""
import sys, time, numpy as np
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]
R = np.load("shared/receptors.npz"); rc = R["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
PG = np.linspace(0.0, 0.130, 261)                       # net rain grid, 0.5 mm steps

def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); D = M.depth_at(LL, rc)
    wet = D >= THR
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf), M, D

t0 = time.time(); c0, M0, D0 = crit(z0); t1 = time.time() - t0
has = np.isfinite(c0) & (c0 > 0.5)
print("one terrain x %d rain depths: %.2f s. receptors with a critical depth in 0.5-130 mm: %d; always wet: %d" % (len(PG), t1, has.sum(), (c0 <= 0.5).sum()))
print("critical net depth mm:", np.round(np.sort(c0[has]), 1))

# ---- (2) candidate patches: the pass cells of the merge tree on each receptor's root path (where ponds spill or merge)
def pass_cells(M):
    """For every internal node, the two cells either side of its lowest pass."""
    z, lab = M.z, M.lab; best = {}
    for sa, sb, da in (((slice(None), slice(0, -1)), (slice(None), slice(1, None)), (0, 1)), ((slice(0, -1), slice(None)), (slice(1, None), slice(None)), (1, 0))):
        la, lb = lab[sa], lab[sb]; w = np.maximum(z[sa], z[sb]); m = (la != lb) & (la >= 0) & (lb >= 0)
        rr, cc = np.nonzero(m)
        for r, c, a, b, ww in zip(rr, cc, la[m], lb[m], w[m]):
            k = (min(a, b), max(a, b))
            if k not in best or ww < best[k][0]: best[k] = (ww, (r, c), (r + da[0], c + da[1]))
    return best
best = pass_cells(M0)
node_pass = {}
for n in range(M0.nb, M0.N):
    k = (min(M0.la[n], M0.lb[n]), max(M0.la[n], M0.lb[n]))
    if k in best: node_pass[n] = best[k]
leaf = M0.lab[rc[:, 0], rc[:, 1]]
cands = {}                                                 # pass node -> receptors that have it on their root path (lowest 40 ancestors)
for r in np.flatnonzero(has):
    n = leaf[r]; k = 0
    while M0.parent[n] >= 0 and k < 40:
        n = M0.parent[n]; k += 1
        if n in node_pass and M0.h[n] < 1e8: cands.setdefault(n, []).append(r)
print("candidate passes on root paths of at-risk receptors:", len(cands))

def patch(z, cell, dz, rad=1):
    z = z.copy(); r, c = cell
    sl = (slice(max(r - rad, 0), r + rad + 1), slice(max(c - rad, 0), c + rad + 1))
    z[sl] = np.where(op[sl], z[sl] + dz, z[sl]); return z, sl

rows = []; t0 = time.time()
order = sorted(cands, key=lambda n: -len(cands[n]))[:160]
for i, n in enumerate(order):
    w, ca_, cb_ = node_pass[n]
    for dz in (+0.05, -0.05):
        zp, sl = patch(z0, ca_, dz)
        c1, _, _ = crit(zp)
        d = c1 - c0
        for r in np.flatnonzero(has):
            if np.isfinite(d[r]) and abs(d[r]) >= 1.0 or (np.isfinite(c0[r]) != np.isfinite(c1[r])):
                rows.append((n, ca_[0], ca_[1], dz, r, c0[r], c1[r]))
    if i % 20 == 19: print("  %d/%d passes, %.0fs, effects so far %d" % (i + 1, len(order), time.time() - t0, len(rows)), flush=True)
rows = np.array(rows, dtype=np.float64)
np.save("results/air/pass_effects.npy", rows)
print("patch tests: %d (3x3 m, +-5 cm) in %.0f s; receptor critical depths moved by >= 1 mm: %d effects on %d receptors, from %d distinct passes" % (2 * len(order), time.time() - t0, len(rows), len(set(rows[:, 4])) if len(rows) else 0, len(set(rows[:, 0])) if len(rows) else 0))
if len(rows):
    ch = np.where(np.isfinite(rows[:, 6]), rows[:, 6] - rows[:, 5], np.inf)
    fin = np.isfinite(ch)
    print("shift in critical depth mm for a 5 cm, 9 m2 change: median |shift| %.1f, p90 %.1f, max %.1f; relative median %.0f%%; made never-flood: %d" % (
        np.median(np.abs(ch[fin])), np.percentile(np.abs(ch[fin]), 90), np.abs(ch[fin]).max(), 100 * np.median(np.abs(ch[fin]) / rows[fin, 5]), (~fin).sum()))
    best_per = {}
    for row, c in zip(rows, ch):
        r = int(row[4]); s = abs(c) if np.isfinite(c) else 1e9
        if r not in best_per or s > best_per[r][0]: best_per[r] = (s, row)
    big = sum(1 for s, _ in best_per.values() if s >= 5)
    print("at-risk receptors whose critical depth moves >= 5 mm from ONE 9 m2 patch at 5 cm: %d of %d" % (big, has.sum()))
