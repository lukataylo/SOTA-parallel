"""floodlab: synthetic street generator + differentiable 2D local-inertial flood solver (JAX).

Solver: Bates et al. 2010 local-inertial shallow water, semi-implicit Manning friction,
positivity-preserving flux limiter (mass conserving), gully sinks, critical-depth outflow
at both street ends. Rain is an "effective" uniform rate on open ground (includes run-on).
"""
import numpy as np, jax, jax.numpy as jnp
from scipy.ndimage import gaussian_filter

G = 9.81
N2 = 0.015 ** 2
LX, LY = 32.0, 24.0


def make_street(seed, dx=0.25, n_sags=None):
    """Returns dict with terrain z (ny,nx) and masks. Units metres."""
    r = np.random.default_rng(seed)
    nx, ny = int(LX / dx), int(LY / dx)
    x = (np.arange(nx) + 0.5) * dx
    y = (np.arange(ny) + 0.5) * dx
    X, Y = np.meshgrid(x, y)
    A = r.uniform(0.12, 0.30)
    B = r.uniform(0.03, 0.09)
    k = n_sags if n_sags is not None else r.integers(1, 3)
    ph = r.uniform(0, 2 * np.pi)
    Lp = A * (2 * x / LX - 1) ** 2 + B * np.sin(2 * np.pi * k * x / LX + ph)
    Lp -= Lp.min()
    z = np.tile(Lp, (ny, 1))
    road = (Y >= 6) & (Y < 18)
    pavS = (Y >= 3) & (Y < 6)
    pavN = (Y >= 18) & (Y < 21)
    bld = (Y < 3) | (Y >= 21)
    z += np.where(road, 0.08 * (1 - ((Y - 12) / 6) ** 2), 0)
    kerb = np.full(nx, 0.11)
    kerbN = np.full(nx, 0.11)
    for kk in (kerb, kerbN):                       # dropped kerbs
        for _ in range(r.integers(2, 4)):
            c = r.uniform(3, LX - 3)
            w = np.clip(1 - np.abs(x - c) / 1.5, 0, 1)
            kk -= 0.09 * np.minimum(1, 2 * w) * (kk > 0.05)
    dS = np.clip(6 - Y, 0, 3); dN = np.clip(Y - 18, 0, 3)
    z += np.where(pavS, kerb[None, :] + 0.015 * dS, 0)
    z += np.where(pavN, kerbN[None, :] + 0.015 * dN, 0)
    rough = gaussian_filter(r.normal(0, 1, (ny, nx)), 0.5 / dx) * 0.012 * (0.5 / dx) ** 0.5
    z += np.where(~bld, rough, 0)
    wallS = kerb + 0.045; wallN = kerbN + 0.045     # pavement level at building line
    z = np.where(Y < 3, Lp[None, :] + wallS[None, :] + 3.0, z)
    z = np.where(Y >= 21, Lp[None, :] + wallN[None, :] + 3.0, z)
    doors = []                                      # (iy_in, ix_slice, iy_thr, iy_front)
    interior = np.zeros((ny, nx), bool); thr = np.zeros((ny, nx), bool)
    for side in (0, 1):
        xs = np.sort(r.choice(np.arange(3, 29, 3), 4, replace=False) + r.uniform(-0.5, 0.5, 4))
        for j, xc in enumerate(xs):
            t = r.uniform(0.02, 0.15)
            sunk = 0.30 if (side == 0 and j == 1) else 0.0
            cols = np.where(np.abs(x - xc) < 0.5)[0]
            if side == 0:
                ythr = np.where((y >= 3 - dx - 1e-9) & (y < 3))[0]
                yin = np.where((y >= 1.0) & (y < 3 - dx - 1e-9))[0]
                yfront = ythr.max() + 1
                base = Lp[cols] + wallS[cols]
            else:
                ythr = np.where((y >= 21) & (y < 21 + dx + 1e-9))[0]
                yin = np.where((y >= 21 + dx + 1e-9) & (y < 23.0))[0]
                yfront = ythr.min() - 1
                base = Lp[cols] + wallN[cols]
            zt = base.mean() + t
            z[np.ix_(ythr, cols)] = zt
            z[np.ix_(yin, cols)] = base.mean() - sunk
            thr[np.ix_(ythr, cols)] = True; interior[np.ix_(yin, cols)] = True
            m = np.zeros((ny, nx), bool); m[np.ix_(yin, cols)] = True
            doors.append(dict(mask=m, zt=float(zt), front=(int(yfront), int(cols[len(cols) // 2])),
                              thr_rows=ythr, cols=cols, t=float(t), sunk=sunk))
    gul = np.zeros((ny, nx))
    for yy in (6 + dx / 2, 18 - dx / 2):
        iy = int(yy / dx)
        for xc in (5 + r.uniform(-2, 2), 16 + r.uniform(-2, 2), 27 + r.uniform(-2, 2)):
            gul[iy, int(xc / dx)] = 0.004 / dx ** 2   # 4 L/s per gully, as m/s over one cell
    rainmask = (road | pavS | pavN).astype(np.float32)
    return dict(z=z.astype(np.float32), dx=dx, rainmask=rainmask, gul=gul.astype(np.float32),
                doors=doors, open=(~bld), interior=interior, thr=thr,
                doorw=np.stack([d["mask"] / d["mask"].sum() for d in doors]).astype(np.float32))


def make_sim(st, tsim=300.0, dt=None, ch=50, use_gullies=True, return_final=False):
    dx = st["dx"]
    dt = dt or 0.24 * dx
    nsteps = int(round(tsim / dt / ch)) * ch
    rm = jnp.array(st["rainmask"]); gul = jnp.array(st["gul"]) * (1.0 if use_gullies else 0.0)
    dw = jnp.array(st["doorw"])

    def step(z, R, T, s, i):
        h, qx, qy, dmax, acc = s
        t = i * dt
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
        f = jnp.minimum(1., h / (out + 1e-12))
        qx = qxp * f[:, :-1] - qxm * f[:, 1:]
        qy = qyp * f[:-1] - qym * f[1:]
        div = (jnp.pad(qx, ((0, 0), (0, 1))) - jnp.pad(qx, ((0, 0), (1, 0))) +
               jnp.pad(qy, ((0, 1), (0, 0))) - jnp.pad(qy, ((1, 0), (0, 0))))
        rain = jnp.where(t < T, R, 0.) * rm * dt
        h = h - div * dt / dx + rain
        g = jnp.minimum(gul * dt, h); h = h - g
        hs = jnp.maximum(h, 1e-9)
        edge = jnp.zeros_like(h).at[:, 0].set(1.).at[:, -1].set(1.)
        bo = jnp.minimum(h, edge * dt / dx * hs * jnp.sqrt(G * hs)); h = h - bo
        dd = (dw * h[None]).sum((1, 2))
        dmax = jnp.maximum(dmax, dd)
        acc = acc + jnp.stack([rain.sum(), g.sum(), bo.sum()])
        return (h, qx, qy, dmax, acc)

    @jax.checkpoint
    def chunk(z, R, T, s, i0):
        def body(s, i):
            return step(z, R, T, s, i), None
        s, _ = jax.lax.scan(body, s, i0 + jnp.arange(ch))
        return s

    def sim(z, R, T):
        """z terrain, R rain m/s, T rain duration s -> (door max depths, final h, mass acc)."""
        ny, nx = z.shape
        s = (jnp.zeros((ny, nx)), jnp.zeros((ny, nx - 1)), jnp.zeros((ny - 1, nx)),
             jnp.zeros(dw.shape[0]), jnp.zeros(3))
        def ob(s, i0):
            return chunk(z, R, T, s, i0), None
        s, _ = jax.lax.scan(ob, s, jnp.arange(nsteps // ch) * ch)
        return s[3], s[0], s[4]
    return sim, nsteps, dt
