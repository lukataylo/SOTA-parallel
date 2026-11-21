"""Job 3 gate: partial fill against the settled JAX solver on synthetic streets (no gullies, 30 min settling)."""
import sys, json, time, numpy as np, jax, jax.numpy as jnp
sys.path.insert(0, "fill"); sys.path.insert(0, "prior")
from fillmodel import FillModel
from floodlab import make_street, make_sim
DX = 0.5; PS = np.array([5, 10, 20, 35, 60, 100, 160]) * 1e-3; T = 120.0; THR = 0.05
rows = []; agree = tot = 0; dagree = dtot = 0; diffs = []
for seed in range(1, 13):
    st = make_street(seed, DX); z = st["z"].astype(np.float64)
    outlet = np.zeros(z.shape, bool); outlet[:, 0] = True; outlet[:, -1] = True
    M = FillModel(z, np.ones(z.shape, bool), outlet, rainw=st["rainmask"])
    LL, out = M.run(PS)
    sim, nsteps, dt = make_sim(st, 1920.0, use_gullies=False)
    f = jax.jit(jax.vmap(lambda R: sim(jnp.array(st["z"]), R, T)[1]))
    H = np.array(f(jnp.array(PS / T)))
    cmp = st["open"] & ~outlet; cmp[:, :2] = False; cmp[:, -2:] = False
    for s, P in enumerate(PS):
        d = M.depth_field(LL, s); hs = H[s]
        a, b = d[cmp] >= THR, hs[cmp] >= THR
        agree += (a == b).sum(); tot += a.size
        either = a | b
        diffs.append((hs - d)[cmp][either])
        fd = np.array([(dw * d).sum() for dw in st["doorw"]]); sd = np.array([(dw * hs).sum() for dw in st["doorw"]])
        dagree += ((fd >= 0.01) == (sd >= 0.01)).sum(); dtot += len(fd)
        rows.append(dict(seed=seed, P_mm=float(P * 1e3), cells=int(a.size), fill_wet=int(a.sum()), solver_wet=int(b.sum()), mismatch=int((a != b).sum()),
                         fill_only=int((a & ~b).sum()), solver_only=int((~a & b).sum()), doors_fill=int((fd >= 0.01).sum()), doors_solver=int((sd >= 0.01).sum()),
                         door_mismatch=int(((fd >= 0.01) != (sd >= 0.01)).sum())))
    print("street", seed, "leaves", M.nb, [ (r["P_mm"], r["mismatch"], r["door_mismatch"]) for r in rows[-len(PS):] ], flush=True)
dd = np.concatenate(diffs)
print("CELL decisions (depth >= %.0f cm): agree %.4f of %d" % (THR * 100, agree / tot, tot))
print("  fill-only (false alarm) %d, solver-only (miss) %d" % (sum(r["fill_only"] for r in rows), sum(r["solver_only"] for r in rows)))
print("DOOR decisions (interior >= 1 cm): agree %.4f of %d; mismatches %d" % (dagree / dtot, dtot, dtot - dagree))
print("solver minus fill depth where either is wet, cm: p1 %.1f p10 %.1f median %.1f p90 %.1f p99 %.1f" % tuple(np.percentile(dd, [1, 10, 50, 90, 99]) * 100))
json.dump(rows, open("results/air/oracle_synthetic.json", "w"))
