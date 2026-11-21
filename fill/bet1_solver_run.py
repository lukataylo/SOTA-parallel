"""Bet 1 in the solver: does knowing the ensemble-chosen 1% of ground cut the spread of each building's critical rainfall?
Arms:  A  survey error everywhere      B  error removed on the chosen ground (results/air/bet1_cpu2_selection.npz)      C  error removed on random ground
Each terrain is run up a ladder of rain depths (centred triangle, 40 min + 20 min). Chunked and resumable.
  uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py pilot      # 8 terrains x 6 levels x arms A,B = 96 runs
  uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py full       # 30 terrains x 12 levels x arms A,B,C = 1,080 runs
Error fields are the held-out ones used in the fill-model test (seeds 1000+), 5 cm sd, 3 m correlation."""
import sys, os, time, numpy as np
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "solver"); from flood import simulate
mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
NT, LEVELS, ARMS = (8, np.array([8., 13., 19., 27., 38., 55.]), "AB") if mode == "pilot" else (30, np.array([5., 8., 11., 14., 18., 22., 27., 33., 40., 50., 65., 85.]), "ABC")
out = f"results/pro/bet1_{mode}"; os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); z, op, dx = t["z"], t["open"], float(t["dx"]); rc = np.load("shared/receptors.npz")["rc"]
sel = np.load("results/air/bet1_cpu2_selection.npz")["known"]; rnd = np.load("results/air/bet1_cpu.npz")["known_C"]
LOSS, DUR = 12.0, 40
def profile_for_net(net_mm):
    m = DUR; x = (np.arange(m) + 0.5) / m; w = np.where(x <= 0.5, x / 0.5, (1 - x) / 0.5); w /= w.sum(); lo, hi = net_mm, net_mm + 40.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if np.maximum(w * mid * 60.0 - LOSS, 0).sum() / 60.0 < net_mm: lo = mid
        else: hi = mid
    p = np.zeros(60, np.float32); p[:m] = w * hi * 60.0; return p
PROF = np.array([profile_for_net(n) for n in LEVELS])
def noise(seed): n = gaussian_filter(np.random.default_rng(seed).normal(size=z.shape), 3.0); return n * (0.05 / n.std())
def terrain(seed, arm):
    n = noise(1000 + seed)
    if arm == "B": n = np.where(sel, 0.0, n)
    if arm == "C": n = np.where(rnd, 0.0, n)
    return np.where(op, z + n, z).astype(np.float32)
np.savez(f"{out}/setup.npz", levels_net_mm=LEVELS, profile=PROF, arms=np.array(list(ARMS)), n_terrains=NT, loss_mm_h=LOSS, t_end_s=DUR * 60 + 1200.0)
for seed in range(NT):
    for arm in ARMS:
        f = f"{out}/t{seed:03d}_{arm}.npz"
        if os.path.exists(f): continue
        zt = terrain(seed, arm); pk, fn, im = [], [], []; t0 = time.time()
        for c in range(0, len(LEVELS), 6):
            ii = np.arange(c, min(c + 6, len(LEVELS))); m = len(ii)
            o = simulate(np.repeat(zt[None], m, 0), op, dx, rc, PROF[ii], 60.0, np.full(m, LOSS, np.float32), np.full(m, DUR * 60 + 1200.0, np.float32))
            pk.append(o["peak_depth"]); fn.append(o["final_depth"]); im.append(o["imbalance"])
        np.savez(f + ".tmp.npz", peak=np.concatenate(pk), final=np.concatenate(fn), imbalance=np.concatenate(im), ground_at_receptors=zt[rc[:, 0], rc[:, 1]], seed=seed, arm=arm, wall_s=time.time() - t0)
        os.replace(f + ".tmp.npz", f); print(f"terrain {seed} arm {arm}: {time.time() - t0:.0f}s", flush=True)
print("done")
