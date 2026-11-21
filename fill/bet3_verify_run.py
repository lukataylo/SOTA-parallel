"""Bet 3 in the solver: the harm-free 5-patch design and the naive 5-patch design from results/air/bet3_all.npz, at the three
standard storms, against the unchanged terrain (reuses the control experiment's baseline if present). 6 runs (+3).
  uv run --with mlx --with numpy python fill/bet3_verify_run.py"""
import sys, os, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
jobs = np.load("results/air/decisive.npz")["jobs"]; b3 = np.load("results/air/bet3_all.npz")
def build(design):
    zc = z.copy()
    for j in design:
        r, c, dz, rad = jobs[j]; r, c = int(r), int(c); sl = (slice(max(r - 2, 0), r + 3), slice(max(c - 2, 0), c + 3)); zc[sl] += np.where(op[sl], dz, 0).astype(np.float32)
    return zc
terr = [z, build(b3["design"]), build(b3["naive"])]; pk, fn = [], []
for s in range(3):
    o = simulate(np.array(terr), op, dx, rc, np.repeat(d["profile"][s][None], 3, 0), float(d["profile_dt_s"]), np.full(3, float(d["loss_mm_h"]), np.float32), np.full(3, float(d["t_end_s"]), np.float32))
    pk.append(o["peak_depth"]); fn.append(o["final_depth"]); print("storm", s, "done", flush=True)
os.makedirs("results/pro", exist_ok=True)
np.savez("results/pro/bet3_verify.npz", peak=np.array(pk), final=np.array(fn), arms=np.array(["unchanged", "harm_free_design", "naive_design"]), net_mm=d["net_mm"], design=b3["design"], naive=b3["naive"])
P = np.array(pk)
for a, nm in ((1, "harm-free design"), (2, "naive design")):
    dd = P[:, a] - P[:, 0]; print("%s: receptors whose peak falls by >= 1 cm in any storm: %d; rises by >= 1 cm: %d; largest rise %.1f cm" % (nm, (dd.min(0) <= -0.01).sum(), (dd.max(0) >= 0.01).sum(), dd.max() * 100))
