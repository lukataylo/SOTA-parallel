"""Friction sensitivity on a subset of the control experiment: the first 10 patches of each class in shared/p1_cases.npz,
middle storm (35 mm net), with Manning's n = 0.02 (the Environment Agency's 2013 value for tarmac) in place of 0.015. 31 runs.
  uv run --with mlx --with numpy python fill/p1_friction_run.py"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
out = "results/pro/p1_friction"; os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); S = 1; N = 0.02
cases = np.concatenate([np.flatnonzero(d["kind"] == k)[:10] for k in ("null", "random", "positive")])
def run(terrains):
    m = len(terrains)
    o = simulate(np.array(terrains), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32), n_manning=N)
    return o["peak_depth"], o["final_depth"], o["imbalance"]
if not os.path.exists(f"{out}/base.npz"):
    a, b, c = run([z]); np.savez(f"{out}/base.npz", peak=a[0], final=b[0], imbalance=c[0], n_manning=N, storm=S)
for c in range(0, len(cases), 6):
    f = f"{out}/chunk_{c:03d}.npz"
    if os.path.exists(f): continue
    ii = cases[c:c + 6]; zs = []
    for i in ii:
        a, b, lo, hi = d["rect"][i]; zc = z.copy(); zc[a:b, lo:hi] += np.where(op[a:b, lo:hi], d["dz"][i], 0).astype(np.float32); zs.append(zc)
    t0 = time.time(); pk, fn, im = run(zs); np.savez(f, case=ii, peak=pk, final=fn, imbalance=im, wall_s=time.time() - t0); print(f"cases {ii.tolist()}: {time.time() - t0:.0f}s", flush=True)
print("done")
