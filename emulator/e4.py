"""E4: residual diffusion on top of a regression mean, conditioned on fine terrain.   python e4.py"""
import os, time, numpy as np, torch, torch.nn.functional as F
import flood_exp as fx, harness as H

STEPS, SAMPLE_STEPS, MEMBERS = int(os.environ.get("E4_STEPS", 4000)), 20, 8


def up(a):
    return F.interpolate(torch.as_tensor(a)[:, None], size=fx.NF, mode="bilinear", align_corners=False)


def cond(z, c):
    """coarse peak and final depth (bilinear, dm) + fine terrain."""
    z = torch.as_tensor(z); return torch.cat([up(c["hmax"]) * H.OUT_SCALE, up(c["hfin"]) * H.OUT_SCALE, ((z - z.mean((-1, -2), keepdim=True)) / 2)[:, None]], 1).to(H.DEV)


def abar(t):                          # cosine schedule, t in [0,1]
    return torch.cos(torch.as_tensor(t, dtype=torch.float32) * torch.pi / 2).clamp(1e-3, 1) ** 2


@torch.no_grad()
def sample(den, c, mean, scale, g):
    """DDIM, x0-prediction, SAMPLE_STEPS steps. Returns residual in dm."""
    x = torch.randn(len(c), 1, fx.NF, fx.NF, generator=g).to(c.device); ts = torch.linspace(1, 0, SAMPLE_STEPS + 1)
    for a, b in zip(ts[:-1], ts[1:]):
        x0 = den(torch.cat([x, c, mean, torch.full_like(x, float(a))], 1)); aa, ab = abar(a), abar(b)
        eps = (x - aa.sqrt() * x0) / (1 - aa).sqrt(); x = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
    return x0 * scale


def job(s):
    tr = H.train_fractal(); trc = H.dataset_fixed("train_fractal_c12", tr["z"], tr["K"], 12); ts = H.testsets()
    C, Y = cond(tr["z"], trc), H.targets(tr); torch.manual_seed(s); g = torch.Generator().manual_seed(s)
    reg = H.UNet(cin=3, w=H.SMALL); t1 = H.train(reg, C, Y, epochs=40, lr=H.LR_SMALL, seed=s); reg.eval()            # stage one: regression mean
    with torch.no_grad():
        M = reg(C)
    res = Y[:, :1] - M[:, :1]; scale = float(res.std()); den = H.UNet(cin=6, cout=1, w=H.SMALL); opt = torch.optim.AdamW(den.parameters(), 1e-3); t0 = time.time()
    for st in range(STEPS):                                                                         # stage two: diffusion on the peak-depth residual
        j = torch.randint(len(C), (32,), generator=g).to(H.DEV); t = torch.rand(32, 1, 1, 1, generator=g).to(H.DEV); x0 = res[j] / scale
        xt = abar(t).sqrt() * x0 + (1 - abar(t)).sqrt() * torch.randn(x0.shape, generator=g).to(H.DEV)
        loss = F.mse_loss(den(torch.cat([xt, C[j], M[j, :1], t.expand_as(xt)], 1)), x0); opt.zero_grad(); loss.backward(); opt.step()
    t2 = time.time() - t0; den.eval(); r = dict(train_s=t1 + t2, stage2_train_s=t2, labels=2000, residual_std_m=scale / H.OUT_SCALE)
    gs = torch.Generator().manual_seed(4242)
    for name, d in ts.items():
        c = cond(d["z"], fx.solve_batch(d["z"], d["K"], 12))
        with torch.no_grad():
            m = reg(c)
            mem = np.stack([((m[:, :1] + sample(den, c, m[:, :1], scale, gs)).clamp(min=0)[:, 0] / H.OUT_SCALE).cpu().numpy() for _ in range(MEMBERS)])
        m = m.clamp(min=0).cpu().numpy() / H.OUT_SCALE; per = [H.metrics(x, m[:, 1], d) for x in mem]
        r[name] = dict(stage1=H.metrics(m[:, 0], m[:, 1], d), member_mean={k: float(np.mean([p[k] for p in per])) for k in per[0]},
                       ensemble_mean=H.metrics(mem.mean(0), m[:, 1], d), member_spread_m=float(mem.std(0).mean()))
        if s == 0 and name == "T_iid":
            keep = (d, c, mem[0])
    a, b = r["T_iid"]["stage1"], r["T_iid"]["member_mean"]
    print(f"[E4] seed {s}: T_iid tail rmse stage1 {a['tail_rmse']:.4f} -> members {b['tail_rmse']:.4f}; csi0.3 {a['csi_0.3']:.3f} -> {b['csi_0.3']:.3f}", flush=True)
    if s == 0:
        d, c, m0 = keep; lut = {d["z"][i].tobytes(): m0[i] for i in range(3)}
        H.plot_examples("E4", lambda z, K: (np.stack([lut[x.tobytes()] for x in z]), None), d)        # member 0 for the first three test storms
        t0 = time.perf_counter(); sample(den, c, reg(c)[:, :1].detach(), scale, gs); r["_timing"] = dict(b256=(time.perf_counter() - t0) / 256, b1=float("nan"))
    return r


if __name__ == "__main__":
    tr = H.train_fractal(); H.dataset_fixed("train_fractal_c12", tr["z"], tr["K"], 12)
    per = H.pmap(job, list(H.SEEDS)); timing = per[0].pop("_timing")
    H.save("E4", dict(per_seed=per, summary=H.summarise(per), timing=timing, steps=STEPS, sample_steps=SAMPLE_STEPS, members=MEMBERS,
                      note="input is the 12x12 solver's peak/final depth + fine terrain (so each prediction also costs one coarse solve, not included in timing); "
                           "timing is one diffusion member, batch 256; 'member_mean' averages each metric over the 8 members"))
