"""Run the packed terrains for the bet G check. Resumable. uv run --with mlx --with numpy python fill/pack_run.py"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
out = "results/air/pack_check"; os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); pk = np.load("shared/pack_check.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
def add(zc, a, b, lo, hi, dz): zc[a:b, lo:hi] += np.where(op[a:b, lo:hi], dz, 0).astype(np.float32)
def run(terrains, s):
    m = len(terrains)
    o = simulate(np.array(terrains), op, dx, rc, np.repeat(d["profile"][s][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    return o["peak_depth"], o["imbalance"]
packs = [np.flatnonzero(pk["pack_of"] == k) for k in range(int(pk["n_packs"]))]; T = []
for p in packs:
    zc = z.copy()
    for i in p: add(zc, *d["rect"][i], d["dz"][i])
    T.append(zc)
for s in range(3):
    for c in range(0, len(T), 6):
        f = f"{out}/packs_s{s}_{c:03d}.npz"
        if os.path.exists(f): continue
        t0 = time.time(); a, b = run(T[c:c + 6], s); np.savez(f, pack=np.arange(c, min(c + 6, len(T))), storm=s, peak=a, imbalance=b, wall_s=time.time() - t0); print(f, "%.0fs" % (time.time() - t0), flush=True)
for s in range(3):
    ii = np.flatnonzero(pk["planted_storm"] == s)
    for c in range(0, len(ii), 6):
        f = f"{out}/planted_s{s}_{c:03d}.npz"
        if os.path.exists(f): continue
        jj = ii[c:c + 6]; ts = []
        for j in jj:
            zc = z.copy(); add(zc, *d["rect"][pk["planted_mover"][j]], d["dz"][pk["planted_mover"][j]])
            for r, cc, dz in pk["planted_extra"][j]:
                if r >= 0: add(zc, int(r) - 2, int(r) + 3, int(cc) - 2, int(cc) + 3, dz)
            ts.append(zc)
        t0 = time.time(); a, b = run(ts, s); np.savez(f, planted=jj, storm=s, peak=a, imbalance=b, wall_s=time.time() - t0); print(f, "%.0fs" % (time.time() - t0), flush=True)
print("done")
