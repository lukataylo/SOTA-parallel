"""flood_exp: differentiable 2D local-inertial flood solver (JAX) + procedural terrains/storms.

Scheme is prior/floodlab.py's step, unchanged in its physics: Bates et al. 2010 local-inertial
fluxes, semi-implicit Manning friction, positivity-preserving flux limiter (mass conserving),
critical-depth open outflow. Changes for this study: rain is a space-time field rain_fn(t),
the sink is a constant sewer rate on every cell, outflow is on the downstream (last-row) edge only.

Self-check (mass, lake at rest, gradient vs finite difference, throughput):  python flood_exp.py
"""
import os, time, multiprocessing as mp
import numpy as np, jax, jax.numpy as jnp

G = 9.81
N2 = 0.015 ** 2            # Manning n^2, as prior/floodlab.py
L = 480.0                  # domain side, m
NF = 48                    # fine grid (ground truth)
T_RAIN, T_SIM = 1800.0, 2400.0
NK, KS = 8, 6              # storm knots: 8 time slabs x 6x6 space
N_OUT = 40                 # checkpoint segments (also snapshot count)
DRAIN = 10e-3 / 3600       # sewer sink, m/s (10 mm/h)
CAP = 150e-3 / 3600        # rainfall intensity cap, m/s (150 mm/h)
VOL = 0.030                # fixed storm volume: 30 mm mean depth over the domain (60 mm/h mean for 30 min)
KINDS = ("fractal", "valley", "basin", "street")


def grid(res):
    dx = L / res
    dt = dx / 10.0                              # 1 s at 10 m: CFL 0.7 holds up to ~5 m depth
    return dx, dt, int(round(T_SIM / dt / N_OUT))


def step(z, rain, s, dx, dt, drain=DRAIN):
    h, qx, qy, hmax, acc = s
    eta = z + h
    hfx = jnp.maximum(jnp.maximum(eta[:, :-1], eta[:, 1:]) - jnp.maximum(z[:, :-1], z[:, 1:]), 0.)
    hfy = jnp.maximum(jnp.maximum(eta[:-1], eta[1:]) - jnp.maximum(z[:-1], z[1:]), 0.)
    wx = hfx > 1e-4; wy = hfy > 1e-4
    sx = jnp.where(wx, hfx, 1.); sy = jnp.where(wy, hfy, 1.)
    qx = jnp.where(wx, (qx - G * sx * dt * (eta[:, 1:] - eta[:, :-1]) / dx) /
                   (1 + G * dt * N2 * jnp.abs(qx) / sx ** (7 / 3)), 0.)
    qy = jnp.where(wy, (qy - G * sy * dt * (eta[1:] - eta[:-1]) / dx) /
                   (1 + G * dt * N2 * jnp.abs(qy) / sy ** (7 / 3)), 0.)
    qxp = jnp.maximum(qx, 0); qxm = jnp.maximum(-qx, 0)
    qyp = jnp.maximum(qy, 0); qym = jnp.maximum(-qy, 0)
    out = (jnp.pad(qxp, ((0, 0), (0, 1))) + jnp.pad(qxm, ((0, 0), (1, 0))) +
           jnp.pad(qyp, ((0, 1), (0, 0))) + jnp.pad(qym, ((1, 0), (0, 0)))) * dt / dx
    f = jnp.minimum(1., h / (out + 1e-12))       # never export more water than the cell holds
    qx = qxp * f[:, :-1] - qxm * f[:, 1:]
    qy = qyp * f[:-1] - qym * f[1:]
    div = (jnp.pad(qx, ((0, 0), (0, 1))) - jnp.pad(qx, ((0, 0), (1, 0))) +
           jnp.pad(qy, ((0, 1), (0, 0))) - jnp.pad(qy, ((1, 0), (0, 0))))
    r = rain * dt
    h = h - div * dt / dx + r
    g = jnp.minimum(drain * dt, h); h = h - g
    hs = jnp.maximum(h[-1], 1e-9)                # downstream edge: critical-depth outflow
    bo = jnp.minimum(h[-1], dt / dx * hs * jnp.sqrt(G * hs))
    h = h.at[-1].add(-bo)
    acc = acc + jnp.stack([r.sum(), g.sum(), bo.sum()])
    return (h, qx, qy, jnp.maximum(hmax, h), acc)


def solve(z, rain_fn, tgt=(NF // 2, NF // 2), drain=DRAIN):
    """z (n,n) m, rain_fn(t)->(n,n) m/s. Checkpointed: backprop stores N_OUT states, not every step.
    Returns hmax, hfin, series (target depth per segment), acc (rain, drain, outflow as depth sums;
    x dx^2 for m^3), snaps (N_OUT, 12, 12) block-mean depth."""
    n = z.shape[0]
    dx, dt, ch = grid(n)

    @jax.checkpoint
    def chunk(s, i0):
        def body(s, i):
            return step(z, rain_fn(i * dt), s, dx, dt, drain), None
        s, _ = jax.lax.scan(body, s, i0 + jnp.arange(ch))
        return s, (s[0][tgt[0], tgt[1]], s[0].reshape(12, n // 12, 12, n // 12).mean((1, 3)))

    s0 = (jnp.zeros((n, n)), jnp.zeros((n, n - 1)), jnp.zeros((n - 1, n)), jnp.zeros((n, n)), jnp.zeros(3))
    s, (series, snaps) = jax.lax.scan(chunk, s0, jnp.arange(N_OUT) * ch)
    return dict(hmax=s[3], hfin=s[0], series=series, acc=s[4], snaps=snaps)


# ---------- storms: (NK, KS, KS) knots of intensity, piecewise constant in time ----------
def pool(a, res):
    f = a.shape[-1] // res
    return a.reshape(a.shape[:-2] + (res, f, res, f)).mean((-3, -1))


def rain_field(K, res=NF):
    """knots -> (NK, res, res) m/s. Bilinear up to the fine grid (a convex combination, so the cap
    carries over), then block-mean to coarser grids (so volume is identical at every resolution)."""
    return pool(jax.image.resize(K, (NK, NF, NF), "linear"), res)


def knots_rain_fn(R):
    return lambda t: jnp.where(t < T_RAIN, R[jnp.minimum((t / (T_RAIN / NK)).astype(int), NK - 1)], 0.)


def project(raw, vol=VOL):
    """Positive knots -> knots with fine-field volume `vol` and peak <= CAP (alternating scale/clip)."""
    K = raw
    for _ in range(30):
        K = jnp.minimum(K * vol / (rain_field(K).mean() * T_RAIN), CAP)
    return K


def make_storm(key, a=None):
    """a = log-contrast of the field (0 = uniform rain); None draws U(0.3, 3)."""
    k1, k2 = jax.random.split(key)
    g = jax.random.normal(k1, (NK, KS, KS))
    g = (g + jnp.roll(g, 1, 0)) / jnp.sqrt(2.)                       # some persistence in time
    return project(jnp.exp((jax.random.uniform(k2, (), minval=0.3, maxval=3.0) if a is None else a) * g))


# ---------- terrains ----------
def _fractal(key, amp):
    ks = jax.random.split(key, 4)
    return sum(amp * 0.5 ** i * jax.image.resize(jax.random.normal(ks[i], (n, n)), (NF, NF), "cubic")
               for i, n in enumerate((3, 6, 12, 24)))


def make_terrain(key, kind, rough=None):
    """(NF,NF) elevation, m. Every kind drains towards the last row. rough in [0,1] scales relief
    (noise amplitude, basin depth); None draws U(0.3,1)."""
    k = jax.random.split(key, 8)
    rough = jax.random.uniform(k[0], (), minval=0.3, maxval=1.0) if rough is None else rough
    y, x = jnp.meshgrid(jnp.linspace(0, 1, NF), jnp.linspace(0, 1, NF), indexing="ij")
    z = jax.random.uniform(k[1], (), minval=0.004, maxval=0.012) * L * (1 - y)
    if kind == "fractal":
        z = z + _fractal(k[2], 1.5 * rough)
    elif kind == "valley":
        xc = 0.5 + 0.2 * jnp.sin(2 * jnp.pi * (y + jax.random.uniform(k[3])))
        z = z + jax.random.uniform(k[4], (), minval=0.01, maxval=0.04) * L * jnp.abs(x - xc) + _fractal(k[2], 0.4 * rough)
    elif kind == "basin":
        z = z + _fractal(k[2], 0.4 * rough)
        c = jax.random.uniform(k[3], (4, 2), minval=0.15, maxval=0.85)
        d = jax.random.uniform(k[4], (4,), minval=0.5, maxval=2.0) * rough
        w = jax.random.uniform(k[5], (4,), minval=0.06, maxval=0.12)
        for i in range(4):
            z = z - d[i] * jnp.exp(-((x - c[i, 0]) ** 2 + (y - c[i, 1]) ** 2) / (2 * w[i] ** 2))
        yu = jax.random.uniform(k[6], (), minval=0.3, maxval=0.7)     # underpass: a trench across the slope
        z = z - 1.5 * rough * jnp.exp(-((y - yu) / 0.03) ** 2) * (jnp.abs(x - 0.5) < 0.3)
    elif kind == "street":
        p = jax.random.randint(k[3], (), 6, 13); o = jax.random.randint(k[4], (2,), 0, 12)
        i, j = jnp.meshgrid(jnp.arange(NF), jnp.arange(NF), indexing="ij")
        ri, rj = (i + o[0]) % p, (j + o[1]) % p
        road = (ri < 2) | (rj < 2)
        bld = (ri >= 3) & (ri < p - 1) & (rj >= 3) & (rj < p - 1)
        z = z + _fractal(k[2], 0.5 * rough) + jnp.where(road, 0., 0.15) + jnp.where(bld, 3.0, 0.)  # kerb, buildings
    return z


def make_terrains(key, kind, n, rough=None):
    return jax.vmap(lambda k: make_terrain(k, kind, rough))(jax.random.split(key, n))


def make_storms(key, n):
    return jax.vmap(make_storm)(jax.random.split(key, n))


# ---------- batched solve: vmapped chunks on a process pool ----------
def _solve_one(z, K, tgt, drain=DRAIN):
    return solve(z, knots_rain_fn(rain_field(K, z.shape[0])), tgt, drain)


_jit = {}
def _solve_chunk(a):
    if "s" not in _jit:
        _jit["s"] = jax.jit(jax.vmap(_solve_one))
    return {k: np.asarray(v) for k, v in _jit["s"](*a).items()}


def _search_chunk(a):
    """Batched gradient ascent on target-cell peak depth over storm logits, under the cap/volume
    projection. Returns knots at each iteration (iters+1, B, NK, KS, KS) and depths."""
    import optax
    z, theta, tgt, iters, lr = a
    if "g" not in _jit:
        obj = lambda th, z, t: solve(z, knots_rain_fn(rain_field(project(jnp.exp(th)))), t)["hmax"][t[0], t[1]]
        _jit["g"] = jax.jit(jax.vmap(jax.value_and_grad(obj)))
        _jit["p"] = jax.jit(jax.vmap(lambda th: project(jnp.exp(th))))
    opt = optax.adam(lr); st = opt.init(theta); Ks, ds = [], []
    for _ in range(iters):
        d, g = _jit["g"](theta, z, tgt)
        Ks.append(np.asarray(_jit["p"](theta))); ds.append(np.asarray(d))
        up, st = opt.update(-g, st); theta = optax.apply_updates(theta, up)
    return np.stack(Ks), np.stack(ds)


WORKERS = int(os.environ.get("FLOOD_WORKERS", 4))   # ponytail: 4 niced procs, machine is shared; raise if alone
_pool = None
def _init():
    os.nice(10)

def pmap(fn, tasks):
    global _pool
    if _pool is None:
        _pool = mp.get_context("spawn").Pool(WORKERS, initializer=_init)
    return _pool.map(fn, tasks, chunksize=1)


def solve_batch(terrains, storms, res=NF, tgt=None, chunk=64, drain=None):
    """terrains (B,NF,NF) fine elevations, storms (B,NK,KS,KS) knots. Terrain is block-averaged
    to `res`. Returns dict of numpy arrays: hmax, hfin (B,res,res), series, acc (B,3), snaps."""
    z = np.asarray(pool(jnp.asarray(terrains), res)); K = np.asarray(storms); B = len(z)
    tgt = np.full((B, 2), res // 2, np.int32) if tgt is None else np.asarray(tgt, np.int32)
    drain = np.full(B, DRAIN, np.float32) if drain is None else np.asarray(drain, np.float32)
    pad = (-B) % chunk
    if pad:                                    # pad to whole chunks so workers compile once
        z, K, tgt, drain = (np.concatenate([a, np.repeat(a[-1:], pad, 0)]) for a in (z, K, tgt, drain))
    outs = pmap(_solve_chunk, [tuple(a[i:i + chunk] for a in (z, K, tgt, drain)) for i in range(0, len(z), chunk)])
    return {k: np.concatenate([o[k] for o in outs])[:B] for k in outs[0]}


def search_batch(terrains, tgt, key, iters=30, lr=0.3, chunk=16):
    z = np.asarray(terrains); B = len(z)
    theta = np.asarray(0.5 * jax.random.normal(key, (B, NK, KS, KS)))
    outs = pmap(_search_chunk, [(z[i:i + chunk], theta[i:i + chunk], np.asarray(tgt[i:i + chunk], np.int32), iters, lr)
                                for i in range(0, B, chunk)])
    return np.concatenate([o[0] for o in outs], 1), np.concatenate([o[1] for o in outs], 1)


def find_targets(terrains):
    """Target cell per terrain: deepest cell under a uniform storm, away from the outflow rows."""
    K = np.broadcast_to(np.asarray(project(jnp.ones((NK, KS, KS)))), (len(terrains), NK, KS, KS))
    hm = solve_batch(terrains, K)["hmax"][:, 2:-6, 2:-2]
    i = hm.reshape(len(hm), -1).argmax(1)
    return np.stack([i // hm.shape[2] + 2, i % hm.shape[2] + 2], 1)


def volume_m3(acc, hfin, res):
    """(rain, drain, outflow, stored) in m^3 from solver outputs."""
    a = (L / res) ** 2
    return acc[..., 0] * a, acc[..., 1] * a, acc[..., 2] * a, hfin.sum((-1, -2)) * a


if __name__ == "__main__":
    jax.config.update("jax_enable_x64", True)      # checks in float64; production runs are float32
    key = jax.random.PRNGKey(0)
    out = {}
    for kind in KINDS:
        z = make_terrain(jax.random.fold_in(key, 1), kind); K = make_storm(jax.random.fold_in(key, 2))
        F = rain_field(K)
        f = jax.jit(lambda z, K: _solve_one(z, K, jnp.array([24, 24])))
        o = f(z, K); t0 = time.time(); o = f(z, K); o["hmax"].block_until_ready(); t = time.time() - t0
        rain, drain, outf, stored = (float(v) for v in volume_m3(o["acc"], o["hfin"], NF))
        imb = (rain - drain - outf - stored) / rain
        print(f"{kind:8s} rain {rain:7.1f} m3 (target {VOL*L*L:.1f}) peak {float(F.max())*3.6e6:5.1f} mm/h | drain {drain:6.1f} out {outf:6.1f} "
              f"stored {stored:6.1f} imbalance {imb:+.1e} | hmax {float(o['hmax'].max()):.2f} m, min h {float(o['hfin'].min()):.1e} | "
              f"{NF*NF*grid(NF)[2]*N_OUT/t/1e6:.1f} Mcell-steps/s (1 thread, f64)")
        assert abs(imb) < 1e-9 and float(o["hfin"].min()) >= 0 and np.isfinite(np.asarray(o["hmax"])).all()
        assert abs(rain / (VOL * L * L) - 1) < 1e-3 and float(F.max()) <= CAP * (1 + 1e-9)
        out[kind] = imb
    # lake at rest: flat water surface over uneven ground must not move (no rain, no drain, closed)
    z = make_terrain(key, "basin"); z = z.at[-1].set(z.max() + 5)             # wall off the outflow edge
    h = jnp.maximum(z.min() + 1.0 - z, 0.)
    s = (h, jnp.zeros((NF, NF - 1)), jnp.zeros((NF - 1, NF)), h, jnp.zeros(3))
    s1 = s
    for _ in range(100):
        s1 = step(z, jnp.zeros((NF, NF)), s1, 10., 1.)
    moved = float(jnp.abs(s1[0] + jnp.minimum(DRAIN * 100, h) - h).max())
    print(f"lake at rest: max depth change beyond the sewer sink after 100 steps = {moved:.1e} m")
    assert moved < 1e-9
    # gradient check: d(target peak depth + mean final depth)/d(storm logits), AD vs central FD
    z = make_terrain(jax.random.fold_in(key, 1), "fractal")
    def obj(th):
        o = solve(z, knots_rain_fn(rain_field(project(jnp.exp(th)))), (30, 24))
        return o["hmax"][30, 24] + o["hfin"].mean() + o["hmax"].mean()
    th = 0.5 * jax.random.normal(key, (NK, KS, KS)); v = jax.random.normal(jax.random.fold_in(key, 9), th.shape)
    g = jax.jit(jax.grad(obj))(th); jf = jax.jit(obj)
    ad = float((g * v).sum())
    for eps in (1e-3, 1e-4, 1e-5):
        fd = float((jf(th + eps * v) - jf(th - eps * v)) / (2 * eps))
        print(f"grad check eps {eps:.0e}: FD {fd:+.6e}  AD {ad:+.6e}  rel err {abs(fd-ad)/abs(ad):.1e}")
    assert abs(fd - ad) / abs(ad) < 2e-2
    print("ALL CHECKS PASSED")
