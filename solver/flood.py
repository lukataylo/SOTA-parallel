"""Batched local-inertial shallow-water solver (MLX, Apple GPU, float32).

Scheme: Bates et al. 2010 local-inertial, semi-implicit Manning friction, positivity-preserving
flux limiter, as in prior/floodlab.py. Added here: wall masks, per-storm rain series and loss,
per-storm adaptive time step, free (critical-depth) outflow on every open edge cell,
full-field peak depth, float64 mass accounting on the host.

Run `python solver/flood.py` for a smoke test on the real tile.
"""
import time
import numpy as np
import mlx.core as mx

G = 9.81


def make_step(z, open_, dx, rain_mask=None, n_manning=0.015, theta=1.0, outflow=True):
    """Compile one step for a (B,H,W) batch. z, open_ are (H,W) numpy arrays."""
    H, W = z.shape
    n2 = n_manning ** 2
    op = np.asarray(open_, bool)
    zz = mx.array(np.asarray(z, np.float32))
    zfx = mx.maximum(zz[:, :-1], zz[:, 1:])
    zfy = mx.maximum(zz[:-1], zz[1:])
    fx = mx.array(op[:, :-1] & op[:, 1:])          # a face carries flow only between two open cells
    fy = mx.array(op[:-1] & op[1:])
    rm = mx.array((op if rain_mask is None else np.asarray(rain_mask, bool)).astype(np.float32))
    e = np.zeros((H, W), bool)
    e[0] = e[-1] = e[:, 0] = e[:, -1] = True
    edge = mx.array(((e & op) if outflow else np.zeros_like(e)).astype(np.float32))
    P = lambda a, t, b, l, r: mx.pad(a, [(0, 0), (t, b), (l, r)])

    def step(h, qx, qy, peak, bacc, rate, dt):
        """rate: (B,1,1) effective rain m/s. dt: (B,1,1) s; dt=0 freezes that storm exactly."""
        eta = zz + h
        hfx = mx.maximum(mx.maximum(eta[:, :, :-1], eta[:, :, 1:]) - zfx, 0.)
        hfy = mx.maximum(mx.maximum(eta[:, :-1], eta[:, 1:]) - zfy, 0.)
        wx = (hfx > 1e-4) & fx
        wy = (hfy > 1e-4) & fy
        sx = mx.where(wx, hfx, 1.)
        sy = mx.where(wy, hfy, 1.)
        if theta < 1.0:   # de Almeida et al. 2012 flux smoothing
            qxs = theta * qx + (1 - theta) / 2 * (P(qx, 0, 0, 1, 0)[:, :, :-1] + P(qx, 0, 0, 0, 1)[:, :, 1:])
            qys = theta * qy + (1 - theta) / 2 * (P(qy, 1, 0, 0, 0)[:, :-1] + P(qy, 0, 1, 0, 0)[:, 1:])
        else:
            qxs, qys = qx, qy
        qx = mx.where(wx, (qxs - G * sx * dt * (eta[:, :, 1:] - eta[:, :, :-1]) / dx) /
                      (1 + G * dt * n2 * mx.abs(qx) / sx ** (7 / 3)), 0.)
        qy = mx.where(wy, (qys - G * sy * dt * (eta[:, 1:] - eta[:, :-1]) / dx) /
                      (1 + G * dt * n2 * mx.abs(qy) / sy ** (7 / 3)), 0.)
        qxp = mx.maximum(qx, 0); qxm = mx.maximum(-qx, 0)
        qyp = mx.maximum(qy, 0); qym = mx.maximum(-qy, 0)
        out = (P(qxp, 0, 0, 0, 1) + P(qxm, 0, 0, 1, 0) + P(qyp, 0, 1, 0, 0) + P(qym, 1, 0, 0, 0)) * dt / dx
        f = mx.minimum(1., h / (out + 1e-12))       # limiter: a cell cannot give more than it holds
        qx = qxp * f[:, :, :-1] - qxm * f[:, :, 1:]
        qy = qyp * f[:, :-1] - qym * f[:, 1:]
        div = P(qx, 0, 0, 0, 1) - P(qx, 0, 0, 1, 0) + P(qy, 0, 1, 0, 0) - P(qy, 1, 0, 0, 0)
        h = mx.maximum(h - div * dt / dx, 0.) + rate * dt * rm
        hs = mx.maximum(h, 1e-9)
        bo = mx.minimum(h, edge * dt / dx * hs * mx.sqrt(G * hs))   # critical-depth outflow
        h = h - bo
        return h, qx, qy, mx.maximum(peak, h), bacc + bo.sum(axis=(1, 2))

    return mx.compile(step)


def simulate(z, open_, dx, rc, profile, profile_dt_s, loss_mm_h, t_end_s, *,
             rain_mult=1.0, rain_mask=None, alpha=0.7, h_floor=0.05, dt_fixed=None, check=10,
             n_manning=0.015, theta=1.0, outflow=True, h0=None, step=None, return_fields=False):
    """Simulate one batch of B storms on one terrain.

    profile (B,K) mm/h at fixed step profile_dt_s; loss_mm_h (B,) is subtracted from the rain
    rate (floored at zero); t_end_s (B,) is each storm's simulated length.
    dt per storm = alpha*dx/sqrt(g*hmax), refreshed every `check` steps, capped via h_floor.
    Returns peak/final depth at receptors rc (n,2 row,col) and a per-storm mass balance in m3.
    """
    profile = np.atleast_2d(np.asarray(profile, np.float64))
    B, K = profile.shape
    H, W = z.shape
    loss = np.broadcast_to(np.asarray(loss_mm_h, np.float64), (B,))
    tend = np.broadcast_to(np.asarray(t_end_s, np.float64), (B,))
    eff = np.maximum(profile - loss[:, None], 0.) * rain_mult / 3.6e6         # m/s on rained cells
    eff = np.concatenate([eff, np.zeros((B, 1))], 1)                            # dry after the series
    rmask = np.asarray(open_ if rain_mask is None else rain_mask, bool)
    n_rain = float(rmask.sum())
    step = step or make_step(z, open_, dx, rain_mask, n_manning, theta, outflow)

    h = mx.zeros((B, H, W)) if h0 is None else mx.array(np.broadcast_to(h0, (B, H, W)).astype(np.float32))
    stored0 = np.zeros(B) if h0 is None else np.broadcast_to(h0, (B, H, W)).sum((1, 2), dtype=np.float64)
    qx = mx.zeros((B, H, W - 1)); qy = mx.zeros((B, H - 1, W))
    peak = h
    bacc = mx.zeros((B,))
    t = np.zeros(B); rain_in = np.zeros(B); bnd = np.zeros(B); nsteps = np.zeros(B, np.int64)
    dt_max = alpha * dx / np.sqrt(G * h_floor)
    dt = np.full(B, dt_fixed if dt_fixed else dt_max)
    ar = np.arange(B)
    t0 = time.time(); i = 0
    while (t < tend - 1e-9).any():
        d = np.minimum(dt, tend - t).clip(0)
        r = eff[ar, np.minimum((t / profile_dt_s).astype(int), K)]
        h, qx, qy, peak, bacc = step(h, qx, qy, peak, bacc,
                                     mx.array(r.astype(np.float32)).reshape(B, 1, 1),
                                     mx.array(d.astype(np.float32)).reshape(B, 1, 1))
        # host accounting uses the float32 values the GPU actually used
        rain_in += r.astype(np.float32).astype(np.float64) * d.astype(np.float32) * n_rain
        t += d; nsteps += d > 0; i += 1
        if i % check == 0:
            hmax = np.array(h.max(axis=(1, 2)))     # forces evaluation
            bnd += np.array(bacc, np.float64); bacc = mx.zeros((B,))
            if not np.isfinite(hmax).all():
                raise FloatingPointError(f"non-finite depth at step {i}")
            if not dt_fixed:
                dt = alpha * dx / np.sqrt(G * np.maximum(hmax, h_floor))
    mx.eval(h, peak, bacc)
    wall = time.time() - t0
    bnd += np.array(bacc, np.float64)
    hn = np.array(h); pk = np.array(peak)
    a = dx * dx
    stored = hn.sum((1, 2), dtype=np.float64)
    rc = np.asarray(rc)
    # "drained" (the loss) never enters the grid: rain_in is already net of it
    gross = (np.concatenate([profile, np.zeros((B, 1))], 1) * rain_mult / 3.6e6)
    out = dict(peak_depth=pk[:, rc[:, 0], rc[:, 1]], final_depth=hn[:, rc[:, 0], rc[:, 1]],
               rain_net_m3=rain_in * a, stored_m3=stored * a, boundary_m3=bnd * a,
               imbalance=(stored0 + rain_in - stored - bnd) / np.maximum(stored0 + rain_in, 1e-12),
               gross_rain_m3=gross.sum(1) * profile_dt_s * n_rain * a,
               nsteps=nsteps, hmax=pk.max((1, 2)), wall_s=wall,
               cell_steps_per_s=float(nsteps.sum()) * H * W / wall)
    if return_fields:
        out["peak_field"] = pk; out["final_field"] = hn
    return out


def standin_storms(n, seed=0, profile_dt_s=60.0):
    """Stand-in storms until shared/storms_*.npz exist. Ranges are the brief's stated assumptions."""
    r = np.random.default_rng(seed)
    depth = r.uniform(10, 120, n); dur = r.choice([900, 1800, 2700, 3600], n).astype(float)
    K = int(3600 / profile_dt_s)
    prof = np.zeros((n, K))
    for i in range(n):
        k = int(dur[i] / profile_dt_s)
        peak_at = r.choice([0.2, 0.5, 0.8])                      # front, centred, back loaded
        w = np.exp(-0.5 * ((np.arange(k) + 0.5) / k - peak_at) ** 2 / 0.2 ** 2)
        prof[i, :k] = w / w.sum() * depth[i] / (profile_dt_s / 3600)   # mm/h, integrates to depth
    return dict(depth_mm=depth, duration_s=dur, profile=prof, loss_mm_h=np.full(n, 12.0),
                profile_dt_s=profile_dt_s)


def load_tile(path="data/blackfriars_512.npz"):
    d = np.load(path)
    op = d["buildings"] == 0
    return d["dtm"].astype(np.float32), op, 1.0


if __name__ == "__main__":
    import sys
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    z, op, dx = load_tile()
    s = standin_storms(B, seed=1)
    rr = np.random.default_rng(0); idx = np.argwhere(op); rc = idx[rr.choice(len(idx), 100, replace=False)]
    o = simulate(z, op, dx, rc, s["profile"], s["profile_dt_s"], s["loss_mm_h"], s["duration_s"] + 1200)
    print(f"B={B} wall {o['wall_s']:.1f}s  {o['cell_steps_per_s']/1e6:.0f} Mcell-steps/s  "
          f"steps {o['nsteps'].min()}..{o['nsteps'].max()}")
    for i in range(B):
        print(f"  {s['depth_mm'][i]:5.1f} mm / {s['duration_s'][i]/60:.0f} min: net rain {o['rain_net_m3'][i]:8.0f} m3, "
              f"stored {o['stored_m3'][i]:8.0f}, out {o['boundary_m3'][i]:7.0f}, imbalance {o['imbalance'][i]:+.1e}, "
              f"hmax {o['hmax'][i]:.2f} m, receptors >=0.10 m: {(o['peak_depth'][i] >= 0.1).sum()}/100")
    assert np.abs(o["imbalance"]).max() < 1e-3, "mass balance worse than 0.1%"
