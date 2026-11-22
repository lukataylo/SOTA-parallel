"""Run packed colours of the solver map on rented GPUs. See docs/G_CRITERIA.md (cloud GPU scaling).
uv run --with modal --with numpy modal run cloud/modal_map.py --mode check          (unchanged run + 5 colours, compare with the laptop)
uv run --with modal --with numpy modal run cloud/modal_map.py --mode scale --gpus 1,2,4,8"""
import modal, time, json, numpy as np
GPU, NRUN, BATCH, P = "A100", 240, 30, 30
image = (modal.Image.debian_slim(python_version="3.11").pip_install("torch==2.5.1", "numpy").add_local_file("shared/terrain_512.npz", "/d/terrain.npz")
         .add_local_file("shared/receptors.npz", "/d/receptors.npz").add_local_file("shared/p1_cases.npz", "/d/cases.npz").add_local_file("cloud/flood_torch.py", "/root/flood_torch.py"))
app = modal.App("flood-map", image=image)
@app.function(gpu=GPU, timeout=3600)
def run(cols, warm=True):
    import torch, sys; sys.path.insert(0, "/root"); from flood_torch import simulate
    t = np.load("/d/terrain.npz"); d = np.load("/d/cases.npz"); rc = np.load("/d/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
    def terrain(c):
        zc = z.copy()
        if c >= 0:
            for i in range(c // P or P, 101, P):
                for j in range(c % P or P, 101, P): sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], 0.05, 0).astype(np.float32)
        return zc
    sim = lambda cs: simulate(np.array([terrain(c) for c in cs]), op, dx, rc, np.repeat(d["profile"][1][None], len(cs), 0), float(d["profile_dt_s"]), np.full(len(cs), float(d["loss_mm_h"])), np.full(len(cs), float(d["t_end_s"])))
    if warm: simulate(np.array([z]), op, dx, rc, d["profile"][1][None], float(d["profile_dt_s"]), np.full(1, 12.0), np.full(1, 60.0))   # one simulated minute, to load CUDA
    t0 = time.time(); pk, imb, steps = [], [], 0
    for a in range(0, len(cols), BATCH): o = sim(cols[a:a + BATCH]); pk.append(o["peak_depth"]); imb.append(o["imbalance"]); steps += o["steps"]
    return dict(cols=list(cols), peak=np.concatenate(pk), imbalance=np.concatenate(imb), solve_s=time.time() - t0, steps=steps, gpu=torch.cuda.get_device_name(0))
def laptop(c):
    import os
    for m in ("air", "pro"):
        f = f"results/{m}/map/s1_raise/" + ("base_start.npz" if c < 0 else "c%03d.npz" % c)
        if os.path.exists(f): return np.load(f)["peak"].astype(float)
@app.local_entrypoint()
def main(mode: str = "check", gpus: str = "1,2,4,8"):
    order = [int(c) for c in np.random.default_rng(2026).permutation(P * P)][:NRUN]
    if mode == "check":
        r = run.remote([-1] + order[:5], False); dif = [np.abs(r["peak"][k] - laptop(c)).max() for k, c in enumerate(r["cols"])]
        print("%s: %d terrains in %.1f s (%.1f s each, %d steps); largest difference from the laptop at a receptor, mm: %s; worst imbalance %.1e" % (r["gpu"], len(dif), r["solve_s"], r["solve_s"] / len(dif), r["steps"], np.round(1000 * np.array(dif), 3).tolist(), np.abs(r["imbalance"]).max())); return
    out = []
    for n in [int(g) for g in gpus.split(",")]:
        chunks = [order[k::n] for k in range(n)]; t0 = time.time(); res = list(run.map(chunks)); wall = time.time() - t0
        dif = max(np.abs(r["peak"][k] - laptop(c)).max() for r in res for k, c in enumerate(r["cols"])); imb = max(np.abs(r["imbalance"]).max() for r in res); solve = max(r["solve_s"] for r in res)
        out.append(dict(gpus=n, runs=NRUN, wall_with_start_s=wall, solve_s=solve, gpu_seconds=sum(r["solve_s"] for r in res), max_diff_mm=1000 * dif, max_imbalance=imb, gpu=res[0]["gpu"]))
        print(json.dumps(out[-1]), flush=True); json.dump(out, open("results/cloud/scaling_%s.json" % GPU, "w"), indent=1)
        np.savez("results/cloud/peaks_%d.npz" % n, cols=np.concatenate([r["cols"] for r in res]), peak=np.concatenate([r["peak"] for r in res]))
