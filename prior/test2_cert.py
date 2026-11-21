"""Test 2: certified-dry bounds, checked against the full solver.
 (a) physical check: solver equilibrium water surface vs min-max fill level F.
 (b) mass certificate: door stays dry if rain volume < volume needed to raise a level
     surface to the threshold over the connected sub-threshold region at the door.
     No credit for drains or outflow, so it should be conservative.
 (c) static certificate: if fill level at the door front is below the threshold,
     a static pond can never reach it. Tested for violations from moving water.
Kill line: zero violations; mass bound within 2x of solver threshold."""
import json, sys, numpy as np, jax, jax.numpy as jnp
from scipy.ndimage import label
from floodlab import *
from test1_minmax import priority_flood
DX = 0.5; WET = 1e-3
PS = np.round(np.geomspace(8, 200, 18), 1); TS = [60., 180.]
rows = []; phys = []
S0, S1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 21)
REPAIR = len(sys.argv) > 3
for seed in range(S0, S1):
    st = make_street(seed, DX); z = st["z"].astype(np.float64); zj = jnp.array(st["z"])
    outlet = np.zeros(z.shape, bool); outlet[:, 0] = st["open"][:, 0]; outlet[:, -1] = st["open"][:, -1]
    F = priority_flood(z, outlet)
    A = st["rainmask"].sum() * DX * DX
    if seed <= 6:      # (a) heavy rain, no gullies, let it settle 30 min
        simL, _, _ = make_sim(st, 1800., use_gullies=False)
        _, h, _ = jax.jit(simL)(zj, 0.2 / 120, 120.); h = np.array(h)
        wet = (h > 0.01) & ~outlet
        diff = (z + h - F)[wet]
        phys.append(dict(seed=seed, wet_cells=int(wet.sum()), mean_abs_mm=float(np.abs(diff).mean() * 1000),
                         p99_abs_mm=float(np.percentile(np.abs(diff), 99) * 1000), max_above_mm=float(diff.max() * 1000),
                         fillable_but_dry=int(((F - z > 0.01) & (h < 0.001)).sum()), fillable=int((F - z > 0.01).sum())))
        print("phys", json.dumps(phys[-1]), flush=True)
    sim, _, _ = make_sim(st, 300.)
    Rg = jnp.array([[P * 1e-3 / T for P in PS] for T in TS]); Tg = jnp.array([[T] * len(PS) for T in TS])
    D = np.array(jax.jit(lambda z: jax.vmap(jax.vmap(lambda R, T: sim(z, R, T)[0]))(Rg, Tg))(zj))   # (T,P,door)
    for di, d in enumerate(st["doors"]):
        fy, fx = d["front"]; zt = d["zt"]
        lab, _ = label(z < zt); comp = lab == lab[fy, fx]
        Vneed = ((zt - z)[comp]).sum() * DX * DX
        Pcert = Vneed / A * 1000
        if REPAIR and z[fy, d["cols"]].max() >= zt: Pcert = 0.0     # ground at the door is not below the threshold: refuse to certify
        static_dry = bool(F[fy, fx] < zt)
        for ti, T in enumerate(TS):
            wet = D[ti, :, di] > WET
            Ptrue = float(PS[wet][0]) if wet.any() else None
            viol = bool(wet[PS < Pcert].any())
            rows.append(dict(seed=seed, door=di, T=T, t_cm=d["t"] * 100, sunk=d["sunk"], Pcert=float(Pcert), Ptrue=Ptrue,
                             viol=viol, static_dry=static_dry, margin_cm=float((zt - F[fy, fx]) * 100),
                             touches_outlet=bool((comp & outlet).any())))
    print("street", seed, "done", flush=True)
json.dump(dict(rows=rows, phys=phys, PS=PS.tolist()), open("res_test2%s.json" % ("_val" if REPAIR else ""), "w"))
R = rows
print("cases", len(R), "flooded within sweep", sum(r["Ptrue"] is not None for r in R))
print("MASS certificate violations:", sum(r["viol"] for r in R))
ratio = np.array([r["Ptrue"] / r["Pcert"] for r in R if r["Ptrue"] and r["Pcert"] > 0])
print("refused", sum(r["Pcert"] == 0 for r in R))
dry = sum((PS < (r["Ptrue"] or 1e9)).sum() for r in R); cert = sum(((PS < r["Pcert"]) & (PS < (r["Ptrue"] or 1e9))).sum() for r in R); print("dry cases", dry, "certified share %.3f" % (cert / dry))
print("tightness Ptrue/Pcert: median %.2f, p10 %.2f, p90 %.2f, min %.2f, share within 2x: %.2f" % (
    np.median(ratio), np.percentile(ratio, 10), np.percentile(ratio, 90), ratio.min(), (ratio <= 2).mean()))
for T in TS:
    rr = np.array([r["Ptrue"] / r["Pcert"] for r in R if r["Ptrue"] and r["Pcert"] > 0 and r["T"] == T]); print(" T", T, "median ratio %.2f n %d" % (np.median(rr), len(rr)))
sd = [r for r in R if r["static_dry"]]
sv = [r for r in sd if r["Ptrue"] is not None]
print("STATIC certificate: 'never floods' cases", len(sd), "violated", len(sv))
if sv:
    print(" violated margins cm: min %.1f max %.1f ; lowest violating P mm: %.0f" % (
        min(r["margin_cm"] for r in sv), max(r["margin_cm"] for r in sv), min(r["Ptrue"] for r in sv)))
    for m in (2, 5, 8, 12):
        a = [r for r in sd if r["margin_cm"] > m]; print("  margin >%d cm: cases %d violated %d" % (m, len(a), sum(r["Ptrue"] is not None for r in a)))
