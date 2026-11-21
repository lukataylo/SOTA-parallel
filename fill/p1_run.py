"""P1 runner: every case in shared/p1_cases.npz at 3 storms, plus the unchanged terrain. Chunked and resumable.
uv run --with mlx --with numpy python fill/p1_run.py [forward|reverse] [outdir]
Two machines can share the work: one runs forward, the other reverse, writing the same chunk file names."""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
direction = sys.argv[1] if len(sys.argv) > 1 else "forward"; out = sys.argv[2] if len(sys.argv) > 2 else "results/air/p1_chunks"
os.makedirs(out, exist_ok=True)
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]
z, op, dx = t["z"], t["open"], float(t["dx"]); n = len(d["dz"]); B = 8
def run(terrains, s):
    m = len(terrains); rep = lambda x: np.repeat(np.asarray(x)[None], m, 0)
    o = simulate(np.array(terrains), op, dx, rc, rep(d["profile"][s]), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    return o["peak_depth"], o["final_depth"], o["imbalance"]
f = f"{out}/base.npz"
if not os.path.exists(f):
    pk, fn, im = [], [], []
    for s in range(3):
        a, b, c = run([z], s); pk.append(a[0]); fn.append(b[0]); im.append(c[0])
    np.savez(f + ".tmp.npz", peak=np.array(pk), final=np.array(fn), imbalance=np.array(im)); os.replace(f + ".tmp.npz", f); print("base done", flush=True)
blocks = list(range(0, n, B)); blocks = blocks[::-1] if direction == "reverse" else blocks
for c in blocks:
    for s in range(3):
        f = f"{out}/chunk_{c:04d}_s{s}.npz"
        if os.path.exists(f): continue
        ii = np.arange(c, min(c + B, n)); zs = []
        for i in ii:
            a, b, lo, hi = d["rect"][i]; zc = z.copy(); zc[a:b, lo:hi] += np.where(op[a:b, lo:hi], d["dz"][i], 0).astype(np.float32); zs.append(zc)
        t0 = time.time(); pk, fn, im = run(zs, s)
        np.savez(f + ".tmp.npz", case=ii, storm=s, peak=pk, final=fn, imbalance=im, wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f)
        print(f"cases {ii[0]}-{ii[-1]} storm {s}: {time.time() - t0:.0f}s", flush=True)
print("all done")
