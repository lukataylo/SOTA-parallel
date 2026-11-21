"""Baselines B0-B3 and the harness re-verification.   python baselines.py"""
import time, os, numpy as np, torch, torch.nn.functional as F, jax, jax.numpy as jnp
import flood_exp as fx, harness as H


def coarse_predict(z, K, res=12):
    """B2: solver on a 4x coarser grid, bilinear upsample of depth."""
    o = fx.solve_batch(z, K, res)
    up = lambda a: F.interpolate(torch.as_tensor(a)[:, None], size=fx.NF, mode="bilinear", align_corners=False)[:, 0].numpy()
    return up(o["hmax"]), up(o["hfin"])


def solver_timing(d):
    """In-process (one XLA thread) and pooled solver timings, float32."""
    def best(f, n, reps=3):
        f(); ts = []
        for _ in range(reps):
            t0 = time.perf_counter(); f(); ts.append(time.perf_counter() - t0)
        return min(ts) / n
    z, K = d["z"], d["K"]; tg = np.full((256, 2), 24, np.int32); out = {}
    for res in (fx.NF, 12):
        zr = np.asarray(fx.pool(jnp.asarray(z), res)); t2 = np.full((256, 2), res // 2, np.int32)
        one = jax.jit(fx._solve_one); vm = jax.jit(jax.vmap(fx._solve_one))
        out[f"res{res}_single_s"] = best(lambda: one(zr[0], K[0], t2[0])["hmax"].block_until_ready(), 1)
        out[f"res{res}_vmap256_s"] = best(lambda: vm(zr, K, t2)["hmax"].block_until_ready(), 256)
        out[f"res{res}_pool{fx.WORKERS}x64_s"] = best(lambda: fx.solve_batch(z, K, res), 256)
    cs = fx.NF ** 2 * fx.grid(fx.NF)[2] * fx.N_OUT
    out["cell_steps_per_storm"] = cs
    for k in ("single", "vmap256", f"pool{fx.WORKERS}x64"):
        out[f"Mcell_steps_per_s_{k}"] = cs / out[f"res{fx.NF}_{k}_s"] / 1e6
    return out


def make_b3(s):
    m, t, _ = H.cached_unet("B3", s, lambda: (*H.fit_unet(H.train_fractal(), s, epochs=40, log=f"B3 s{s}"), None))
    return H.predictor(m), dict(train_s=t, labels=2000, params=H.nparams(m))


if __name__ == "__main__":
    ts = H.testsets()
    # --- re-verify the earlier search claim, now under the cap: gradient search vs best of 1,024 random storms
    tt = ts["T_tail"]; z0, tg0 = tt["z"][0], tt["tgt"][0]
    Kr = np.asarray(fx.make_storms(jax.random.PRNGKey(77), 1024))
    hr = fx.solve_batch(np.tile(z0, (1024, 1, 1)), Kr, tgt=np.tile(tg0, (1024, 1)))["hmax"][:, tg0[0], tg0[1]]
    sd = tt["search_depth"]            # (25 iters, 64 terrains)
    ver = dict(terrain0_search_depth_m=float(sd[:, 0].max()), terrain0_best_of_1024_random_m=float(hr.max()),
               terrain0_random_median_m=float(np.median(hr)), search_iter0_mean_m=float(sd[0].mean()),
               search_iter24_mean_m=float(sd[24].mean()), search_wall_s=float(tt["search_s"]),
               note="64 searches x 25 Adam steps, batched; equal volume, peak <= cap")
    print("[verify]", ver, flush=True)
    H.save("harness", ver)
    # --- B0 / B1: the solver itself (error is zero by definition; timings only)
    tm = solver_timing(ts["T_iid"]); print("[B0/B1]", tm, flush=True)
    H.save("B0", dict(timing=dict(b1=tm["res48_single_s"]), detail=tm, note="fine solver, single storm, one CPU thread; ground truth"))
    H.save("B1", dict(timing=dict(b256=min(tm["res48_vmap256_s"], tm[f"res48_pool{fx.WORKERS}x64_s"])), detail=tm,
                      note=f"fine solver, batch 256: best of in-process vmap and {fx.WORKERS}-process pool of vmapped chunks"))
    # --- B2
    ev = H.evaluate(coarse_predict, ts); print("[B2]", {k: round(v["rmse_all"], 4) for k, v in ev.items()}, flush=True)
    H.plot_examples("B2", coarse_predict, ts["T_iid"])
    H.save("B2", dict(per_seed=[ev], summary=H.summarise([ev]), labels=0, train_s=0,
                      timing=dict(b1=tm["res12_single_s"], b256=min(tm["res12_vmap256_s"], tm[f"res12_pool{fx.WORKERS}x64_s"])),
                      note="deterministic, so one run; timing excludes the (negligible) upsample"))
    # --- B3: plain U-Net, MSE, random storms on one terrain kind
    H.train_fractal()
    H.run_many({"B3": make_b3}, extra=dict(note="2,000 storms, each on a fresh fractal terrain; seeds vary init and batch order"))
