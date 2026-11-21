"""Correctness checks 1, 2, 3, 5 from docs/BRIEF_PRO.md. Writes results/pro/checks.json.

uv run --with mlx --with numpy --with jax --with scipy python solver/checks.py [1 2 3 5]
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "prior"))
from flood import simulate

which = set(sys.argv[1:]) or {"1", "3", "25"}
OUT = "results/pro/checks.json"
os.makedirs("results/pro", exist_ok=True)
res = json.load(open(OUT)) if os.path.exists(OUT) else {}


def shared():
    t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz")
    return t["z"], t["open"], float(t["dx"]), r["rc"], float(r["threshold_m"])


if "1" in which:   # agreement with the JAX reference on a synthetic street
    import jax.numpy as jnp, jax
    import floodlab
    st = floodlab.make_street(1, 0.25)
    R, T = 60e-3 / 120, 120.0
    sim, nsteps, dt = floodlab.make_sim(st, 300., use_gullies=False)
    d_ref, h_ref, acc = jax.jit(sim)(jnp.array(st["z"]), R, T)
    d_ref, h_ref = np.array(d_ref), np.array(h_ref)
    doors = np.stack([d["mask"] for d in st["doors"]])
    cells = np.argwhere(doors.any(0))
    kw = dict(rain_mask=st["rainmask"] > 0, return_fields=True)
    args = (st["z"], np.ones_like(st["z"], bool), 0.25, cells, [[R * 3.6e6]], T, 0.0, 300.0)
    door_mean = lambda f: np.array([f[m].mean() for m in doors])
    r1 = {}
    for name, extra in (("same_dt", dict(dt_fixed=dt)), ("adaptive_dt", {})):
        o = simulate(*args, **kw, **extra)
        r1[name] = dict(
            max_abs_final_field_diff_m=float(np.abs(o["final_field"][0] - h_ref).max()),
            max_abs_final_door_diff_m=float(np.abs(door_mean(o["final_field"][0]) - door_mean(h_ref)).max()),
            max_abs_peak_door_diff_m=float(np.abs(door_mean(o["peak_field"][0]) - d_ref).max()),
            steps=int(o["nsteps"][0]), imbalance=float(o["imbalance"][0]))
    r1["ref_peak_door_depth_m"] = [round(float(x), 4) for x in d_ref]
    r1["ref_steps"] = int(nsteps)
    res["check1_jax_agreement"] = r1
    print(json.dumps(r1, indent=1))

if "3" in which:   # lake at rest on the real terrain: still water must stay still
    z, op, dx, rc, thr = shared()
    r3 = {}
    for L in (3.0, 4.0):
        h0 = np.where(op, np.maximum(L - z, 0), 0).astype(np.float32)
        o = simulate(z, op, dx, rc, np.zeros((1, 1)), 60.0, 0.0, 600.0, outflow=False, h0=h0, return_fields=True)
        r3[f"level_{L}m"] = dict(wet_cells=int((h0 > 0).sum()), max_depth_m=float(h0.max()),
                                 max_abs_depth_change_m=float(np.abs(o["final_field"][0] - h0).max()),
                                 steps=int(o["nsteps"][0]), imbalance=float(o["imbalance"][0]))
    res["check3_lake_at_rest"] = r3
    print(json.dumps(r3, indent=1))

if "25" in which:  # mass balance on real terrain at 1 m, then the same storms at 2 m
    z, op, dx, rc, thr = shared()
    s = np.load("shared/storms_pilot.npz")
    pick = np.argsort(s["depth_mm"])[3::8]                      # 8 storms spread across the depth range
    a = (s["profile"][pick], float(s["profile_step_s"]), s["loss_mm_h"][pick], s["duration_s"][pick] + 1200)
    o1 = simulate(z, op, dx, rc, *a)
    res["check2_mass_balance_1m"] = dict(
        storms=pick.tolist(), depth_mm=s["depth_mm"][pick].round(1).tolist(),
        imbalance=o1["imbalance"].tolist(), max_abs_imbalance=float(np.abs(o1["imbalance"]).max()),
        net_rain_m3=o1["rain_net_m3"].round(0).tolist(), stored_m3=o1["stored_m3"].round(0).tolist(),
        boundary_m3=o1["boundary_m3"].round(0).tolist(), hmax_m=o1["hmax"].round(2).tolist(),
        wall_s=o1["wall_s"], mcell_steps_per_s=o1["cell_steps_per_s"] / 1e6, steps=o1["nsteps"].tolist())
    print(json.dumps(res["check2_mass_balance_1m"], indent=1))
    # 2 m grid: a coarse cell is open if at least 2 of its 4 cells are open; height = mean of its open cells
    o4 = op.reshape(256, 2, 256, 2); z4 = np.where(op, z, 0).reshape(256, 2, 256, 2)
    cnt = o4.sum((1, 3)); op2 = cnt >= 2
    z2 = np.where(op2, z4.sum((1, 3)) / np.maximum(cnt, 1), 25.0).astype(np.float32)
    rc2 = rc // 2; ok = op2[rc2[:, 0], rc2[:, 1]]
    o2 = simulate(z2, op2, 2 * dx, rc2, *a)
    f1 = o1["peak_depth"][:, ok] >= thr; f2 = o2["peak_depth"][:, ok] >= thr
    res["check5_resolution"] = dict(
        receptors_compared=int(ok.sum()), receptors_dropped_closed_at_2m=int((~ok).sum()),
        decision_agreement=float((f1 == f2).mean()),
        flooded_1m=int(f1.sum()), flooded_2m=int(f2.sum()), cases=int(f1.size),
        flooded_1m_only=int((f1 & ~f2).sum()), flooded_2m_only=int((~f1 & f2).sum()),
        median_abs_peak_diff_m=float(np.median(np.abs(o1["peak_depth"][:, ok] - o2["peak_depth"][:, ok]))),
        p95_abs_peak_diff_m=float(np.percentile(np.abs(o1["peak_depth"][:, ok] - o2["peak_depth"][:, ok]), 95)),
        max_abs_imbalance_2m=float(np.abs(o2["imbalance"]).max()), wall_s_2m=o2["wall_s"],
        per_storm_agreement=(f1 == f2).mean(1).round(3).tolist())
    print(json.dumps(res["check5_resolution"], indent=1))
    np.savez_compressed("results/pro/check_1m_vs_2m.npz", storm_index=pick, peak_1m=o1["peak_depth"],
                        peak_2m=o2["peak_depth"], receptor_ok_at_2m=ok)

json.dump(res, open(OUT, "w"), indent=1)
