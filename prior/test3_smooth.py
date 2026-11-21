"""Test 3: does averaging the scan map over extra noise draws make it stable?
Truth 0.25 m. 'LiDAR' = 1 m block mean + 3 cm noise per block. Scan unit = 1 m block.
Kill line: top-11% agreement between two independent LiDAR realisations > 80% after smoothing."""
import sys, json, time, numpy as np, jax, jax.numpy as jnp
from floodlab import *
K = 6; SIG = 0.03; FRAC = 0.11; B = 4
STORMS = [(50e-3 / 120, 120.), (90e-3 / 120, 120.)]
out = {}
for seed in [int(a) for a in sys.argv[1:]] or [1, 2, 3]:
    t0 = time.time()
    st = make_street(seed, 0.25); zt = st["z"]; ny, nx = zt.shape
    ground = (st["rainmask"] > 0) | st["thr"] | st["interior"]
    sim, _, _ = make_sim(st, 240.)
    Rs = jnp.array([s[0] for s in STORMS]); Ts = jnp.array([s[1] for s in STORMS])
    depths = jax.jit(lambda z: jax.vmap(lambda R, T: sim(z, R, T)[0])(Rs, Ts))
    grad = jax.jit(jax.grad(lambda z: jax.vmap(lambda R, T: sim(z, R, T)[0])(Rs, Ts).sum()))
    blk = lambda a: a.reshape(ny // B, B, nx // B, B)
    gb = blk(ground).sum((1, 3)); bmean = blk(zt * ground).sum((1, 3)) / np.maximum(gb, 1)
    gblock = gb > 0; nb = int(gblock.sum()); ntop = int(round(FRAC * nb))
    up = lambda a: np.repeat(np.repeat(a, B, 0), B, 1)
    def lidar(rng):
        return np.where(ground, up(bmean + rng.normal(0, SIG, bmean.shape)), zt).astype(np.float32)
    def score(z):
        g = np.abs(np.array(grad(jnp.array(z)))) * ground
        return blk(g).sum((1, 3))
    def top(s):
        s = np.where(gblock, s, -1); idx = np.argsort(-s.ravel())[:ntop]
        m = np.zeros(s.size, bool); m[idx] = True; return m.reshape(s.shape)
    d_true = np.array(depths(jnp.array(zt)))
    def err(z): return float(np.abs(np.array(depths(jnp.array(z))) - d_true).mean())
    def scanned(z, m): return np.where(up(m), zt, z)
    res = dict(single_top=[], smooth_top=[], err0=[], err_single=[], err_smooth=[], err_rand=[])
    for a in range(2):
        rng = np.random.default_rng(1000 * seed + a)
        zo = lidar(rng)
        s1 = score(zo)
        sm = np.zeros_like(s1)
        for k in range(K):
            pert = np.where(ground, up(rng.normal(0, SIG, bmean.shape)), 0).astype(np.float32)
            sm += score(zo + pert) / K
        t1, tK = top(s1), top(sm)
        rm = np.zeros(gblock.size, bool); rm[rng.choice(np.where(gblock.ravel())[0], ntop, replace=False)] = True
        res["single_top"].append(t1); res["smooth_top"].append(tK)
        res["err0"].append(err(zo)); res["err_single"].append(err(scanned(zo, t1)))
        res["err_smooth"].append(err(scanned(zo, tK))); res["err_rand"].append(err(scanned(zo, rm.reshape(gblock.shape))))
    ov = lambda m: float((m[0] & m[1]).sum() / ntop)
    r = dict(blocks=nb, ntop=ntop, agree_single=ov(res["single_top"]), agree_smooth=ov(res["smooth_top"]),
             err0_cm=100 * np.mean(res["err0"]),
             removed_single=1 - np.mean(res["err_single"]) / np.mean(res["err0"]),
             removed_smooth=1 - np.mean(res["err_smooth"]) / np.mean(res["err0"]),
             removed_random=1 - np.mean(res["err_rand"]) / np.mean(res["err0"]), secs=time.time() - t0)
    out[seed] = r; print(seed, json.dumps(r), flush=True)
    json.dump(out, open("res_test3.json", "w"), indent=1)
