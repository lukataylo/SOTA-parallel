"""Test 6: fair retest of barriers. Optimise a continuous raised-ground field b(x,y) in [0, 15 cm]
on public ground under a material budget, by gradient descent through the solver.
Compare with raising the door's own threshold by 10 cm (0.05 m3 of material).
Kill line: optimised regrade must beat the threshold raise per m3 of material."""
import sys, json, numpy as np, jax, jax.numpy as jnp, optax
from floodlab import *
DX = 0.5; CAP = 0.15; ITERS = 60
TRAIN = (90e-3 / 120, 120.); TEST = [(60e-3 / 60, 60.), (130e-3 / 180, 180.)]
out = {}
for seed in [int(a) for a in sys.argv[1:]] or [1, 2, 3]:
    st = make_street(seed, DX); z = jnp.array(st["z"]); pub = jnp.array(st["rainmask"])
    sim, _, _ = make_sim(st, 300.)
    f = jax.jit(lambda z, R, T: sim(z, R, T)[0])
    d0 = np.array(f(z, *TRAIN)); ok = [i for i, d in enumerate(st["doors"]) if d["sunk"] == 0]
    def raised(i):
        zr = np.array(z); zr[np.ix_(st["doors"][i]["thr_rows"], st["doors"][i]["cols"])] += 0.10; return jnp.array(zr)
    cand = [(float(f(raised(i), *TRAIN)[i]), i) for i in ok if d0[i] > 0.01]   # door the threshold raise helps most
    if not cand: print(seed, "no flooded door"); continue
    tgt = min(cand)[1]; door = st["doors"][tgt]; zr = raised(tgt)
    near = np.zeros(z.shape, bool); fy, fx = door["front"]
    near[max(fy - 4, 0):fy + 5, max(fx - 4, 0):fx + 5] = True          # 2 m zone round the door front
    def field(theta, mask, V):
        b = CAP * jax.nn.sigmoid(theta) * mask
        vol = b.sum() * DX * DX
        return b * jnp.minimum(1., V / vol)
    res = dict(target=tgt, t_cm=door["t"] * 100, base_cm=float(d0[tgt] * 100),
               thr_raise_cm=float(f(zr, *TRAIN)[tgt] * 100),
               base_test_cm=[float(f(z, *s)[tgt] * 100) for s in TEST],
               thr_raise_test_cm=[float(f(zr, *s)[tgt] * 100) for s in TEST], runs={})
    for name, V, mask in (("anywhere_0.05", 0.05, pub), ("anywhere_0.5", 0.5, pub), ("remote_0.5", 0.5, pub * jnp.array(~near)), ("remote_4.0", 4.0, pub * jnp.array(~near))):
        loss = lambda th: sim(z + field(th, mask, V), *TRAIN)[0][tgt]
        vg = jax.jit(jax.value_and_grad(loss))
        th = jnp.full(z.shape, -8.0) + 0.01 * jax.random.normal(jax.random.PRNGKey(seed), z.shape)
        opt = optax.adam(0.5); os_ = opt.init(th); best = (1e9, th)
        for it in range(ITERS):
            v, g = vg(th)
            if float(v) < best[0]: best = (float(v), th)
            up, os_ = opt.update(g, os_); th = optax.apply_updates(th, up)
        v = float(loss(th))
        if v < best[0]: best = (v, th)
        b = field(best[1], mask, V); zb = z + b
        dn = np.array(f(zb, *TRAIN)); bn = np.array(b)
        oth = [i for i in range(len(d0)) if i != tgt]
        res["runs"][name] = dict(depth_cm=float(dn[tgt] * 100), vol_m3=float(bn.sum() * DX * DX),
                                 cells_over_2cm=int((bn > 0.02).sum()), share_within_2m=float(bn[near].sum() / max(bn.sum(), 1e-9)),
                                 max_b_cm=float(bn.max() * 100), other_doors_change_cm=float((dn[oth] - d0[oth]).sum() * 100),
                                 test_cm=[float(f(zb, *s)[tgt] * 100) for s in TEST])
        print(seed, name, json.dumps(res["runs"][name]), flush=True)
    out[seed] = res; print(seed, json.dumps({k: v for k, v in res.items() if k != "runs"}), flush=True)
    json.dump(out, open("res_test6.json", "w"), indent=1)
