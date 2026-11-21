"""Collate results/*/metrics.json into results/table.md, speedup.png, failure_map.png, and score the
saved models on the real-terrain set.
  FLOOD_DEVICE=cpu python report.py time   # quiet-machine CPU timings (solver + emulators, 1 thread) -> results/timings_cpu.json
  python report.py time                    # emulator timings on the Apple GPU -> results/timings_mps.json
  python report.py        # tables and figures
"""
import os, sys, json, time, numpy as np, torch, jax, jax.numpy as jnp
import flood_exp as fx, harness as H

SETS = ("T_iid", "T_tail", "T_terrain")
MET = ("rmse_all", "rmse_wet", "csi_0.1", "csi_0.3", "tail_rmse", "mass_err")
# row -> (results dir, path to the {set: {metric: {median,min,max}}} block, timing key in timings.json, emulator passes per storm)
ROWS = {
    "B0 solver, single": ("B0", None, "solver_single", 1), "B1 solver, batched": ("B1", None, "solver_batch", 1),
    "B2 coarse solver + upsample": ("B2", ("summary",), "coarse", 1), "B3 U-Net 2M": ("B3", ("summary",), "unet2m", 1),
    "E1 adversarial AL": ("E1", ("summary",), "small", 4), "E1 control (random)": ("E1_control", ("summary",), "small", 4),
    "E2 multi-terrain": ("E2", ("summary",), "unet2m", 1), "E2 + curriculum": ("E2_curriculum", ("summary",), "unet2m", 1),
    "E3 corrector": ("E3", ("summary",), "e3", 1),
    "E4 stage 1 (regression)": ("E4", ("summary", "*", "stage1"), "small+coarse", 1), "E4 diffusion members": ("E4", ("summary", "*", "member_mean"), "small+coarse", 21),
    "E5 fine-tune, 100 labels": ("E5", ("summary", "finetune_100"), "small", 1), "E5 scratch, 100 labels": ("E5", ("summary", "scratch_100"), "small", 1),
    "E5 fine-tune, 500 labels": ("E5", ("summary", "finetune_500"), "small", 1),
    "E8 (a) all fine, B=400": ("E8", ("a_all_fine_B400", "summary"), "small", 1), "E8 (b) 90/10 mix, B=400": ("E8", ("b_fixed_90_10_B400", "summary"), "small", 1),
    "E8 (c) adaptive, B=400": ("E8", ("c_adaptive_B400", "summary"), "small", 1),
}


def load(exp):
    p = os.path.join(H.RES, exp, "metrics.json")
    return json.load(open(p)) if os.path.exists(p) else None


def block(exp, path):
    d = load(exp)
    if d is None or path is None:
        return None
    if "*" in path:                                    # E4: summary[set][variant]
        return {s: d["summary"][s][path[-1]] for s in SETS}
    for k in path:
        d = d[k]
    return d


def fmt(x, rng=False):
    if x is None:
        return ""
    if not isinstance(x, dict):
        return f"{x:.3g}"
    return f"{x['median']:.3f} [{x['min']:.3f}-{x['max']:.3f}]" if rng else f"{x['median']:.3f}"


def timings():
    """One quiet session. CPU file: solver in-process (XLA threads) and 4-process pool, emulators on 1 thread. MPS file: emulators only."""
    from baselines import solver_timing
    import e3
    d = H.testsets()["T_iid"]; t = {}
    if H.DEV.type == "cpu":
        st = solver_timing(d); t = dict(solver_detail=st)
        t["solver_single"] = dict(b1=st["res48_single_s"]); t["solver_batch"] = dict(b256=min(st["res48_vmap256_s"], st[f"res48_pool{fx.WORKERS}x64_s"]))
        t["coarse"] = dict(b1=st["res12_single_s"], b256=min(st["res12_vmap256_s"], st[f"res12_pool{fx.WORKERS}x64_s"]))
        t["e3"] = H.time_per_storm(e3.predictor(e3.init(jax.random.PRNGKey(0))), d)
    t["unet2m"] = H.time_per_storm(H.predictor(H.UNet().eval()), d); t["small"] = H.time_per_storm(H.predictor(H.UNet(w=H.SMALL).eval()), d)
    json.dump(dict(t, hardware=H.HW, device=H.DEV.type), open(os.path.join(H.RES, f"timings_{H.DEV.type}.json"), "w"), indent=1); print(json.dumps(t, indent=1))


def storm_grid():
    """Failure-map data: fractal terrains at set roughness x storms at set contrast, 24 each, solver-labelled."""
    p = os.path.join(H.DATA, "failure_grid.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    R, A, n = (0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 1.4), (0.0, 0.5, 1.0, 2.0, 3.0, 4.5), 24; key = jax.random.PRNGKey(4040); z, K, ri, ai = [], [], [], []
    for i, r in enumerate(R):
        for j, a in enumerate(A):
            k = jax.random.fold_in(key, i * 10 + j); z.append(np.asarray(fx.make_terrains(k, "fractal", n, r)))
            K.append(np.asarray(jax.vmap(lambda q: fx.make_storm(q, a))(jax.random.split(jax.random.fold_in(k, 1), n)))); ri += [i] * n; ai += [j] * n
    d = dict(H.label(np.concatenate(z), np.concatenate(K)), ri=np.array(ri), ai=np.array(ai), R=np.array(R), A=np.array(A))
    np.savez(p, **d); return d


def unet(name, s):
    m = H.UNet(); m.load_state_dict(torch.load(os.path.join(H.DATA, f"{name}_{s}.pt"))); return H.predictor(m.eval())


if __name__ == "__main__":
    if sys.argv[1:] == ["time"]:
        raise SystemExit(timings())
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from baselines import coarse_predict
    T = json.load(open(os.path.join(H.RES, "timings_cpu.json"))); G = json.load(open(os.path.join(H.RES, "timings_mps.json")))
    T["small+coarse"] = {k: T["small"][k] + T["coarse"][k] for k in ("b1", "b256")}; G["small+coarse"] = {k: G["small"][k] + T["coarse"][k] for k in ("b1", "b256")}
    b0, b1 = T["solver_single"]["b1"], T["solver_batch"]["b256"]
    status = json.load(open(os.path.join(H.HERE, "status.json"))) if os.path.exists(os.path.join(H.HERE, "status.json")) else {}
    # ---- master table
    L = ["| Row | " + " | ".join(f"{s} {m}" for s in SETS for m in MET) + " | CPU s/storm b1 | CPU s/storm b256 | x vs B0 (b1, CPU) | x vs B1 (b256, CPU) | GPU s/storm b256 | x vs B1 (GPU emulator vs CPU solver) | labels | train s | status |",
         "|" + "---|" * (len(SETS) * len(MET) + 10)]
    pts = []
    for row, (exp, path, tk, passes) in ROWS.items():
        d, b = load(exp), block(exp, path)
        if d is None:
            L.append(f"| {row} |" + " |" * (len(SETS) * len(MET) + 8) + f" {status.get(row.split()[0], 'NOT RUN')} |"); continue
        cells = [fmt(b[s][m]) if b else ("0" if row[:2] in ("B0", "B1") else "") for s in SETS for m in MET]
        t1, t256 = (T[tk].get("b1"), T[tk].get("b256")); t1, t256 = (t1 * passes if t1 else None), (t256 * passes if t256 else None)
        ps = d.get("per_seed", [{}]); lab = ps[0].get("labels", d.get("labels", "")); tr = np.median([p["train_s"] for p in ps]) if "train_s" in ps[0] else ""
        if exp == "E5":
            lab = row.split(",")[1].strip().split()[0] + (f" (+{ps[0]['pretrain_labels']} pretrain)" if "fine-tune" in row else ""); tr = ""
        if exp == "E8":
            lab = f"{ps and d[path[0]]['per_seed'][0]['n_fine']} fine + {d[path[0]]['per_seed'][0]['n_coarse']} coarse"; tr = np.median([p["train_s"] for p in d[path[0]]["per_seed"]])
        g256 = G[tk]["b256"] * passes if tk in G else None
        L.append(f"| {row} | " + " | ".join(cells) + f" | {fmt(t1)} | {fmt(t256)} | {fmt(b0 / t1) if t1 else ''} | {fmt(b1 / t256) if t256 else ''} | {fmt(g256)} | {fmt(b1 / g256) if g256 else ''} | {lab} | {fmt(tr) if tr != '' else ''} | {status.get(row.split()[0], '')} |")
        if b and t256:
            pts.append((row, t256, b["T_iid"]["rmse_all"]))
    for e in ("E6", "E7", "E9", "E10"):
        L.append(f"| {e} (own metrics, see text) |" + " |" * (len(SETS) * len(MET) + 8) + f" {status.get(e, 'NOT RUN' if load(e) is None else '')} |")
    out = ["## Master table (medians of 3 seeds; ranges in the per-set tables)", "",
           f"Config: {H.CAPTION}. Hardware: {H.HW}. Timings: quiet sessions; CPU columns are like for like (solver and emulator both on CPU, emulator on 1 thread); "
           "the GPU columns put the emulator on the Apple GPU against the CPU solver, which is not like for like. b1 = batch 1, b256 = batch 256. Multi-pass rows (E1 x4 members, E4 x21 network passes + one coarse solve) are derived from the per-pass timing.", "", *L, ""]
    for s in SETS:
        out += [f"## {s}: median [min-max] over 3 seeds", "", "| Row | " + " | ".join(MET) + " |", "|" + "---|" * (len(MET) + 1)]
        out += [f"| {row} | " + " | ".join(fmt(b[s][m], True) for m in MET) + " |" for row, (exp, path, _, _) in ROWS.items() if (b := block(exp, path))]
        out.append("")
    # ---- real terrain + by-kind for the saved 2M models
    real = H.real_set(); rr = {"B2 coarse solver + upsample": [H.metrics(*coarse_predict(real["z"], real["K"]), real)]}
    for name, lab in (("B3", "B3 U-Net 2M"), ("E2", "E2 multi-terrain"), ("E2_curriculum", "E2 + curriculum")):
        if os.path.exists(os.path.join(H.DATA, f"{name}_0.pt")):
            rr[lab] = [H.metrics(*unet(name, s)(real["z"], real["K"]), real) for s in H.SEEDS]
    rs = {k: H.summarise(v) for k, v in rr.items()}; H.save("T_real", dict(summary=rs, peak_depth_mean_of_max_m=float(real["hmax"].max((1, 2)).mean())))
    out += ["## T_real (Blackfriars Road LiDAR, 256 random storms): median [min-max]", "", "| Row | " + " | ".join(MET) + " |", "|" + "---|" * (len(MET) + 1)]
    out += [f"| {k} | " + " | ".join(fmt(v[m], True) for m in MET) + " |" for k, v in rs.items()] + [""]
    open(os.path.join(H.RES, "table.md"), "w").write("\n".join(out)); print("\n".join(out))
    # ---- speedup.png
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for row, t, r in pts:
        ax.errorbar(t, r["median"], yerr=[[r["median"] - r["min"]], [r["max"] - r["median"]]], marker="o", capsize=2); ax.annotate(row, (t, r["median"]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.axvline(b1, color="k", ls="--", lw=0.8); ax.annotate("B1 fine solver, batched\n(error 0 by definition)", (b1, ax.get_ylim()[1]), fontsize=6, ha="right", va="top", rotation=90)
    ax.axvline(b0, color="grey", ls=":", lw=0.8); ax.annotate("B0 fine solver, single", (b0, ax.get_ylim()[1]), fontsize=6, ha="right", va="top", rotation=90)
    ax.set_xscale("log"); ax.set_xlabel("wall-clock seconds per storm, batch 256, CPU"); ax.set_ylabel("T_iid RMSE of peak depth (m), median and range of 3 seeds")
    ax.set_title(f"Accuracy against cost. {H.CAPTION}\n{H.HW}", fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(H.RES, "speedup.png"), dpi=130)
    # ---- failure_map.png: best 2M emulator by T_iid
    cand = [n for n in ("B3", "E2", "E2_curriculum") if load(n)]; best = min(cand, key=lambda n: load(n)["summary"]["T_iid"]["rmse_all"]["median"])
    g = storm_grid(); pk = np.mean([unet(best, s)(g["z"], g["K"])[0] for s in H.SEEDS], 0); nr, na = len(g["R"]), len(g["A"])
    cell = lambda f: np.array([[f((g["ri"] == i) & (g["ai"] == j)) for j in range(na)] for i in range(nr)])
    rm = cell(lambda s: np.sqrt(((pk[s] - g["hmax"][s]) ** 2).mean())); dep = cell(lambda s: np.sort(g["hmax"][s].reshape(s.sum(), -1), 1)[:, -23:].mean())
    tl = cell(lambda s: np.sqrt(np.take_along_axis(((pk[s] - g["hmax"][s]) ** 2).reshape(s.sum(), -1), np.argsort(g["hmax"][s].reshape(s.sum(), -1), 1)[:, -23:], 1).mean()))
    pkmm = [float(np.median(np.quantile(np.asarray(jax.vmap(fx.rain_field)(jnp.asarray(g["K"][g["ai"] == j]))).reshape((g["ai"] == j).sum(), -1), 0.99, 1)) * 3.6e6) for j in range(na)]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for a, (m, ttl) in zip(ax, ((rm, "RMSE, all cells (m)"), (tl, "RMSE, deepest 1% of cells (m)"), (tl / dep, "deepest-1% RMSE / true mean depth of those cells"))):
        im = a.imshow(m, origin="lower", cmap="magma", aspect="auto"); fig.colorbar(im, ax=a)
        a.set_xticks(range(na), [f"{x:.0f}" for x in pkmm]); a.set_yticks(range(nr), [f"{r:.1f}" for r in g["R"]])
        a.set_xlabel("storm 99th-percentile intensity (mm/h); volume fixed"); a.set_ylabel("terrain roughness parameter"); a.set_title(ttl, fontsize=9)
        a.add_patch(plt.Rectangle((0.5, 0.5), 3, 4, fill=False, ec="cyan", lw=1.5, ls="--"))
        for i in range(nr):
            for j in range(na):
                a.text(j, i, f"{m[i, j]:.2f}" if m[i, j] < 10 else f"{m[i, j]:.0f}", ha="center", va="center", fontsize=6, color="w" if m[i, j] < m.max() * 0.6 else "k")
    fig.suptitle(f"Failure map of {best} (mean of 3 seeds) on fractal terrain, 24 storms per cell. Dashed box: roughly the training range. {H.CAPTION}", fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(H.RES, "failure_map.png"), dpi=130)
    H.save("failure_map", dict(model=best, rmse=rm.tolist(), tail_rmse=tl.tolist(), true_tail_depth=dep.tolist(), roughness=g["R"].tolist(), contrast=g["A"].tolist(), p99_mm_h=pkmm))
