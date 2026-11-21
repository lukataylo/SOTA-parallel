"""Unbiased audit of the depth-change screen. A uniform random sample of (5 x 5 m block, +-5 cm) what-ifs over all open ground,
with the fill model's predicted depth change at every receptor for the 15 and 35 mm storms, packed 120 m apart (the spacing at which
packed and single runs agreed to 0.2 mm). Lines are in docs/AUDIT_CRITERIA.md, written before any solver run.
  uv run --with numpy --with scipy --with numba python fill/audit_make.py"""
import sys, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
N, SEED, GAP, NEAR = 3400, 2026, 120.0, 7.5
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; d = np.load("shared/p1_cases.npz")
NET = d["net_mm"][:2].astype(np.float64) * 1e-3                                   # 15 and 35 mm net
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
def fill_depth(job):
    r, c, dz = job; z = z0.copy(); sl = (slice(r - 2, r + 3), slice(c - 2, c + 3)); z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    M = FillModel(z, op, outlet); LL, _ = M.run(NET); return M.depth_at(LL, rc)
if __name__ == "__main__":
    cr, cc = np.meshgrid(np.arange(2, 510, 5), np.arange(2, 510, 5), indexing="ij"); ok = op[cr, cc]; br, bc = cr[ok], cc[ok]
    rng = np.random.default_rng(SEED); pick = rng.choice(2 * len(br), N, replace=False); r, c, dz = br[pick // 2], bc[pick // 2], np.where(pick % 2 == 0, 0.05, -0.05)
    print("blocks with an open centre: %d; what-ifs possible: %d; sampled: %d" % (len(br), 2 * len(br), N), flush=True)
    M0 = FillModel(z0, op, outlet); LL, _ = M0.run(NET); base = M0.depth_at(LL, rc)
    with mp.Pool(8) as p: FD = np.array(p.map(fill_depth, [(int(a), int(b), float(e)) for a, b, e in zip(r, c, dz)], chunksize=8))
    far = np.hypot(r[:, None] - rc[None, :, 0], c[:, None] - rc[None, :, 1]) > NEAR                # (what-if, receptor)
    fch = np.where(far[:, None, :], FD - base[None], 0.0); fmax = np.abs(fch).max(2)               # (what-if, storm)
    packs = []; pack_of = np.zeros(N, int)
    for i in range(N):                                                                             # sample order is already random
        for k, p_ in enumerate(packs):
            if (np.hypot(r[p_] - r[i], c[p_] - c[i]) >= GAP).all(): p_.append(i); pack_of[i] = k; break
        else: packs.append([i]); pack_of[i] = len(packs) - 1
    for s in range(2): print("storm %d (%.0f mm): fill model predicts 1 mm or more at a receptor beyond %.1f m for %d what-ifs; dismissed %d" % (s, NET[s] * 1e3, NEAR, (fmax[:, s] >= 0.001).sum(), (fmax[:, s] < 0.001).sum()))
    print("packed into %d terrains; what-ifs per terrain: median %d, min %d, max %d" % (len(packs), np.median([len(p_) for p_ in packs]), min(map(len, packs)), max(map(len, packs))))
    np.savez("shared/audit.npz", r=r, c=c, dz=dz, pack_of=pack_of, n_packs=len(packs), fill_change=fch.astype(np.float32), fill_max=fmax, net_mm=NET * 1e3, gap_m=GAP, near_m=NEAR, seed=SEED)
