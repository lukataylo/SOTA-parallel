"""Pivot task 3: run each intervention case on the unchanged and the changed terrain.

uv run --with mlx --with numpy python solver/interventions.py [shared/interventions.npz results/pro/interventions.npz]
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from flood import simulate

src = sys.argv[1] if len(sys.argv) > 1 else "shared/interventions.npz"
dst = sys.argv[2] if len(sys.argv) > 2 else "results/pro/interventions.npz"
t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz"); d = np.load(src)
z, op, dx, rc, thr = t["z"], t["open"], float(t["dx"]), r["rc"], float(r["threshold_m"])
n = len(d["receptor"]); out = {k: [] for k in ("peak_base", "peak_changed", "final_base", "final_changed", "imbalance")}
t0 = time.time()
for c in range(0, n, 4):
    ii = np.arange(c, min(c + 4, n)); m = len(ii)
    zc = np.repeat(z[None], m, 0)
    for j, i in enumerate(ii):
        a, b, lo, hi = d["rect"][i]
        zc[j, a:b, lo:hi] += np.where(op[a:b, lo:hi], d["dz"][i], 0).astype(np.float32)   # open cells only
    zz = np.concatenate([np.repeat(z[None], m, 0), zc])                                    # base members, then changed
    two = lambda x: np.concatenate([x, x])
    o = simulate(zz, op, dx, rc, two(d["profile"][ii]), float(d["profile_dt_s"]), two(d["loss_mm_h"][ii]), two(d["t_end_s"][ii]))
    out["peak_base"].append(o["peak_depth"][:m]); out["peak_changed"].append(o["peak_depth"][m:])
    out["final_base"].append(o["final_depth"][:m]); out["final_changed"].append(o["final_depth"][m:])
    out["imbalance"].append(o["imbalance"].reshape(2, m).T)
    print(f"cases {ii[0]}..{ii[-1]}: {o['wall_s']:.0f}s", flush=True)
out = {k: np.concatenate(v) for k, v in out.items()}
k = np.arange(n); rcp = d["receptor"]
sb = out["peak_base"][k, rcp] >= thr; sc = out["peak_changed"][k, rcp] >= thr
fb = out["final_base"][k, rcp] >= thr; fc = out["final_changed"][k, rcp] >= thr
pb, pc = d["fill_base_wet"], d["fill_changed_wet"]
np.savez_compressed(dst, **out, receptor=rcp, solver_peak_base_wet=sb, solver_peak_changed_wet=sc,
                    solver_final_base_wet=fb, solver_final_changed_wet=fc,
                    flip_confirmed_peak=(sb == pb) & (sc == pc), flip_confirmed_final=(fb == pb) & (fc == pc),
                    wall_s=time.time() - t0, source=src)
print(f"total {time.time() - t0:.0f}s, max |imbalance| {np.abs(out['imbalance']).max():.1e}")
print("case rcp dz   pred    peak base->changed (m)        final base->changed (m)     peak? final?")
for i in range(n):
    print(f"{i:3d} {rcp[i]:4d} {d['dz'][i]:+.2f} {'wet' if pb[i] else 'dry'}->{'wet' if pc[i] else 'dry'}  "
          f"{out['peak_base'][i, rcp[i]]:.3f} -> {out['peak_changed'][i, rcp[i]]:.3f}   "
          f"{out['final_base'][i, rcp[i]]:.3f} -> {out['final_changed'][i, rcp[i]]:.3f}   "
          f"{'Y' if (sb[i] == pb[i]) & (sc[i] == pc[i]) else 'n'}  {'Y' if (fb[i] == pb[i]) & (fc[i] == pc[i]) else 'n'}")
print("confirmed on peak:", int(((sb == pb) & (sc == pc)).sum()), "of", n, "| on final:", int(((fb == pb) & (fc == pc)).sum()), "of", n)
