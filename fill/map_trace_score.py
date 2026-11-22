"""Score fill/map_trace.py: for each move the packed map could not place, which block of that colour reproduces it alone."""
import sys, glob, numpy as np
sys.path.insert(0, "fill"); import map_lib as L
rc = L.rc; P = np.load("results/air/map/trace/plan.npz"); J, C = P["job"], P["colour"]; M = np.load("results/air/map_scored.npz"); idx = {(int(a), int(b)): n for n, (a, b) in enumerate(zip(M["i"], M["j"]))}
pk = np.full((len(J), 207), np.nan)
for f in sorted(glob.glob("results/air/map/trace/t*.npz")): c = np.load(f); pk[c["k"]] = c["peak"]
print("single runs done: %d of %d" % ((~np.isnan(pk[:, 0])).sum(), len(J))); tot = placed = 0; new = set(); reach = []
for k, s in enumerate(("raise", "lower")):
    base, ch, _ = L.load(s); ab = np.load(f"results/air/map/s1_{s}/base_start.npz")["peak"].astype(float); lost = {(int(M["i"][n]), int(M["j"][n])): int(M["receptor"][k, n]) for n in np.flatnonzero(M["mover"][k] & ~M["confirmed"][k])}
    for c in sorted(set(C[J[:, 0] == k])):
        B = L.blocks_of(c); cen = np.array([(5 * i + 2, 5 * j + 2) for i, j in B], float); dn = np.hypot(cen[:, None, 0] - rc[None, :, 0], cen[:, None, 1] - rc[None, :, 1]).min(0)
        qs = set(np.flatnonzero((np.abs(ch[c]) >= L.THR) & (dn > L.FAR)).tolist()) | {q for b, q in lost.items() if (b[0] % L.P) * L.P + b[1] % L.P == c}
        rows = np.flatnonzero((J[:, 0] == k) & (C == c))
        for q in sorted(qs):
            tot += 1; e = pk[rows, q] - ab[q]; n = np.nanargmax(np.abs(e)); i, j = J[rows[n], 1:]; d = np.hypot(5 * i + 2 - rc[q, 0], 5 * j + 2 - rc[q, 1]); ok = abs(e[n] - ch[c][q]) <= 0.002
            placed += ok; print("  %s colour %d building %d: packed run %.1f cm; alone, block (%d,%d) %.0f m away gives %.1f cm%s" % (s, c, q, 100 * ch[c][q], i, j, d, 100 * e[n], "" if ok else "  <- not reproduced by any one block"))
            if ok: reach.append(d); new.add((k, int(i), int(j))) if not M["confirmed"][k, idx[(int(i), int(j))]] else None
print("moves traced to one block: %d of %d; distance of that block, m: median %.0f, max %.0f" % (placed, tot, np.median(reach), max(reach)))
print("blocks that are movers only through a building more than 75 m away or behind a nearer block (not in the confirmed list): %d: %s" % (len(new), sorted(new)))
# final list: confirmed movers plus the blocks found only by tracing; saved for the figure and the table
fin = M["confirmed"].copy(); eff, dist, rcp = M["effect"].copy(), M["dist"].copy(), M["receptor"].copy(); ab = {s: np.load(f"results/air/map/s1_{s}/base_start.npz")["peak"].astype(float) for s in ("raise", "lower")}
for k, i, j in sorted(new):
    n = idx[(i, j)]; r = np.flatnonzero((J[:, 0] == k) & (J[:, 1] == i) & (J[:, 2] == j))[0]; e = pk[r] - ab[("raise", "lower")[k]]; D = np.hypot(5 * i + 2 - rc[:, 0], 5 * j + 2 - rc[:, 1]); q = np.abs(np.where(D > L.NEAR, e, 0)).argmax(); fin[k, n] = True; eff[k, n], dist[k, n], rcp[k, n] = e[q], D[q], q
r1, r2 = M["rule1"], M["rule2"]; nb = fin.shape[1]
print("FINAL: %d what-ifs of %d (%.2f%%) move a building more than 7.5 m away by 1 cm; blocks %d of %d (%.2f%%), both signs %d; raise %d, lower %d; deeper %d, shallower %d; buildings %d" % (fin.sum(), fin.size, 100 * fin.mean(), fin.any(0).sum(), nb, 100 * fin.any(0).mean(), fin.all(0).sum(), fin[0].sum(), fin[1].sum(), (eff[fin] > 0).sum(), (eff[fin] < 0).sum(), len(set(rcp[fin]))))
print("   distance m: median %.0f, p90 %.0f, max %.0f (longest traced reach %.0f); share more than 10 m away %.0f%%; effect cm: median %.1f, max %.1f" % (np.median(dist[fin]), np.percentile(dist[fin], 90), dist[fin].max(), max(reach), 100 * (dist[fin] > 10).mean(), 100 * np.median(np.abs(eff[fin])), 100 * np.abs(eff[fin]).max()))
for nm, fl in (("rule 1", r1), ("rule 2", r2)): print("   %s: flags %d (%.1f%%), finds %d of %d (%.0f%%), dismisses %d of which movers %d (%.2f%%); flagged that are movers %.0f%%" % (nm, fl.sum(), 100 * fl.mean(), (fl & fin).sum(), fin.sum(), 100 * (fl & fin).sum() / fin.sum(), (~fl).sum(), (~fl & fin).sum(), 100 * (~fl & fin).sum() / (~fl).sum(), 100 * (fl & fin).sum() / fl.sum()))
np.savez("results/air/map_final.npz", i=M["i"], j=M["j"], mover=fin, effect=eff, dist=dist, receptor=rcp, rule1=r1, rule2=r2)
