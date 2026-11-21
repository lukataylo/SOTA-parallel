"""E6: in-context operator. A transformer sees a few solved storms on an unseen terrain (terrain itself
withheld) and predicts a new storm there, no weight update. 24x24 grid.   python e6.py"""
import os, time, numpy as np, torch, torch.nn as nn, jax
import flood_exp as fx, harness as H

R, NS, NTR, NTE, STEPS = 24, 6, 1200, 120, int(os.environ.get("E6_STEPS", 4000))
SHOTS = (0, 1, 3, 5)


def data(name, n, seed):
    p = os.path.join(H.DATA, f"{name}.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    key = jax.random.PRNGKey(seed)
    z = np.concatenate([np.asarray(fx.make_terrains(jax.random.fold_in(key, i), k, n // 3)) for i, k in enumerate(H.TRAIN_KINDS)])
    K = np.asarray(fx.make_storms(jax.random.fold_in(key, 9), n * NS))
    hm = fx.solve_batch(np.repeat(z, NS, 0), K, R)["hmax"]
    d = dict(K=K.reshape(n, NS, fx.NK, 36).transpose(0, 1, 3, 2) / fx.CAP,                       # (n, NS, 36 knots, 8 times)
             h=hm.reshape(n, NS, 6, 4, 6, 4).transpose(0, 1, 2, 4, 3, 5).reshape(n, NS, 36, 16) * H.OUT_SCALE)   # 4x4 depth patch per knot
    np.savez(p, **d); return d


class ICON(nn.Module):
    def __init__(s, d=128):
        super().__init__()
        s.inp = nn.Linear(8 + 16 + 1, d); s.pos = nn.Parameter(torch.zeros(36, d)); s.slot = nn.Parameter(torch.zeros(NS, d))
        s.tf = nn.TransformerEncoder(nn.TransformerEncoderLayer(d, 4, 256, dropout=0., batch_first=True, norm_first=True), 4)
        s.out = nn.Linear(d, 16)
    def forward(s, K, h, n_ctx):
        """K, h: (B, NS, 36, .); storms 0..n_ctx-1 are context (depth shown), storm n_ctx is the query."""
        B = len(K); q = torch.zeros(B, n_ctx + 1, 36, 1, device=K.device); q[:, -1] = 1
        x = torch.cat([K[:, :n_ctx + 1], h[:, :n_ctx + 1] * (1 - q), q], -1)
        x = s.inp(x) + s.pos + s.slot[:n_ctx + 1, None]
        return s.out(s.tf(x.flatten(1, 2))[:, -36:])


def fit(tr, seed, blind):
    torch.manual_seed(seed); g = torch.Generator().manual_seed(seed); m = ICON().to(H.DEV); opt = torch.optim.AdamW(m.parameters(), 5e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 5e-4, total_steps=STEPS, pct_start=0.1); K, h = torch.as_tensor(tr["K"]).to(H.DEV), torch.as_tensor(tr["h"]).to(H.DEV); t0 = time.time()
    for st in range(STEPS):
        j = torch.randint(NTR, (32,), generator=g).to(H.DEV); perm = torch.randperm(NS, generator=g).to(H.DEV)        # random storm order per step
        n = 0 if blind else int(torch.randint(NS, (), generator=g))
        loss = ((m(K[j][:, perm], h[j][:, perm], n) - h[j][:, perm][:, n]) ** 2).mean(); opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    return m.eval(), time.time() - t0


@torch.no_grad()
def rmse(m, d, n):
    K, h = torch.as_tensor(d["K"]).to(H.DEV), torch.as_tensor(d["h"]).to(H.DEV)
    order = list(range(n)) + [NS - 1]                                   # the query is always the last storm, never shown as context
    return float(((m(K[:, order], h[:, order], n) - h[:, -1]) ** 2).mean().sqrt()) / H.OUT_SCALE


def job(s):
    tr, te = data("e6_train", NTR, 60), data("e6_test", NTE, 61)
    m, t = fit(tr, s, False); mb, tb = fit(tr, s, True)
    r = dict({f"shot{n}": rmse(m, te, n) for n in SHOTS}, blind_model=rmse(mb, te, 0), train_s=t + tb,
             zero_pred=float(np.sqrt((te["h"][:, -1] ** 2).mean())) / H.OUT_SCALE)
    print(f"[E6] seed {s}:", {k: round(v, 4) for k, v in r.items()}, flush=True)
    return r


if __name__ == "__main__":
    data("e6_train", NTR, 60), data("e6_test", NTE, 61); per = H.pmap(job, list(H.SEEDS))
    H.save("E6", dict(per_seed=per, summary=H.summarise(per), steps=STEPS, grid=R, train_terrains=NTR, test_terrains=NTE,
                      note="RMSE of peak depth (m) on 120 unseen terrains (fractal/valley/basin), query storm never in context; "
                           "blind_model is the same transformer trained with no context"))
