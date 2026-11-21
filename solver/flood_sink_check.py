"""Small checks for flood_sink.py on a 128 x 128 crop, batch of 2. Light on the GPU by design.

uv run --with mlx --with numpy python solver/flood_sink_check.py
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from flood import simulate
from flood_sink import simulate_sink

R0, C0, N = 128, 0, 128
t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz"); p = np.load("shared/p1_cases.npz")
z = t["z"][R0:R0 + N, C0:C0 + N].copy(); op = t["open"][R0:R0 + N, C0:C0 + N].copy(); dx = float(t["dx"])
rc = r["rc"]; m = (rc[:, 0] >= R0) & (rc[:, 0] < R0 + N) & (rc[:, 1] >= C0) & (rc[:, 1] < C0 + N)
rc = rc[m] - [R0, C0]
prof = p["profile"][1:3]; pdt = float(p["profile_dt_s"]); loss = float(p["loss_mm_h"]); tend = float(p["t_end_s"])
kw = dict(alpha=0.7, h_floor=0.05, n_manning=0.015, theta=1.0, rain_mult=1.0)
print(f"crop rows {R0}:{R0+N} cols {C0}:{C0+N}, open cells {op.sum()}, receptors {len(rc)}, storms: p1 cases 1 and 2")

# warm both (compile + first-call cost), then time
simulate(z, op, dx, rc, prof, pdt, loss, 120.0, **kw); simulate_sink(z, op, dx, rc, prof, pdt, loss, 120.0, **kw)
a = simulate(z, op, dx, rc, prof, pdt, loss, tend, return_fields=True, **kw)
b = simulate_sink(z, op, dx, rc, prof, pdt, loss, tend, return_fields=True, **kw)
a2 = simulate(z, op, dx, rc, prof, pdt, loss, tend, **kw)
b2 = simulate_sink(z, op, dx, rc, prof, pdt, loss, tend, **kw)

print("\n1. zero sink vs flood.simulate")
for k in ("peak_depth", "final_depth", "peak_field", "final_field"):
    print(f"   {k:12s} bit-identical: {np.array_equal(a[k], b[k])}, max |diff| {np.abs(a[k] - b[k]).max():.3e} m")
print(f"   nsteps equal: {np.array_equal(a['nsteps'], b['nsteps'])} {a['nsteps']}, boundary_m3 diff "
      f"{np.abs(a['boundary_m3'] - b['boundary_m3']).max():.3e}, absorbed {b['absorbed_m3']}")
print(f"   imbalance simulate {a['imbalance']}, simulate_sink {b['imbalance']}")

print("\n4. timing (wall_s of the loop, batch 2, after warm-up; two runs each)")
wa = min(a["wall_s"], a2["wall_s"]); wb = min(b["wall_s"], b2["wall_s"])
print(f"   simulate {a['wall_s']:.2f}, {a2['wall_s']:.2f} s; simulate_sink {b['wall_s']:.2f}, {b2['wall_s']:.2f} s; "
      f"best-of-2 overhead {100 * (wb / wa - 1):+.1f}%")

# 3. sanity: same storm (case 2, 70 mm net) in both members.
#    member 0: a 100-cell patch on the deepest-ponding open cells of the no-sink run, small capacity -> must fill
#    member 1: every open cell, huge capacity -> must stay below capacity and below the rain
pf = np.where(op, a["final_field"][1], -1.)
idx = np.argsort(pf.ravel())[-100:]
patch = np.zeros((N, N), bool); patch.ravel()[idx] = True
print(f"\n3. sanity. patch: 100 cells, no-sink final depth there {pf[patch].min():.3f}..{pf[patch].max():.3f} m")
s1 = np.zeros((2, N, N), np.float32); s2 = np.zeros_like(s1); f = np.zeros_like(s1)
s1[0, patch] = 0.05; s2[0, patch] = 0.10; f[0, patch] = 1e-4          # 15 m3 total, stage 2 needs 1000 s
s1[1] = 0.05; s2[1] = 5.0; f[1] = 1e-5                                # 36 mm/h on every cell, ~bottomless
s1[1, ~op] = 9.9                                                      # closed cells must be ignored
pp = np.stack([prof[1], prof[1]])
c = simulate_sink(z, op, dx, rc, pp, pdt, loss, tend, s1_m=s1, s2_m=s2, f_m_s=f, return_fields=True, **kw)
for j, name in enumerate(("patch 100 cells s1=0.05 s2=0.10 f=1e-4", "all open cells s1=0.05 s2=5 f=1e-5")):
    print(f"   member {j} ({name}): capacity {c['sink_capacity_m3'][j]:.4f} m3, absorbed {c['absorbed_m3'][j]:.4f} m3 "
          f"(s1 {c['absorbed_s1_m3'][j]:.4f}, s2 {c['absorbed_s2_m3'][j]:.4f}), fill {c['sink_fill_frac'][j]:.6f}, "
          f"rain {c['rain_net_m3'][j]:.2f}, stored {c['stored_m3'][j]:.2f}, out {c['boundary_m3'][j]:.2f}, "
          f"imbalance {c['imbalance'][j]:+.1e}")
    print(f"      room left min {min(c['room1_field'][j].min(), c['room2_field'][j].min()):.3e} (never negative), "
          f"min depth {c['final_field'][j].min():.3e}, hmax {c['hmax'][j]:.3f} (no sink {a['hmax'][1]:.3f})")
exp1 = op.sum() * 0.05 + min(1e-5 * tend, 5.0) * op.sum()
print(f"   member 1 upper bound s1 + f*t_end on open cells = {exp1:.2f} m3 (absorbed must be <= this and <= rain)")
print(f"   member 0 peak at receptors: max change vs no sink {np.abs(c['peak_depth'][0] - a['peak_depth'][1]).max():.4f} m")

# per-cell Manning array: constant array should reproduce the scalar closely (not bit-exact: float32 n)
d = simulate_sink(z, op, dx, rc, prof, pdt, loss, tend, **{**kw, "n_manning": np.full((N, N), 0.015)})
e = simulate_sink(z, op, dx, rc, prof, pdt, loss, tend, **{**kw, "n_manning": np.where(np.arange(N)[None] < 64, 0.015, 0.05) * np.ones((N, 1))})
print(f"\nManning array: constant 0.015 array vs scalar max |peak diff| {np.abs(d['peak_depth'] - b['peak_depth']).max():.3e} m; "
      f"half the crop at n=0.05: imbalance {e['imbalance']}, max |peak diff| {np.abs(e['peak_depth'] - b['peak_depth']).max():.3f} m")

print("\n2. mass balance |imbalance| max over all sink runs:",
      f"{max(np.abs(x['imbalance']).max() for x in (b, c, d, e)):.2e}")
assert max(np.abs(x["imbalance"]).max() for x in (b, c, d, e)) < 1e-3
assert (c["absorbed_m3"] <= c["sink_capacity_m3"] * (1 + 1e-5)).all()
