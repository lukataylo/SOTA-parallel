"""The shortcut (fill) model for every square, both signs, at six water depths. For each depth: the largest predicted change at any wall point
more than 7.5 m from the square. Protocol in docs/G_CRITERIA.md. uv run --with numpy --with scipy python fill/map_fill_depths.py"""
import sys, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; D = np.array([25, 35, 43, 50, 60, 70]) * 1e-3
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
def dep(z): M = FillModel(z, op, outlet); LL, _ = M.run(D); return M.depth_at(LL, rc)
BASE = None
def job(a):
    global BASE
    if BASE is None: BASE = dep(z0)
    i, j, dz = a; z = z0.copy(); sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    far = np.hypot(rc[:, 0] - (5 * i + 2), rc[:, 1] - (5 * j + 2)) > 7.5; ch = np.where(far[None], dep(z) - BASE, 0); return np.abs(ch).max(1)
if __name__ == "__main__":
    F = np.load("results/air/map_final.npz"); mv = F["mover"][0] | F["mover"][1]; x = 5 * F["j"] + 2; rng = np.random.default_rng(2026); rest = np.flatnonzero(~mv)
    pick = np.concatenate([np.flatnonzero(mv), rng.choice(rest[x[rest] < 256], 250, replace=False), rng.choice(rest[x[rest] >= 256], 250, replace=False)])   # every mover square, plus 250 random other squares per half for the flag rate
    B = [(int(F["i"][n]), int(F["j"][n])) for n in pick]; jobs = [(i, j, dz) for dz in (0.05, -0.05) for i, j in B]
    with mp.Pool(9) as p:
        R = []
        for n, r in enumerate(p.imap(job, jobs, chunksize=8)):
            R.append(r)
            if n % 100 == 0: print(n, flush=True)
    np.savez("results/air/map_fill_depths.npz", depths_mm=D * 1e3, index=pick, is_mover_square=mv[pick], change=np.array(R).reshape(2, len(B), len(D))); print("done", flush=True)
