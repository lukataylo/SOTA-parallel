"""Bet 3, CPU step: search for a small set of 5 cm patches that raises many buildings' critical rainfall and lowers none.
Single-patch effects come from results/air/decisive.npz; every design reported here is re-evaluated exactly in the fill model
on the combined terrain. Fill effects are deflated by 0.6 (the measured solver/fill slope on remote patches) when counting benefit.
Pass line (set before running): a design of at most 5 patches lifts at least 5 buildings' critical rain by 10% or more, and harms none
(no receptor's critical rain lowered by 1 mm or more, and no never-flooding receptor put at risk)."""
import sys, time, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op; PG = np.linspace(0.0, 0.130, 261)
d = np.load("results/air/decisive.npz"); c0, jobs, C = d["c0"], d["jobs"], d["crit_patch"]; cap = lambda x: np.where(np.isfinite(x), x, 200.0)
DEFL = 0.6
def crit_of(design):
    z = z0.copy()
    for j in design:
        r, c, dz, rad = jobs[j]; r, c = int(r), int(c); sl = (slice(max(r - 2, 0), r + 3), slice(max(c - 2, 0), c + 3)); z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); D = M.depth_at(LL, rc); wet = D >= THR
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
def score(c1):
    delta = cap(c1) - cap(c0); atrisk = np.isfinite(c0)
    lifted = atrisk & (DEFL * delta >= 0.10 * c0); harmed = (delta <= -1.0)
    return int(lifted.sum()), int(harmed.sum()), lifted, harmed
def near_receptor(j, lim=5.0):
    r, c = jobs[j][:2]; return np.hypot(rc[:, 0] - r, rc[:, 1] - c).min() <= lim
if __name__ == "__main__":
    delta = cap(C) - cap(c0)[None]; atrisk = np.isfinite(c0)
    lift1 = (atrisk[None] & (DEFL * delta >= 0.10 * c0[None])).sum(1); harm1 = (delta <= -1.0).sum(1)
    remote = np.array([not near_receptor(j) for j in range(len(jobs))])
    print("single patches: any lift %d; lift and no harm %d; of those more than 5 m from every receptor %d; best single lift %d (harm %d)" % ((lift1 > 0).sum(), ((lift1 > 0) & (harm1 == 0)).sum(), ((lift1 > 0) & (harm1 == 0) & remote).sum(), lift1.max(), harm1[lift1.argmax()]), flush=True)
    for label, pool_idx in (("ALL ground", np.flatnonzero(lift1 > 0)), ("REMOTE ground only (> 5 m from every receptor)", np.flatnonzero((lift1 > 0) & remote))):
        pool_idx = pool_idx[np.argsort(-lift1[pool_idx])][:40]; design = []; best = (0, 0); t0 = time.time(); hist = []
        with mp.Pool(2) as p:
            for step in range(5):
                cand = [design + [int(j)] for j in pool_idx if int(j) not in design and all(tuple(jobs[j][:2]) != tuple(jobs[k][:2]) for k in design)]
                res = p.map(crit_of, cand, chunksize=2); sc = [score(c1)[:2] for c1 in res]
                ok = [i for i, (l, h) in enumerate(sc) if h == 0]
                if not ok: break
                i = max(ok, key=lambda i: sc[i][0])
                if sc[i][0] <= best[0]: break
                design, best = cand[i], sc[i]; hist.append((list(design), best))
                print("  %s step %d: %d patches lift %d buildings, harm %d (%.0fs)" % (label, step + 1, len(design), best[0], best[1], time.time() - t0), flush=True)
            # naive: the patches with the largest single lift, ignoring harm
            naive = [int(j) for j in pool_idx[:len(design) or 3]]; cn = crit_of(naive); ln, hn, _, harmedn = score(cn)
        c1 = crit_of(design); l, h, lifted, harmed = score(c1)
        print("%s: BEST HARM-FREE DESIGN %d patches (%d m2): lifts %d buildings by >= 10%% (deflated), harms %d | pass line: lift >= 5 and harm 0 -> %s" % (label, len(design), 25 * len(design), l, h, "PASS" if (l >= 5 and h == 0) else "FAIL"))
        for j in design: print("     patch centre (%d, %d) %+.0f cm, nearest receptor %.0f m" % (jobs[j][0], jobs[j][1], jobs[j][2] * 100, np.hypot(rc[:, 0] - jobs[j][0], rc[:, 1] - jobs[j][1]).min()))
        print("     lifted receptors:", np.flatnonzero(lifted).tolist(), "| critical rain mm before -> after:", [(round(float(c0[r]), 1), round(float(c1[r]), 1)) for r in np.flatnonzero(lifted)])
        print("   NAIVE design (top %d by single-patch lift, harm ignored): lifts %d, HARMS %d receptors %s" % (len(naive), ln, hn, np.flatnonzero(harmedn).tolist()))
        np.savez("results/air/bet3_%s.npz" % ("all" if label.startswith("ALL") else "remote"), design=np.array(design), naive=np.array(naive), crit_design=c1, crit_naive=cn, c0=c0)
