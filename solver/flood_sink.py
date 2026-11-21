"""flood.py plus water-absorbing ground (rain gardens, permeable paving, grass). flood.py is untouched.

Two-stage sink per cell, taking water that is standing on the cell:
  stage 1  s1_m  (m of water)  instant: takes whatever is on the cell until it is full
  stage 2  s2_m  (m of water)  fills at up to f_m_s (m/s), only from water present on the cell
Water taken leaves the flow for good and is counted (absorbed_m3). Sink arrays are (H,W) or (B,H,W),
zero = no sink, and are zeroed on closed cells.

Order inside one step (everything before the sink is flood.py's step, unchanged):
  1. momentum update, flux limiter, h = max(h - div*dt/dx, 0)
  2. rain added
  3. SINK: t1 = min(h, room1); h -= t1;  t2 = min(h, room2, f*dt); h -= t2
  4. critical-depth boundary outflow from what is left
  5. peak = max(peak, h)   (so peak depth is after the sink has taken its share)

With all sink arrays zero and a scalar n_manning, the arithmetic reduces to flood.py's (h - 0 - 0).
The time-step rule is not changed: the sink only lowers h, so dt chosen from an earlier hmax stays valid.
"""
import os, sys, time
import numpy as np
import mlx.core as mx
sys.path.insert(0, os.path.dirname(__file__))
from flood import G


def _b3(a, B, H, W, name):
    a = np.asarray(a, np.float32)
    if a.ndim == 2:
        a = a[None]
    if a.shape[-2:] != (H, W) or a.shape[0] not in (1, B):
        raise ValueError(f"{name} has shape {a.shape}, expected ({H},{W}) or ({B},{H},{W})")
    return a


def make_step_sink(z, open_, dx, f_m_s, rain_mask=None, n_manning=0.015, theta=1.0, outflow=True):
    """flood.make_step with a sink. f_m_s: (1|B,H,W) float32, already zero on closed cells.
    n_manning: scalar (identical to flood.py) or (H,W)/(B,H,W) per-cell array; a face uses the
    mean n of its two cells."""
    H, W = z.shape[-2:]
    op = np.asarray(open_, bool)
    if np.ndim(n_manning) == 0:
        n2x = n2y = float(n_manning) ** 2
    else:
        nm = np.asarray(n_manning, np.float64)
        nm = nm[None] if nm.ndim == 2 else nm
        n2x = mx.array((((nm[:, :, :-1] + nm[:, :, 1:]) / 2) ** 2).astype(np.float32))
        n2y = mx.array((((nm[:, :-1] + nm[:, 1:]) / 2) ** 2).astype(np.float32))
    zz = mx.array(np.asarray(z, np.float32))
    zfx = mx.maximum(zz[..., :, :-1], zz[..., :, 1:])
    zfy = mx.maximum(zz[..., :-1, :], zz[..., 1:, :])
    fx = mx.array(op[:, :-1] & op[:, 1:])
    fy = mx.array(op[:-1] & op[1:])
    rm = mx.array((op if rain_mask is None else np.asarray(rain_mask, bool)).astype(np.float32))
    e = np.zeros((H, W), bool)
    e[0] = e[-1] = e[:, 0] = e[:, -1] = True
    edge = mx.array(((e & op) if outflow else np.zeros_like(e)).astype(np.float32))
    fr = mx.array(np.asarray(f_m_s, np.float32))
    P = lambda a, t, b, l, r: mx.pad(a, [(0, 0), (t, b), (l, r)])

    def step(h, qx, qy, peak, bacc, room1, room2, sacc, rate, dt):
        """As flood.py's step; room1/room2 (B,H,W) are the remaining sink capacities in m,
        sacc (B,) accumulates the depth taken by the sink."""
        eta = zz + h
        hfx = mx.maximum(mx.maximum(eta[:, :, :-1], eta[:, :, 1:]) - zfx, 0.)
        hfy = mx.maximum(mx.maximum(eta[:, :-1], eta[:, 1:]) - zfy, 0.)
        wx = (hfx > 1e-4) & fx
        wy = (hfy > 1e-4) & fy
        sx = mx.where(wx, hfx, 1.)
        sy = mx.where(wy, hfy, 1.)
        if theta < 1.0:
            qxs = theta * qx + (1 - theta) / 2 * (P(qx, 0, 0, 1, 0)[:, :, :-1] + P(qx, 0, 0, 0, 1)[:, :, 1:])
            qys = theta * qy + (1 - theta) / 2 * (P(qy, 1, 0, 0, 0)[:, :-1] + P(qy, 0, 1, 0, 0)[:, 1:])
        else:
            qxs, qys = qx, qy
        qx = mx.where(wx, (qxs - G * sx * dt * (eta[:, :, 1:] - eta[:, :, :-1]) / dx) /
                      (1 + G * dt * n2x * mx.abs(qx) / sx ** (7 / 3)), 0.)
        qy = mx.where(wy, (qys - G * sy * dt * (eta[:, 1:] - eta[:, :-1]) / dx) /
                      (1 + G * dt * n2y * mx.abs(qy) / sy ** (7 / 3)), 0.)
        qxp = mx.maximum(qx, 0); qxm = mx.maximum(-qx, 0)
        qyp = mx.maximum(qy, 0); qym = mx.maximum(-qy, 0)
        out = (P(qxp, 0, 0, 0, 1) + P(qxm, 0, 0, 1, 0) + P(qyp, 0, 1, 0, 0) + P(qym, 1, 0, 0, 0)) * dt / dx
        f = mx.minimum(1., h / (out + 1e-12))
        qx = qxp * f[:, :, :-1] - qxm * f[:, :, 1:]
        qy = qyp * f[:, :-1] - qym * f[:, 1:]
        div = P(qx, 0, 0, 0, 1) - P(qx, 0, 0, 1, 0) + P(qy, 0, 1, 0, 0) - P(qy, 1, 0, 0, 0)
        h = mx.maximum(h - div * dt / dx, 0.) + rate * dt * rm
        # --- sink: never more than the cell holds, never more than the room left ---
        t1 = mx.where(dt > 0, mx.minimum(h, room1), 0.)      # dt=0 must freeze the storm exactly
        h = h - t1
        room1 = room1 - t1
        t2 = mx.minimum(mx.minimum(h, room2), fr * dt)
        h = h - t2
        room2 = room2 - t2
        sacc = sacc + t1.sum(axis=(1, 2)) + t2.sum(axis=(1, 2))
        # --- boundary outflow, as flood.py ---
        hs = mx.maximum(h, 1e-9)
        bo = mx.minimum(h, edge * dt / dx * hs * mx.sqrt(G * hs))
        h = h - bo
        return h, qx, qy, mx.maximum(peak, h), bacc + bo.sum(axis=(1, 2)), room1, room2, sacc

    return mx.compile(step)


def simulate_sink(z, open_, dx, rc, profile, profile_dt_s, loss_mm_h, t_end_s, *,
                  s1_m=None, s2_m=None, f_m_s=None,
                  rain_mult=1.0, rain_mask=None, alpha=0.7, h_floor=0.05, dt_fixed=None, check=10,
                  n_manning=0.015, theta=1.0, outflow=True, h0=None, step=None, return_fields=False,
                  series_dt_s=None):
    """flood.simulate with a two-stage sink (see module docstring). Same arguments and outputs, plus:

    s1_m, s2_m (m), f_m_s (m/s): (H,W) or (B,H,W); None or zero = no sink; closed cells are zeroed.
    n_manning may also be a (H,W) or (B,H,W) array.
    `step`, if given, must come from make_step_sink (it bakes in f_m_s and n_manning).

    Extra outputs: absorbed_m3 (B,), sink_capacity_m3 (B,), sink_fill_frac (B,) (0 where a member has
    no sink), absorbed_s1_m3 / absorbed_s2_m3 (B,) (from the remaining-room fields), and with
    return_fields: room1_field, room2_field (remaining capacity, m).
    imbalance = (stored0 + rain - stored - boundary - absorbed) / (stored0 + rain).
    """
    profile = np.atleast_2d(np.asarray(profile, np.float64))
    B, K = profile.shape
    H, W = z.shape[-2:]
    loss = np.broadcast_to(np.asarray(loss_mm_h, np.float64), (B,))
    tend = np.broadcast_to(np.asarray(t_end_s, np.float64), (B,))
    eff = np.maximum(profile - loss[:, None], 0.) * rain_mult / 3.6e6
    eff = np.concatenate([eff, np.zeros((B, 1))], 1)
    op = np.asarray(open_, bool)
    rmask = np.asarray(open_ if rain_mask is None else rain_mask, bool)
    n_rain = float(rmask.sum())

    zero = np.zeros((H, W), np.float32)
    c1 = _b3(zero if s1_m is None else s1_m, B, H, W, "s1_m") * op
    c2 = _b3(zero if s2_m is None else s2_m, B, H, W, "s2_m") * op
    fr = _b3(zero if f_m_s is None else f_m_s, B, H, W, "f_m_s") * op
    if min(c1.min(), c2.min(), fr.min()) < 0:
        raise ValueError("sink arrays must be non-negative")
    c1 = np.ascontiguousarray(np.broadcast_to(c1, (B, H, W)))
    c2 = np.ascontiguousarray(np.broadcast_to(c2, (B, H, W)))
    step = step or make_step_sink(z, open_, dx, fr, rain_mask, n_manning, theta, outflow)

    h = mx.zeros((B, H, W)) if h0 is None else mx.array(np.broadcast_to(h0, (B, H, W)).astype(np.float32))
    stored0 = np.zeros(B) if h0 is None else np.broadcast_to(h0, (B, H, W)).sum((1, 2), dtype=np.float64)
    qx = mx.zeros((B, H, W - 1)); qy = mx.zeros((B, H - 1, W))
    peak = h
    bacc = mx.zeros((B,)); sacc = mx.zeros((B,))
    room1 = mx.array(c1); room2 = mx.array(c2)
    t = np.zeros(B); rain_in = np.zeros(B); bnd = np.zeros(B); absd = np.zeros(B)
    nsteps = np.zeros(B, np.int64)
    dt_max = alpha * dx / np.sqrt(G * h_floor)
    dt = np.full(B, dt_fixed if dt_fixed else dt_max)
    ar = np.arange(B)
    rc = np.asarray(rc)
    if series_dt_s:
        n_s = int(np.ceil(tend.max() / series_dt_s)) + 1
        series = np.full((B, n_s, len(rc)), np.nan, np.float32); series[:, 0] = 0.
        mrc = (mx.array(rc[:, 0]), mx.array(rc[:, 1]))
    t0 = time.time(); i = 0
    while (t < tend - 1e-9).any():
        d = np.minimum(dt, tend - t).clip(0)
        r = eff[ar, np.minimum((t / profile_dt_s).astype(int), K)]
        h, qx, qy, peak, bacc, room1, room2, sacc = step(
            h, qx, qy, peak, bacc, room1, room2, sacc,
            mx.array(r.astype(np.float32)).reshape(B, 1, 1),
            mx.array(d.astype(np.float32)).reshape(B, 1, 1))
        rain_in += r.astype(np.float32).astype(np.float64) * d.astype(np.float32) * n_rain
        k0 = (t / series_dt_s).astype(int) if series_dt_s else None
        t += d; nsteps += d > 0; i += 1
        if series_dt_s:
            k1 = (t / series_dt_s + 1e-9).astype(int); hit = k1 > k0
            if hit.any():
                series[hit, k1[hit]] = np.array(h[:, mrc[0], mrc[1]])[hit]
        if i % check == 0:
            hmax = np.array(h.max(axis=(1, 2)))     # forces evaluation
            bnd += np.array(bacc, np.float64); bacc = mx.zeros((B,))
            absd += np.array(sacc, np.float64); sacc = mx.zeros((B,))
            if not np.isfinite(hmax).all():
                raise FloatingPointError(f"non-finite depth at step {i}")
            if not dt_fixed:
                dt = alpha * dx / np.sqrt(G * np.maximum(hmax, h_floor))
    mx.eval(h, peak, bacc, sacc, room1, room2)
    wall = time.time() - t0
    bnd += np.array(bacc, np.float64); absd += np.array(sacc, np.float64)
    hn = np.array(h); pk = np.array(peak); r1 = np.array(room1); r2 = np.array(room2)
    a = dx * dx
    stored = hn.sum((1, 2), dtype=np.float64)
    cap1 = c1.sum((1, 2), dtype=np.float64); cap2 = c2.sum((1, 2), dtype=np.float64)
    cap = cap1 + cap2
    gross = (np.concatenate([profile, np.zeros((B, 1))], 1) * rain_mult / 3.6e6)
    out = dict(peak_depth=pk[:, rc[:, 0], rc[:, 1]], final_depth=hn[:, rc[:, 0], rc[:, 1]],
               rain_net_m3=rain_in * a, stored_m3=stored * a, boundary_m3=bnd * a, absorbed_m3=absd * a,
               sink_capacity_m3=cap * a,
               sink_fill_frac=np.where(cap > 0, absd / np.maximum(cap, 1e-300), 0.),
               absorbed_s1_m3=(cap1 - r1.sum((1, 2), dtype=np.float64)) * a,
               absorbed_s2_m3=(cap2 - r2.sum((1, 2), dtype=np.float64)) * a,
               imbalance=(stored0 + rain_in - stored - bnd - absd) / np.maximum(stored0 + rain_in, 1e-12),
               gross_rain_m3=gross.sum(1) * profile_dt_s * n_rain * a,
               nsteps=nsteps, hmax=pk.max((1, 2)), wall_s=wall,
               cell_steps_per_s=float(nsteps.sum()) * H * W / wall)
    if series_dt_s:
        out["series"] = series; out["series_t_s"] = np.arange(n_s) * series_dt_s
    if return_fields:
        out["peak_field"] = pk; out["final_field"] = hn
        out["room1_field"] = r1; out["room2_field"] = r2
    return out
