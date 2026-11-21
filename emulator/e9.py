"""E9: amortised inversion. Recover storm + drain parameters from sparse noisy peak depths with a
mixture density network, one forward pass.   python e9.py"""
import os, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F, jax, jax.numpy as jnp
import flood_exp as fx, harness as H

NSIM, NTEST, R = 20000, 1000, 24               # 24x24 grid (half the fine grid) keeps this on CPU
NAMES = ("centre_x", "centre_y", "spread", "peak_time_s", "volume_mm", "drain_mm_h")
LO = np.array([0.15, 0.15, 0.08, 300., 10., 0.]); HI = np.array([0.85, 0.85, 0.30, 1500., 40., 30.])   # uniform prior
OBS_SIGMA, NC = 0.01, 5                         # 1 cm observation noise; mixture components


def storm_knots(th):
    """Gaussian cell in space and time on the knot grid, scaled to the requested volume under the cap."""
    g = (jnp.arange(fx.KS) + 0.5) / fx.KS; t = (jnp.arange(fx.NK) + 0.5) * fx.T_RAIN / fx.NK
    sp = jnp.exp(-((g[None, :] - th[0]) ** 2 + (g[:, None] - th[1]) ** 2) / (2 * th[2] ** 2))
    return fx.project(jnp.exp(-((t - th[3]) / 300.) ** 2)[:, None, None] * sp[None] + 1e-6, th[4] * 1e-3)


def simulate():
    p = os.path.join(H.DATA, "e9_sims.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    th = np.random.default_rng(9).uniform(LO, HI, (NSIM + NTEST, 6)).astype(np.float32)
    z = np.asarray(fx.make_terrain(jax.random.PRNGKey(909), "fractal"))
    K = np.asarray(jax.vmap(storm_knots)(jnp.asarray(th))); t0 = time.time()
    o = fx.solve_batch(np.broadcast_to(z, (len(th),) + z.shape), K, R, drain=th[:, 5] * 1e-3 / 3600)
    d = dict(theta=th, hmax=o["hmax"], z=z, solve_s=time.time() - t0,
             vol_delivered_mm=np.asarray(jax.vmap(lambda k: fx.rain_field(k).mean() * fx.T_RAIN)(jnp.asarray(K))) * 1e3)
    np.savez(p, **d); print(f"[E9] simulated {len(th)} in {d['solve_s']:.0f}s", flush=True)
    return d


def observe(hmax, g):
    """10-30 random cells per sample -> 2-channel image (noisy depth in dm, mask)."""
    B = len(hmax); n = torch.randint(10, 31, (B, 1), generator=g)
    mask = (torch.rand(B, R * R, generator=g).argsort(1).argsort(1) < n).float().view(B, R, R)
    return torch.stack([(hmax + OBS_SIGMA * torch.randn(hmax.shape, generator=g)) * 10 * mask, mask], 1)


class MDN(nn.Module):
    def __init__(s, w=48):
        super().__init__()
        s.cnn = nn.Sequential(nn.Conv2d(2, w, 5, padding=2), nn.SiLU(), nn.Conv2d(w, w, 3, padding=1), nn.SiLU(), nn.MaxPool2d(2),
                              nn.Conv2d(w, 2 * w, 3, padding=1), nn.SiLU(), nn.MaxPool2d(2), nn.Conv2d(2 * w, 2 * w, 3, padding=1), nn.SiLU(),
                              nn.Flatten(), nn.Linear(2 * w * 36, 256), nn.SiLU(), nn.Linear(256, NC * 13))
    def forward(s, x):
        o = s.cnn(x).view(-1, NC, 13)
        return o[..., 0], o[..., 1:7], o[..., 7:].clamp(-6, 2)          # logits, means, log-sigmas (in unit-prior coordinates)
    def nll(s, x, y):
        lg, mu, ls = s(x)
        lp = (-0.5 * ((y[:, None] - mu) / ls.exp()) ** 2 - ls - 0.9189).sum(-1) + F.log_softmax(lg, -1)
        return -torch.logsumexp(lp, -1).mean()
    @torch.no_grad()
    def sample(s, x, n, g):
        lg, mu, ls = s(x); c = torch.multinomial(F.softmax(lg, -1), n, replacement=True, generator=g)
        i = c[..., None].expand(-1, -1, 6)
        return mu.gather(1, i) + ls.exp().gather(1, i) * torch.randn(len(x), n, 6, generator=g)


def job(seed):
    d = simulate(); u = torch.as_tensor((d["theta"] - LO) / (HI - LO), dtype=torch.float32); hm = torch.as_tensor(d["hmax"])
    torch.manual_seed(seed); g = torch.Generator().manual_seed(seed); m = MDN(); opt = torch.optim.AdamW(m.parameters(), 1e-3)
    ntr = NSIM - 500; t0 = time.time()                                   # last 500 training sims are the validation split
    for ep in range(20):
        perm = torch.randperm(ntr, generator=g)
        for i in range(0, ntr, 128):
            j = perm[i:i + 128]; loss = m.nll(observe(hm[j], g), u[j]); opt.zero_grad(); loss.backward(); opt.step()
        if ep % 5 == 4:
            with torch.no_grad():
                print(f"  [E9 s{seed}] ep {ep+1} train nll {loss.item():.3f} val nll {m.nll(observe(hm[ntr:NSIM], g), u[ntr:NSIM]).item():.3f} {time.time()-t0:.0f}s", flush=True)
    gt = torch.Generator().manual_seed(1234)                             # frozen test observations
    s = m.sample(observe(hm[NSIM:], gt), 500, gt); y = u[NSIM:]; q = {a: torch.quantile(s, a, dim=1) for a in (0.05, 0.25, 0.75, 0.95)}
    r = dict(train_s=time.time() - t0)
    for k, nm in enumerate(NAMES):
        pm = s[:, :, k].mean(1); inside = lambda lo, hi: float(((y[:, k] >= q[lo][:, k]) & (y[:, k] <= q[hi][:, k])).float().mean())
        r[nm] = dict(cover50=inside(0.25, 0.75), cover90=inside(0.05, 0.95),
                     post_rmse_over_prior_rmse=float(((pm - y[:, k]) ** 2).mean().sqrt() / ((0.5 - y[:, k]) ** 2).mean().sqrt()))
    print(f"[E9] seed {seed}:", {nm: (round(r[nm]['cover50'], 2), round(r[nm]['cover90'], 2), round(r[nm]['post_rmse_over_prior_rmse'], 2)) for nm in NAMES}, flush=True)
    return r, y[:300].numpy(), s[:300].mean(1).numpy()


if __name__ == "__main__":
    d = simulate(); res = H.pmap(job, list(H.SEEDS)); per = [r for r, _, _ in res]; _, y, pm = res[0]
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 6, figsize=(18, 3.2))
    for k, nm in enumerate(NAMES):
        ax[k].scatter(y[:, k] * (HI[k] - LO[k]) + LO[k], pm[:, k] * (HI[k] - LO[k]) + LO[k], s=4)
        ax[k].plot([LO[k], HI[k]], [LO[k], HI[k]], "k--", lw=0.8); ax[k].set_title(nm, fontsize=9); ax[k].set_xlabel("true"); ax[k].set_ylabel("posterior mean")
    fig.suptitle(f"E9: posterior mean vs truth, 300 held-out storms, 10-30 noisy depth observations each ({R}x{R} grid, one terrain, cap {fx.CAP*3.6e6:.0f} mm/h)", fontsize=9)
    fig.tight_layout(); os.makedirs(os.path.join(H.RES, "E9"), exist_ok=True); fig.savefig(os.path.join(H.RES, "E9", "posterior.png"), dpi=110)
    H.save("E9", dict(per_seed=per, summary=H.summarise(per), sims=NSIM, grid=R, solve_s=float(d["solve_s"]),
                      volume_clipped_frac=float((d["vol_delivered_mm"] < 0.99 * d["theta"][:, 4]).mean()),
                      note="one known fractal terrain; uniform priors; cap can clip a requested volume (fraction recorded)"))
