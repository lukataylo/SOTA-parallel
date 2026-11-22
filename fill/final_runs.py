"""Sunday morning checks. See docs/G_CRITERIA.md. uv run --with mlx --with numpy python fill/final_runs.py <job> <air|pro> [reverse]
Jobs: persist70, persistn, persist15, dense, random, design. One file per terrain in results/<machine>/final/<job>/; work done by either machine is skipped."""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
JOB, MACH = sys.argv[1], sys.argv[2]; REV = len(sys.argv) > 3 and sys.argv[3] == "reverse"
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); F = np.load("results/air/map_final.npz")
def bump(zc, k, i, j): sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], 0.05 if k == 0 else -0.05, 0).astype(np.float32)
S, NM = 1, 0.015
if JOB.startswith("persist"):
    S, NM = {"persist70": (2, 0.015), "persistn": (1, 0.03), "persist15": (0, 0.015)}[JOB]; W = [[(int(k), int(F["i"][n]), int(F["j"][n]))] for k in (0, 1) for n in np.flatnonzero(F["mover"][k])]
elif JOB == "dense":
    P = 15; W = [[(1, i, j) for i in range(c // P or P, 101, P) for j in range(c % P or P, 101, P)] for c in range(P * P)]
elif JOB == "random":
    sc = np.load("results/air/map_scored.npz")["mover"] | F["mover"]; kk, nn = np.nonzero(~sc); pick = np.random.default_rng(2026).choice(len(kk), 240, replace=False); W = [[(int(kk[p]), int(F["i"][nn[p]]), int(F["j"][nn[p]]))] for p in sorted(pick)]
elif JOB == "slice70":                                                   # packed map at 70 mm: first 80 colours of the seed-2026 order, both signs
    S = 2; P = 30; cs = [int(c) for c in np.random.default_rng(2026).permutation(P * P)][:80]; W = [[(k, i, j) for i in range(c // P or P, 101, P) for j in range(c % P or P, 101, P)] for k in (0, 1) for c in cs]
elif JOB == "slice70s":                                                  # its movers, each alone
    S = 2; W = [[tuple(int(v) for v in r)] for r in np.load("shared/slice70_plan.npz")["blocks"]]
elif JOB == "design":
    W = [[tuple(int(v) for v in r) for r in np.load("shared/map_design.npz")["blocks"]]]
out = f"results/{MACH}/final/{JOB}"; os.makedirs(out, exist_ok=True)
def terrain(n):
    zc = z.copy()
    if n >= 0:
        for k, i, j in W[n]: bump(zc, k, i, j)
    return zc
name = lambda n: "base" if n < 0 else "r%03d" % n
def done(n): return any(os.path.exists(f"results/{m}/final/{JOB}/{name(n)}.npz") for m in ("air", "pro"))
idxs = list(range(0, 240, 2)) if (JOB == "random" and MACH == "air") else list(range(len(W))); order = [-1] + (idxs[::-1] if REV else idxs)
while True:
    todo = [n for n in order if not done(n) or (n < 0 and not os.path.exists(f"{out}/base.npz"))][:6]
    if not todo: break
    m = len(todo); t0 = time.time()
    o = simulate(np.array([terrain(n) for n in todo]), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32), n_manning=NM)
    for q, n in enumerate(todo): f = f"{out}/{name(n)}.npz"; np.savez(f + ".tmp.npz", n=n, peak=o["peak_depth"][q], imbalance=o["imbalance"][q], wall_s=(time.time() - t0) / m); os.replace(f + ".tmp.npz", f)
    print("%s %s: %.0f s each" % (JOB, todo, (time.time() - t0) / m), flush=True)
print("done", JOB)
