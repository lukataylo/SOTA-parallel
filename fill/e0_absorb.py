"""E0: the absorption map from the fill model.
For each at-risk building b: its critical net rain R*, the set C_b of leaf basins whose extra water raises b's level at R*,
and the contributing area A_b. Then (1) test the formula  rise in R* = captured volume / A_b  against exact re-solving on 100 placements,
(2) compare the absorption map with the height-leverage map, (3) greedy placement of 250 m3 of sink (about 1,000 m2 of rain garden).
Pass lines are in docs/ABSORPTION.md."""
import sys, time, numpy as np
sys.path.insert(0, "fill"); from absorb import FillSink
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
M = FillSink(z0, op, edge & op); nb = M.nb; leaf_of = M.lab[rc[:, 0], rc[:, 1]]; REF = z0[rc[:, 0], rc[:, 1]] + THR
def levels(P, **kw): LL, _ = M.run(P, **kw); return LL[leaf_of].T                      # (S, receptors)
def crit(sink=None, lo=0.0, hi=0.130, rounds=4, n=48):
    """critical net rain per receptor (m), refined by repeated grid search; inf if dry at 130 mm."""
    c = np.full(len(rc), np.inf); a = np.full(len(rc), lo); b = np.full(len(rc), hi)
    P = np.linspace(lo, hi, n); L = levels(P, sink=sink); wet = L >= REF[None]
    never = ~wet.any(0); k = np.where(never, n - 1, np.argmax(wet, 0)); b = P[k]; a = P[np.maximum(k - 1, 0)]
    for _ in range(rounds - 1):
        for g in np.unique(np.round(a, 9)):                                           # receptors sharing a bracket share a run
            m = (np.round(a, 9) == g) & ~never
            if not m.any(): continue
            for bb in np.unique(np.round(b[m], 9)):
                mm = m & (np.round(b, 9) == bb)
                P = np.linspace(g, bb, 12); L = levels(P, sink=sink)[:, mm]; w = L >= REF[mm][None]; k = np.argmax(w, 0)
                b[mm] = P[k]; a[mm] = P[np.maximum(k - 1, 0)]
    return np.where(never, np.inf, b)
t0 = time.time(); c0 = crit(); risk = np.flatnonzero(np.isfinite(c0) & (c0 > 0.001))
print("critical rain refined for %d at-risk buildings in %.0f s" % (len(risk), time.time() - t0), flush=True)
# ---- contributing sets: add 0.05 m3 at each leaf in turn, just below the critical rain
C = np.zeros((len(risk), nb), bool); A = np.zeros(len(risk)); t0 = time.time(); EPS = 0.05
for i, r in enumerate(risk):
    P0 = c0[r] - 2e-5
    base = levels(np.array([P0]))[0, r]
    for s in range(1, nb, 1500):
        leaves = np.arange(s, min(s + 1500, nb)); L = levels(np.full(len(leaves), P0), inject=(leaves, EPS))[:, r]
        C[i, leaves] = L > base + 1e-9
    A[i] = M.area[:nb][C[i]].sum()
    if i % 8 == 7: print("  contributing sets %d/%d, %.0fs" % (i + 1, len(risk), time.time() - t0), flush=True)
cells_in = C[:, np.maximum(M.lab, 0)] & (M.lab >= 0)[None]                              # (risk, ny, nx)
np.savez_compressed("results/air/e0_absorb.npz", risk=risk, c0=c0, C=C, A=A, absorb_count=cells_in.sum(0).astype(np.int16))
print("contributing area A_b, m2: min %.0f median %.0f max %.0f (open ground is %d m2); leaves in C_b: median %d" % (A.min(), np.median(A), A.max(), op.sum(), np.median(C.sum(1))))
any_c = cells_in.any(0); print("cells in at least one building's contributing set: %.1f%% of open ground; in 3 or more: %.1f%%" % (100 * any_c.sum() / op.sum(), 100 * (cells_in.sum(0) >= 3).sum() / op.sum()))
sel = np.load("results/air/bet1_cpu2_selection.npz")["known"]; d = np.load("results/air/decisive.npz"); cap = lambda x: np.where(np.isfinite(x), x, 200.0)
act = np.abs(cap(d["crit_patch"]) - cap(d["c0"])[None]).max(1) >= 1.0; hmap = np.zeros(z0.shape, bool)
for (r, c, dz, rad), a in zip(d["jobs"], act):
    if a: hmap[int(r) - 2:int(r) + 3, int(c) - 2:int(c) + 3] = True
hmap &= op
print("height-leverage ground (active patches): %.2f%% of open ground; share of it inside the absorption map: %.0f%%; share of the absorption map that is height-leverage ground: %.1f%%" % (100 * hmap.sum() / op.sum(), 100 * (hmap & any_c).sum() / max(hmap.sum(), 1), 100 * (hmap & any_c).sum() / max(any_c.sum(), 1)))
# ---- (1) formula check on 100 placements: a sink of volume v in one leaf of C_b
rng = np.random.default_rng(11); errs = []; filled = []; rows = []
for k in range(100):
    i = rng.integers(len(risk)); r = risk[i]; leaf = rng.choice(np.flatnonzero(C[i])); v = float(rng.choice([2.0, 5.0, 10.0, 25.0]))
    sink = np.zeros(nb); sink[leaf] = v; c1 = crit(sink=sink)[r]; pred = v / A[i]
    L, _ = M.run(np.array([c0[r]]), sink=None); inflow = float(M.last_inflow[leaf, 0])
    rows.append((r, leaf, v, c0[r], c1, pred, inflow)); 
rows = np.array(rows); true = rows[:, 4] - rows[:, 3]; pred = rows[:, 5]; fill_ok = rows[:, 6] >= rows[:, 2]
rel = np.abs(true - pred) / np.maximum(pred, 1e-12)
print("FORMULA CHECK, 100 placements: within 2%% of exact: %d of 100 | among sinks that fill (inflow >= capacity, %d cases): within 2%%: %d, within 10%%: %d | sinks that do not fill: %d, of which exact rise is below the formula: %d" % (
    (rel <= 0.02).sum(), fill_ok.sum(), (rel[fill_ok] <= 0.02).sum(), (rel[fill_ok] <= 0.10).sum(), (~fill_ok).sum(), (true[~fill_ok] < pred[~fill_ok] * 0.98).sum()))
print("   exact/formula ratio: median %.3f, p10 %.3f, p90 %.3f; exact rise is never above the formula by more than 2%%: %s" % (np.median(true / pred), np.percentile(true / pred, 10), np.percentile(true / pred, 90), bool((true <= pred * 1.02 + 1e-7).all())))
np.save("results/air/e0_formula_check.npy", rows)
# ---- (3) greedy placement of 250 m3 in 25 m3 units (about 100 m2 of rain garden each)
L, _ = M.run(np.array([0.030])); inflow30 = M.last_inflow[:, 0].astype(np.float64)       # water arriving at each leaf in a 30 mm storm
UNIT = 25.0; w = 1.0 / (A * c0[risk])                                                    # relative rise per m3 for each building
def lifted(c1): return int(((c1[risk] - c0[risk]) >= 0.10 * c0[risk]).sum()), int((c1 < c0 - 1e-4).sum())
sink = np.zeros(nb); t0 = time.time(); hist = []
for step in range(10):
    score = (C * w[:, None]).sum(0) * np.minimum(UNIT, np.maximum(inflow30 - sink, 0))
    cand = np.argsort(-score)[:12]; best = None
    for leaf in cand:
        s2 = sink.copy(); s2[leaf] += UNIT; c1 = crit(sink=s2, rounds=3); l, hrm = lifted(c1); tot = np.minimum(np.where(np.isfinite(c1[risk]), c1[risk], 0.13) / c0[risk], 3).sum()
        if best is None or (l, tot) > best[:2]: best = (l, tot, leaf, hrm)
    sink[best[2]] += UNIT; hist.append((step + 1, best[0], best[3]))
    print("  greedy step %d: %d m3 placed (%d m2 of rain garden): buildings lifted by >= 10%%: %d, harmed: %d (%.0fs)" % (step + 1, sink.sum(), sink.sum() / 0.25, best[0], best[3], time.time() - t0), flush=True)
c1 = crit(sink=sink); l, hrm = lifted(c1)
rs = np.zeros(nb); cand_all = np.flatnonzero(M.area[:nb] > 0)[1:]; res_rand = []
for k in range(8):
    rs = np.zeros(nb); rs[rng.choice(cand_all, 10, replace=False)] = UNIT; res_rand.append(lifted(crit(sink=rs, rounds=3))[0])
print("E0 RESULT: 250 m3 placed by the map lifts %d of %d at-risk buildings by >= 10%%, harms %d | 250 m3 in 10 random basins lifts: %s (median %.1f) | pass line: at least 5 -> %s" % (l, len(risk), hrm, res_rand, np.median(res_rand), "PASS" if l >= 5 else "KILL"))
print("   rise in critical rain for lifted buildings, mm:", np.round((c1[risk] - c0[risk])[(c1[risk] - c0[risk]) >= 0.10 * c0[risk]] * 1e3, 1))
np.savez("results/air/e0_design.npz", sink=sink, c1=c1, c0=c0, risk=risk, hist=np.array(hist), random_lifts=np.array(res_rand))
