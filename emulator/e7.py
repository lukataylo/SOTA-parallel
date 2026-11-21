"""E7: CRPS-trained ensemble emulator against terrain-perturbed solver runs.   python e7.py"""
import os, time, numpy as np, torch, jax
import flood_exp as fx, harness as H

NTR, NTE, MTR, MTE, MGEN = 200, 64, 8, 16, 16      # storms x perturbed-terrain members (train 200x8, test 64x16)
SIGMAS = (0.05, 0.02, 0.10)                         # phone-scan elevation error, m; iid per 10 m cell (assumed)


def perturbed(name, n, m, sigma, seed):
    p = os.path.join(H.DATA, f"{name}_{int(sigma*100)}cm.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    key = jax.random.PRNGKey(seed); z = np.asarray(fx.make_terrains(key, "fractal", n)); K = np.asarray(fx.make_storms(jax.random.fold_in(key, 1), n))
    zp = z[:, None] + sigma * np.random.default_rng(seed).standard_normal((n, m) + z.shape[1:]).astype(np.float32)
    o = fx.solve_batch(zp.reshape(-1, *z.shape[1:]), np.repeat(K, m, 0))
    d = dict(z=z, K=K, hmax=o["hmax"].reshape(n, m, *z.shape[1:]), hfin=o["hfin"].reshape(n, m, *z.shape[1:]))
    np.savez(p, **d); return d


def crps(x, y):
    """Fair per-cell CRPS. x (m,B,H,W) members, y (B,H,W) one solver member."""
    m = len(x)
    return ((x - y).abs().mean(0) - (x[:, None] - x[None]).abs().sum((0, 1)) / (2 * m * (m - 1))).mean()


def members(model, z, K, m, g):
    x = H.feats(z, K)
    return torch.stack([model(torch.cat([x, torch.randn(len(x), 1, *x.shape[2:], generator=g).to(x.device)], 1)) for _ in range(m)])


def calibration(pe, te, thr=0.1):
    """pe, te: (n, m, H, W) emulator / solver member peak depths."""
    p, o = (pe > thr).mean(1).ravel(), (te > thr).mean(1).ravel()
    b = np.minimum((p * 10).astype(int), 9); rel = []
    for i in range(10):
        s = b == i
        if s.sum() >= 200:                                               # skip near-empty bins
            rel.append(dict(bin=i, pred=float(p[s].mean()), obs=float(o[s].mean()), n=int(s.sum())))
    m = pe.shape[1]; spread = np.sqrt((pe.var(1, ddof=1) * (m + 1) / m).mean())
    skill = np.sqrt(((pe.mean(1) - te[:, 0]) ** 2).mean())
    return dict(reliability=rel, max_dev=float(max(abs(r["pred"] - r["obs"]) for r in rel)), spread=float(spread), rmse=float(skill),
                spread_skill=float(spread / skill), brier=float(((p - (te[:, 0] > thr).ravel()) ** 2).mean()),
                brier_climatology=float((((te > thr).mean() - (te[:, 0] > thr).ravel()) ** 2).mean()))


def job(a):
    sigma, seed = a
    tr = perturbed("e7_train", NTR, MTR, sigma, 70); te = perturbed("e7_test", NTE, MTE, sigma, 71)
    Y = torch.as_tensor(np.stack([tr["hmax"], tr["hfin"]], 2)).to(H.DEV) * H.OUT_SCALE     # (n, m, 2, H, W)
    torch.manual_seed(seed); g = torch.Generator().manual_seed(seed); model = H.UNet(cin=10, w=H.SMALL)
    opt = torch.optim.AdamW(model.parameters(), 1e-3); t0 = time.time()
    for ep in range(60):
        perm = torch.randperm(NTR, generator=g)
        for i in range(0, NTR, 16):
            j = perm[i:i + 16]; y = Y[j.to(H.DEV), torch.randint(MTR, (len(j),), generator=g).to(H.DEV)]
            loss = crps(members(model, tr["z"][j.numpy()], tr["K"][j.numpy()], 4, g), y); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        pe = members(model.eval(), te["z"], te["K"], MGEN, torch.Generator().manual_seed(99)).clamp(min=0).cpu().numpy()[:, :, 0].transpose(1, 0, 2, 3) / H.OUT_SCALE
    c = calibration(pe, te["hmax"]); c["train_s"] = time.time() - t0
    print(f"[E7] sigma {sigma*100:.0f} cm seed {seed}: reliability max dev {c['max_dev']:.3f}, spread/skill {c['spread_skill']:.2f}, "
          f"brier {c['brier']:.4f} (climatology {c['brier_climatology']:.4f})", flush=True)
    return c


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    for sg in SIGMAS:
        perturbed("e7_train", NTR, MTR, sg, 70); perturbed("e7_test", NTE, MTE, sg, 71)
    jobs = [(sg, s) for sg in SIGMAS for s in (H.SEEDS if sg == 0.05 else H.SEEDS[:1])]; res = H.pmap(job, jobs)
    out = {}; fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    for si, sigma in enumerate(SIGMAS):
        te = perturbed("e7_test", NTE, MTE, sigma, 71); per = [r for (sg, _), r in zip(jobs, res) if sg == sigma]
        for k, c in enumerate(per):
            ax[si].plot([r["pred"] for r in c["reliability"]], [r["obs"] for r in c["reliability"]], "o-", label=f"seed {k}")
        ev = (te["hmax"] > 0.1).mean(1)                    # how much does terrain noise matter at all, in the solver itself?
        out[f"sigma_{int(sigma*100)}cm"] = dict(per_seed=per, summary=H.summarise(per), solver_member_std_m=float(te["hmax"].std(1).mean()),
                                               solver_event_uncertain_frac=float(((ev > 0) & (ev < 1)).mean()))
        ax[si].plot([0, 1], [0, 1], "k--", lw=0.8); ax[si].fill_between([0, 1], [-0.1, 0.9], [0.1, 1.1], alpha=0.1)
        ax[si].set_title(f"terrain noise sigma = {sigma*100:.0f} cm", fontsize=9); ax[si].set_xlabel("emulator P(depth > 0.1 m)"); ax[si].set_ylabel("solver-ensemble frequency"); ax[si].legend(fontsize=7)
    fig.suptitle(f"E7 reliability, event peak depth > 0.1 m; band is +/-0.1 ({H.CAPTION})", fontsize=9); fig.tight_layout()
    os.makedirs(os.path.join(H.RES, "E7"), exist_ok=True); fig.savefig(os.path.join(H.RES, "E7", "reliability.png"), dpi=110)
    H.save("E7", dict(out, labels=NTR * MTR, note=f"{NTR} storms x {MTR} perturbed-terrain solver members per sigma; small U-Net with a noise channel; "
                      f"{MGEN} generated members at test; 3 seeds at 5 cm, 1 seed at 2 and 10 cm"))
