"""Test 3b diagnostic: why did the gradient scan map remove only 30-37% of error on two streets?
Hypothesis: doors the blurred model thinks are dry have zero gradient, so their thresholds are never ranked.
Check: (i) scan door blocks only, (ii) door blocks first then gradient ranking, same 11% budget."""
import sys, json, numpy as np, jax, jax.numpy as jnp
from floodlab import *
SIG = 0.03; FRAC = 0.11; B = 4
STORMS = [(50e-3 / 120, 120.), (90e-3 / 120, 120.)]
for seed in (1, 2, 3):
    st = make_street(seed, 0.25); zt = st["z"]; ny, nx = zt.shape
    ground = (st["rainmask"] > 0) | st["thr"] | st["interior"]
    sim, _, _ = make_sim(st, 240.)
    Rs = jnp.array([s[0] for s in STORMS]); Ts = jnp.array([s[1] for s in STORMS])
    depths = jax.jit(lambda z: jax.vmap(lambda R, T: sim(z, R, T)[0])(Rs, Ts))
    grad = jax.jit(jax.grad(lambda z: jax.vmap(lambda R, T: sim(z, R, T)[0])(Rs, Ts).sum()))
    blk = lambda a: a.reshape(ny // B, B, nx // B, B); up = lambda a: np.repeat(np.repeat(a, B, 0), B, 1)
    gb = blk(ground).sum((1, 3)); bmean = blk(zt * ground).sum((1, 3)) / np.maximum(gb, 1); gblock = gb > 0
    nb = int(gblock.sum()); ntop = int(round(FRAC * nb))
    rng = np.random.default_rng(1000 * seed)
    zo = np.where(ground, up(bmean + rng.normal(0, SIG, bmean.shape)), zt).astype(np.float32)
    d_true = np.array(depths(jnp.array(zt))); d_obs = np.array(depths(jnp.array(zo)))
    err = lambda z: float(np.abs(np.array(depths(jnp.array(z))) - d_true).mean())
    e0 = err(zo)
    doorcells = st["thr"].copy()
    for d in st["doors"]:
        fy = d["front"][0]; doorcells[fy, d["cols"]] = True
    dblk = blk(doorcells).any((1, 3))
    s = blk(np.abs(np.array(grad(jnp.array(zo)))) * ground).sum((1, 3)); s = np.where(gblock, s, -1)
    order = np.argsort(-s.ravel())
    def topn(n, forced=None):
        m = np.zeros(s.size, bool)
        if forced is not None: m |= forced.ravel()
        for i in order:
            if m.sum() >= n: break
            m[i] = True
        return m.reshape(s.shape)
    sc = lambda m: np.where(up(m), zt, zo)
    zero_grad_doors = int(((blk(np.abs(np.array(grad(jnp.array(zo)))) * st["thr"]).sum((1, 3)) == 0) & blk(st["thr"]).any((1, 3))).sum())
    r = dict(seed=seed, ntop=ntop, door_blocks=int(dblk.sum()), thr_blocks_with_zero_gradient=zero_grad_doors,
             doors_wrong_dry_or_wet=int(((d_obs > 0.001) != (d_true > 0.001)).sum()), door_storm_cases=int(d_true.size),
             removed_gradient=1 - err(sc(topn(ntop))) / e0,
             removed_doors_only=1 - err(sc(dblk)) / e0,
             removed_doors_then_gradient=1 - err(sc(topn(ntop, dblk))) / e0)
    print(json.dumps(r), flush=True)
