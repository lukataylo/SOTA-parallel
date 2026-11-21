"""E3: solver-in-the-loop corrector on the 4x-coarse solver, trained by backprop through the unroll.
python e3.py"""
import time, numpy as np, jax, jax.numpy as jnp, optax
import flood_exp as fx, harness as H
from baselines import coarse_predict
import torch, torch.nn.functional as F

RC = 12; DX, DT, CH = fx.grid(RC)             # corrector acts every CH=15 coarse steps (60 s), 40 times per storm
STAGES = ((8, 200, False), (32, 200, False), (40, 200, True))   # (unroll, steps, add peak/final-depth loss). Brief asks 8 then 32;
BS, LR = 16, 1e-3                                                # the full-length third stage is our addition so the peak map is trained.


def init(key, cin=7, w=32):
    k = jax.random.split(key, 2); he = lambda k, i, o: jax.random.normal(k, (3, 3, i, o)) * jnp.sqrt(2 / (9 * i))
    return [he(k[0], cin, w), he(k[1], w, w), jnp.zeros((3, 3, w, 3))]       # zero last layer: starts as the plain coarse solver


def cnn(p, x):
    for i, W in enumerate(p):
        x = jax.lax.conv_general_dilated(x[None], W, (1, 1), "SAME", dimension_numbers=("NHWC", "HWIO", "NHWC"))[0]
        x = jax.nn.gelu(x) if i < len(p) - 1 else x
    return x


def rollout(p, zf, K, U=fx.N_OUT):
    """Coarse solver with a learned correction to depth and flux after every segment."""
    z = fx.pool(zf, RC); blk = zf.reshape(RC, 4, RC, 4)
    sub = [blk.std((1, 3)), z - blk.min((1, 3))]                             # sub-grid relief the coarse solver cannot see
    rain_fn = fx.knots_rain_fn(fx.rain_field(K, RC))
    def seg(s, i0):
        def body(s, i):
            return fx.step(z, rain_fn(i * DT), s, DX, DT), None
        (h, qx, qy, hmax, acc), _ = jax.lax.scan(body, s, i0 + jnp.arange(CH))
        x = jnp.stack([h * 10, (z - z.mean()) / 2, jnp.pad(qx, ((0, 0), (0, 1))) * 10, jnp.pad(qy, ((0, 1), (0, 0))) * 10,
                       rain_fn((i0 + CH - 1) * DT) / fx.CAP] + sub, -1)
        d = cnn(p, x) * 0.1
        h = jax.nn.relu(h + d[..., 0]); qx = qx + d[:, :-1, 1]; qy = qy + d[:-1, :, 2]
        return (h, qx, qy, jnp.maximum(hmax, h), acc), h
    s0 = (jnp.zeros((RC, RC)), jnp.zeros((RC, RC - 1)), jnp.zeros((RC - 1, RC)), jnp.zeros((RC, RC)), jnp.zeros(3))
    s, hs = jax.lax.scan(seg, s0, jnp.arange(U) * CH)
    return hs, s[3], s[0]


def loss_fn(p, b, U, full):
    hs, hmax, hfin = jax.vmap(lambda z, K: rollout(p, z, K, U))(b["z"], b["K"])
    l = jnp.mean((hs - b["snaps"][:, :U]) ** 2)
    if full:
        l = l + jnp.mean((hmax - fx.pool(b["hmax"], RC)) ** 2) + jnp.mean((hfin - fx.pool(b["hfin"], RC)) ** 2)
    return l * 100.


def fit(tr, seed):
    p = init(jax.random.PRNGKey(seed)); rng = np.random.default_rng(seed); log = []; t0 = time.time()
    for U, steps, full in STAGES:
        lr, p0 = LR, p
        for attempt in range(3):                                             # kill rule: diverging after two LR reductions
            opt = optax.chain(optax.clip_by_global_norm(1.0), optax.adam(lr)); st = opt.init(p0); p = p0; ls = []
            vg = jax.jit(jax.value_and_grad(lambda p, b: loss_fn(p, b, U, full)))
            for i in range(steps):
                j = rng.integers(0, len(tr["z"]), BS); l, g = vg(p, {k: tr[k][j] for k in ("z", "K", "snaps", "hmax", "hfin")})
                up, st = opt.update(g, st); p = optax.apply_updates(p, up); ls.append(float(l))
            ok = np.isfinite(ls).all() and np.mean(ls[-50:]) < np.mean(ls[:20])
            log.append(dict(unroll=U, lr=lr, loss_first20=float(np.mean(ls[:20])), loss_last50=float(np.mean(ls[-50:])), ok=bool(ok)))
            print(f"  [E3 s{seed}] unroll {U} lr {lr:.0e}: loss {log[-1]['loss_first20']:.4f} -> {log[-1]['loss_last50']:.4f} {'ok' if ok else 'DIVERGED'} {time.time()-t0:.0f}s", flush=True)
            if ok:
                break
            lr *= 0.3
        if not ok:
            return None, time.time() - t0, log
    return p, time.time() - t0, log


def predictor(p):
    f = jax.jit(jax.vmap(lambda z, K: rollout(p, z, K)[1:]))
    up = lambda a: F.interpolate(torch.as_tensor(np.asarray(a))[:, None], size=fx.NF, mode="bilinear", align_corners=False)[:, 0].numpy()
    def predict(z, K):
        hmax, hfin = f(jnp.asarray(z), jnp.asarray(K)); return up(hmax), up(hfin)
    return predict


def make(s):
    p, t, log = fit(H.train_fractal(), s)
    if p is None:                                    # killed: report the plain coarse solver's numbers with the flag set
        return coarse_predict, dict(train_s=t, labels=2000, killed=True, log=log)
    return predictor(p), dict(train_s=t, labels=2000, params=int(sum(w.size for w in p)), killed=False, log=log)


if __name__ == "__main__":
    H.run_many({"E3": make}, extra=dict(note="same 2,000 fractal labels as B3; output is the corrected coarse field, bilinearly upsampled like B2; timing is in-process JAX"))
