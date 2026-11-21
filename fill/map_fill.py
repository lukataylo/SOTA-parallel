"""Fill-model prediction for every block of the map, both signs, at the 35 mm storm: largest predicted depth change at any receptor
more than 7.5 m from the block. Computed before the map is scored. uv run --with numpy --with scipy python fill/map_fill.py"""
import sys, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; NET = float(np.load("shared/p1_cases.npz")["net_mm"][1]) * 1e-3
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
def dep(z): M = FillModel(z, op, outlet); LL, _ = M.run(np.array([NET])); return M.depth_at(LL, rc)[0]
BASE = None
def job(a):
    global BASE
    if BASE is None: BASE = dep(z0)
    i, j, dz = a; z = z0.copy(); sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    far = np.hypot(rc[:, 0] - (5 * i + 2), rc[:, 1] - (5 * j + 2)) > 7.5; ch = np.where(far, dep(z) - BASE, 0); k = np.abs(ch).argmax(); return ch[k]
if __name__ == "__main__":
    B = [(i, j) for i in range(1, 101) for j in range(1, 101) if op[5 * i:5 * i + 5, 5 * j:5 * j + 5].any()]; jobs = [(i, j, dz) for dz in (0.05, -0.05) for i, j in B]
    with mp.Pool(7) as p: R = np.array(p.map(job, jobs, chunksize=16))
    np.savez("results/air/map_fill.npz", i=np.array([b[0] for b in B]), j=np.array([b[1] for b in B]), fill_change=R.reshape(2, len(B)))   # row 0 raise, row 1 lower
    print("blocks %d; fill predicts a change of 1 mm or more: raise %d, lower %d" % (len(B), (np.abs(R[:len(B)]) >= 1e-3).sum(), (np.abs(R[len(B):]) >= 1e-3).sum()))
