"""Parallel version: (a) every candidate pass, 5x5 m patch, +-5 cm; (b) terrain-noise ensemble. 9 worker processes."""
import sys, time, numpy as np, multiprocessing as mp
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]
rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
PG = np.linspace(0.0, 0.130, 261)
def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); D = M.depth_at(LL, rc); wet = D >= THR
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
def do_patch(a):
    r, c, dz, rad = a; z = z0.copy(); sl = (slice(max(r - rad, 0), r + rad + 1), slice(max(c - rad, 0), c + rad + 1))
    z[sl] = np.where(op[sl], z[sl] + dz, z[sl]); return crit(z)
def do_noise(a):
    seed, sd, corr = a; g = np.random.default_rng(seed).normal(size=z0.shape)
    n = gaussian_filter(g, corr); n *= sd / n.std(); return crit(np.where(op, z0 + n, z0))
if __name__ == "__main__":
    M0 = FillModel(z0, op, outlet); LL, _ = M0.run(PG); D0 = M0.depth_at(LL, rc); wet = D0 >= THR
    c0 = np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf); has = np.isfinite(c0)
    # pass cells per internal node
    z, lab = M0.z, M0.lab; best = {}
    for sa, sb, da in (((slice(None), slice(0, -1)), (slice(None), slice(1, None)), (0, 1)), ((slice(0, -1), slice(None)), (slice(1, None), slice(None)), (1, 0))):
        la, lb = lab[sa], lab[sb]; w = np.maximum(z[sa], z[sb]); m = (la != lb) & (la >= 0) & (lb >= 0); rr, cc = np.nonzero(m)
        for r, c, a, b, ww in zip(rr, cc, la[m], lb[m], w[m]):
            k = (min(a, b), max(a, b))
            if k not in best or ww < best[k][0]: best[k] = (ww, (int(r), int(c)))
    leaf = M0.lab[rc[:, 0], rc[:, 1]]; cells = {}
    for r in np.flatnonzero(has):
        n = leaf[r]; k = 0
        while M0.parent[n] >= 0 and k < 60:
            n = M0.parent[n]; k += 1; key = (min(M0.la[n], M0.lb[n]), max(M0.la[n], M0.lb[n]))
            if key in best and M0.h[n] < 1e8: cells[best[key][1]] = M0.h[n]
    jobs = [(r, c, dz, 2) for (r, c) in cells for dz in (0.05, -0.05)]
    print("patch jobs", len(jobs), flush=True); t0 = time.time()
    with mp.Pool(9) as pool:
        res = pool.map(do_patch, jobs, chunksize=4); tp = time.time() - t0
        print("patches done %.0fs" % tp, flush=True)
        njobs = [(s, sd, 3.0) for sd in (0.02, 0.05, 0.10) for s in range(120)]
        t0 = time.time(); nres = pool.map(do_noise, njobs, chunksize=4); tn = time.time() - t0
    C = np.array(res); np.savez("results/air/decisive.npz", c0=c0, jobs=np.array(jobs), crit_patch=C, noise_jobs=np.array(njobs), crit_noise=np.array(nres), PG=PG)
    d = C - c0[None]; d[~np.isfinite(d)] = np.nan
    flipinf = np.isfinite(c0)[None] ^ np.isfinite(C)
    eff = (np.abs(np.nan_to_num(d)) >= 1.0) | flipinf
    print("PATCHES: %d tests of a 25 m2 patch at +-5 cm in %.0f s on 9 cores (%d rain depths each)" % (len(jobs), tp, len(PG)))
    print("  patches that move any receptor's critical depth by >= 1 mm: %d of %d; receptors moved: %d of %d at risk" % (eff.any(1).sum(), len(jobs), eff[:, has].any(0).sum(), has.sum()))
    mx = np.nanmax(np.abs(np.where(eff, np.nan_to_num(d, nan=200.0), 0)), 0)
    print("  largest shift per at-risk receptor from ONE patch, mm:", np.round(np.sort(mx[has]), 1))
    print("  at-risk receptors moved >= 5 mm by one patch: %d; >= 10%% of their critical depth: %d; newly at risk (never -> flood): %d" % ((mx[has] >= 5).sum(), (mx[has] >= 0.1 * c0[has]).sum(), (flipinf[:, ~has].any(0)).sum()))
    N = np.array(nres)
    for i, sd in enumerate((0.02, 0.05, 0.10)):
        X = N[i * 120:(i + 1) * 120][:, has]; fin = np.isfinite(X)
        Xn = np.where(fin, X, np.nan); sdv = np.nanstd(Xn, 0); rel = sdv / c0[has]
        rng = np.nanpercentile(Xn, 95, 0) - np.nanpercentile(Xn, 5, 0)
        print("NOISE sd %.0f cm (3 m correlation), 120 terrains: spread of critical depth per at-risk receptor: median sd %.1f mm (%.0f%% of its value), median 5-95%% range %.1f mm; receptors with relative sd > 10%%: %d of %d; became never-flood in some terrain: %d" % (
            sd * 100, np.nanmedian(sdv), 100 * np.nanmedian(rel), np.nanmedian(rng), (rel > 0.10).sum(), has.sum(), (~fin).any(0).sum()))
        newly = np.isfinite(N[i * 120:(i + 1) * 120][:, ~has]).mean(0)
        print("   never-flood receptors that flood (<=130 mm) in at least 10%% of noisy terrains: %d of %d" % ((newly >= 0.1).sum(), (~has).sum()))
    print("noise ensemble: %d terrains x %d rain depths in %.0f s" % (len(njobs), len(PG), tn))
