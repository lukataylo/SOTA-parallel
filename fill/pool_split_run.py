"""Run the packed suspects from the pool test. Resumable. uv run --with mlx --with numpy python fill/pool_split_run.py"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
out = "results/air/pool_split"; os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); Q = np.load("shared/pool_split.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); S = int(Q["storm"])
def terrain(k):
    zc = z.copy()
    for r, c, dz in zip(Q["r"][Q["pack_of"] == k], Q["c"][Q["pack_of"] == k], Q["dz"][Q["pack_of"] == k]): sl = (slice(r - 2, r + 3), slice(c - 2, c + 3)); zc[sl] += np.where(op[sl], dz, 0).astype(np.float32)
    return zc
K = int(Q["n_packs"])
for c in range(0, K, 6):
    f = f"{out}/split_{c:03d}.npz"
    if os.path.exists(f): continue
    kk = np.arange(c, min(c + 6, K)); m = len(kk); t0 = time.time()
    o = simulate(np.array([terrain(k) for k in kk]), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    np.savez(f + ".tmp.npz", k=kk, peak=o["peak_depth"], imbalance=o["imbalance"], wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f); print("packs %d-%d: %.0fs" % (kk[0], kk[-1], time.time() - t0), flush=True)
print("done")
