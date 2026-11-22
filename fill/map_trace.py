"""Trace the moves the packed map could not place: receptors that moved 1 cm with no block within 75 m, and movers that did not move
their building when re-run alone. For each such (sign, colour), every block of that colour within 150 m of the affected building is
run on its own. Changes no pass line: the unattributed line stays failed. uv run --with mlx --with numpy python fill/map_trace.py"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); sys.path.insert(0, "fill"); from flood import simulate; import map_lib as L
rc = L.rc; out = "results/air/map/trace"; os.makedirs(out, exist_ok=True); plan = f"{out}/plan.npz"
if not os.path.exists(plan):
    M = np.load("results/air/map_scored.npz"); jobs = {}
    for k, s in enumerate(("raise", "lower")):
        _, ch, _ = L.load(s); want = {}
        for c, d in ch.items():
            B = L.blocks_of(c); cen = np.array([(5 * i + 2, 5 * j + 2) for i, j in B], float); dn = np.hypot(cen[:, None, 0] - rc[None, :, 0], cen[:, None, 1] - rc[None, :, 1]).min(0)
            for q in np.flatnonzero((np.abs(d) >= L.THR) & (dn > L.FAR)): want.setdefault(c, set()).add(int(q))
        for n in np.flatnonzero(M["mover"][k] & ~M["confirmed"][k]): i, j = int(M["i"][n]), int(M["j"][n]); want.setdefault((i % L.P) * L.P + j % L.P, set()).add(int(M["receptor"][k, n]))
        for c, qs in want.items():
            for i, j in L.blocks_of(c):
                if min(np.hypot(5 * i + 2 - rc[q, 0], 5 * j + 2 - rc[q, 1]) for q in qs) <= 150: jobs[(k, i, j)] = c
    J = sorted(jobs); np.savez(plan, job=np.array(J), colour=np.array([jobs[a] for a in J])); print("single runs planned: %d" % len(J))
J = np.load(plan)["job"]; t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); z, op, dx = t["z"], t["open"], float(t["dx"])
def terrain(a):
    k, i, j = a; zc = z.copy(); sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], 0.05 if k == 0 else -0.05, 0).astype(np.float32); return zc
for c in range(0, len(J), 6):
    f = f"{out}/t{c:03d}.npz"
    if os.path.exists(f): continue
    kk = np.arange(c, min(c + 6, len(J))); m = len(kk); t0 = time.time()
    o = simulate(np.array([terrain(J[k]) for k in kk]), op, dx, rc, np.repeat(d["profile"][1][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    np.savez(f + ".tmp.npz", k=kk, peak=o["peak_depth"], imbalance=o["imbalance"], wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f); print("trace %d-%d: %.0fs" % (kk[0], kk[-1], time.time() - t0), flush=True)
print("done")
