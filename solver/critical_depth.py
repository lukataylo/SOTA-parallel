"""Pivot task 5: critical rainfall depth per receptor from the solver, for a few storm shapes.

More rain gives at least as much water (order check), so one sweep over depth brackets every
receptor at once; the crossing of 0.10 m is then interpolated inside its bracket.
uv run --with mlx --with numpy python solver/critical_depth.py
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from flood import simulate, make_step

t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz")
z, op, dx, rc, thr = t["z"], t["open"], float(t["dx"]), r["rc"], float(r["threshold_m"])
LOSS, STEP = 12.0, 60.0
# (peak position as a fraction of duration, duration in minutes, depths in mm). Triangular, as fill/make_shared.py.
SHAPES = [("front_60min", 0.15, 60, np.linspace(10, 120, 24)), ("centred_60min", 0.5, 60, np.linspace(10, 120, 24)),
          ("back_60min", 0.85, 60, np.linspace(10, 120, 24)), ("centred_30min", 0.5, 30, np.linspace(10, 60, 16))]


def profile(p, m, depth):
    tt = (np.arange(m) + 0.5) / m
    w = np.where(tt <= p, tt / p, (1 - tt) / (1 - p))
    out = np.zeros(60); out[:m] = w / w.sum() * depth * 60.0 / (STEP / 60.0) / 60.0 * 60.0   # mm/h, sums to depth
    return out


step = make_step(z, op, dx)
res = {}
for name, p, m, depths in SHAPES:
    f = f"results/pro/critical_{name}.npz"
    if os.path.exists(f):
        continue
    prof = np.stack([profile(p, m, d) for d in depths])
    assert np.allclose(prof.sum(1) * STEP / 3600, depths)
    pk, fn, t0 = [], [], time.time()
    for c in range(0, len(depths), 8):
        o = simulate(z, op, dx, rc, prof[c:c + 8], STEP, LOSS, m * 60 + 1200.0, step=step)
        pk.append(o["peak_depth"]); fn.append(o["final_depth"])
    pk, fn = np.concatenate(pk), np.concatenate(fn)
    net = np.maximum(prof - LOSS, 0).sum(1) * STEP / 3600
    wet = pk >= thr
    first = wet.argmax(0)                                   # first depth on the grid that floods each receptor
    crit = np.full(len(rc), np.nan); crit_net = crit.copy()
    j = np.where(wet.any(0) & (first > 0))[0]               # bracketed: dry at first-1, wet at first
    a = (thr - pk[first[j] - 1, j]) / (pk[first[j], j] - pk[first[j] - 1, j])
    crit[j] = depths[first[j] - 1] + a * (depths[first[j]] - depths[first[j] - 1])
    crit_net[j] = net[first[j] - 1] + a * (net[first[j]] - net[first[j] - 1])
    np.savez_compressed(f, shape=name, peak_frac=p, duration_min=m, depth_mm=depths, net_depth_mm=net,
                        peak_depth=pk, final_depth=fn, critical_depth_mm=crit, critical_net_depth_mm=crit_net,
                        floods_at_lowest_depth=wet[0], never_floods=~wet.any(0),
                        not_monotone=(np.diff(wet.astype(int), axis=0) < 0).any(0), wall_s=time.time() - t0)
    print(f"{name}: {time.time() - t0:.0f}s, bracketed {len(j)}, never flood {(~wet.any(0)).sum()}, "
          f"flood at {depths[0]:.0f} mm {wet[0].sum()}, not monotone {(np.diff(wet.astype(int), axis=0) < 0).any(0).sum()}, "
          f"documented site critical depth {crit[-1]:.1f} mm (net {crit_net[-1]:.1f})", flush=True)
