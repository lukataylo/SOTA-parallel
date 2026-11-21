"""Run the audit what-ifs in shared/audit.npz at one storm (0 = 15 mm, 1 = 35 mm). Resumable. Terrain n_packs is the unchanged terrain.
  uv run --with mlx --with numpy python fill/audit_run.py 1"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
S = int(sys.argv[1]); out = f"results/pro/audit/s{S}"; os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); Q = np.load("shared/audit.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
def terrain(k):
    zc = z.copy(); m = Q["pack_of"] == k
    for r, c, dz in zip(Q["r"][m], Q["c"][m], Q["dz"][m]): sl = (slice(r - 2, r + 3), slice(c - 2, c + 3)); zc[sl] += np.where(op[sl], dz, 0).astype(np.float32)
    return zc
K = int(Q["n_packs"]) + 1
for c in list(range(0, K, 6))[::-1]:                                   # last chunk first, so the unchanged terrain is run early
    f = f"{out}/audit_{c:03d}.npz"
    if os.path.exists(f): continue
    kk = np.arange(c, min(c + 6, K)); m = len(kk); t0 = time.time()
    o = simulate(np.array([terrain(k) for k in kk]), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    np.savez(f + ".tmp.npz", k=kk, peak=o["peak_depth"], imbalance=o["imbalance"], wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f); print("terrains %d-%d: %.0fs" % (kk[0], kk[-1], time.time() - t0), flush=True)
print("done")
