"""The complete solver map: every open 5 x 5 m block of the tile raised or lowered 5 cm, packed 150 m apart. See docs/G_CRITERIA.md.
uv run --with mlx --with numpy python fill/map_run.py <raise|lower> <machine: air|pro> [forward|reverse] [colour ids to run first ...]
One file per colour in results/<machine>/map/s1_<sign>/. Resumable: existing colours (from either machine) are skipped."""
import sys, os, time, glob, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
SIGN, MACH = sys.argv[1], sys.argv[2]; DIRN = sys.argv[3] if len(sys.argv) > 3 else "forward"; FIRST = [int(a) for a in sys.argv[4:]]
P, S, DZ = 30, 1, (0.05 if SIGN == "raise" else -0.05)                    # period 30 blocks = 150 m; storm index 1 = 35 mm
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
out = f"results/{MACH}/map/s{S}_{SIGN}"; fld = f"data/raw/map_fields/s{S}_{SIGN}"; os.makedirs(out, exist_ok=True); os.makedirs(fld, exist_ok=True)
def terrain(col):
    zc = z.copy()
    if col < 0: return zc                                                # -1: the unchanged terrain
    for i in range(col // P or P, 101, P):
        for j in range(col % P or P, 101, P):
            sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], DZ, 0).astype(np.float32)
    return zc
def done(col): return any(os.path.exists(f"results/{m}/map/s{S}_{SIGN}/c{col:03d}.npz") for m in ("air", "pro"))
def run(cols, tag=None):
    m = len(cols); t0 = time.time()
    o = simulate(np.array([terrain(c) for c in cols]), op, dx, rc, np.repeat(d["profile"][S][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32), return_fields=True)
    w = (time.time() - t0) / m
    for k, c in enumerate(cols):
        f = f"{out}/{tag or 'c%03d' % c}.npz"; np.savez(f + ".tmp.npz", colour=c, peak=o["peak_depth"][k], imbalance=o["imbalance"][k], wall_s=w); os.replace(f + ".tmp.npz", f)
        if c >= 0: np.save(f"{fld}/c{c:03d}.npy", o["peak_field"][k].astype(np.float16))
    print("%s: %d terrains, %.0f s each" % (tag or cols, m, w), flush=True)
order = list(np.random.default_rng(2026).permutation(P * P)); order = order[::-1] if DIRN == "reverse" else order
order = FIRST + [c for c in order if c not in FIRST]
if not os.path.exists(f"{out}/base_start.npz"): run([-1], "base_start")
while True:
    todo = [c for c in order if not done(c)][:6]
    if not todo: break
    run(todo)
run([-1], "base_end"); print("done")
