"""Run the pool test. Resumable; two machines can share it (forward / reverse).
uv run --with mlx --with numpy python fill/pool_run.py [forward|reverse]
Terrain k in 0..63: pool k with checkerboard signs. 64..127: the same pools with every sign flipped. 128..: positive controls."""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
out = "results/air/pool_test"; os.makedirs(out, exist_ok=True); direction = sys.argv[1] if len(sys.argv) > 1 else "forward"
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); P = np.load("shared/pool_test.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); S = int(P["storm"]); NP = int(P["n_pools"])
def terrain(k):
    zc = z.copy(); pool = k % NP if k < 2 * NP else int(P["control_pool"][k - 2 * NP]); flip = (k >= NP) and (k < 2 * NP)
    for r, c, par in zip(P["block_r"][P["cls"] == pool], P["block_c"][P["cls"] == pool], P["parity"][P["cls"] == pool]):
        dz = 0.05 if (par == 0) != flip else -0.05; sl = (slice(r - 2, r + 3), slice(c - 2, c + 3)); zc[sl] += np.where(op[sl], dz, 0).astype(np.float32)
    if k >= 2 * NP:
        i = int(P["control_case"][k - 2 * NP]); a, b, lo, hi = d["rect"][i]; zc[a:b, lo:hi] += np.where(op[a:b, lo:hi], d["dz"][i], 0).astype(np.float32)
    return zc
K = 2 * NP + len(P["control_case"]); chunks = list(range(0, K, 6)); chunks = chunks[::-1] if direction == "reverse" else chunks
for c in chunks:
    f = f"{out}/pool_{c:03d}.npz"
    if os.path.exists(f): continue
    kk = np.arange(c, min(c + 6, K)); t0 = time.time(); m = len(kk)
    o = simulate(np.array([terrain(k) for k in kk]), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    np.savez(f + ".tmp.npz", k=kk, peak=o["peak_depth"], imbalance=o["imbalance"], wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f); print("terrains %d-%d: %.0fs" % (kk[0], kk[-1], time.time() - t0), flush=True)
print("done")
