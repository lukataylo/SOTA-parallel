"""Pivot tasks for the Pro agent (docs/PIVOT.md): receptor time series and the order check.

uv run --with mlx --with numpy python solver/pivot_runs.py series|order
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from flood import simulate

t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz"); s = np.load("shared/storms_pilot.npz")
z, op, dx, rc, thr = t["z"], t["open"], float(t["dx"]), r["rc"], float(r["threshold_m"])
pdt = float(s["profile_step_s"])

if sys.argv[1] == "series":      # first 16 pilot storms, depth at every receptor every 30 s
    out = {}
    for c in (0, 8):
        ii = np.arange(c, c + 8)
        o = simulate(z, op, dx, rc, s["profile"][ii], pdt, s["loss_mm_h"][ii], s["duration_s"][ii] + 1200, series_dt_s=30.0)
        for k in ("series", "peak_depth", "final_depth", "imbalance"):
            out.setdefault(k, []).append(o[k])
        print(f"storms {c}..{c+7}: {o['wall_s']:.0f}s, max |imbalance| {np.abs(o['imbalance']).max():.1e}", flush=True)
    out = {k: np.concatenate(v) for k, v in out.items()}
    np.savez_compressed("results/pro/pilot_timeseries.npz", depth=out["series"], t_s=o["series_t_s"],
                        storm_index=np.arange(16), peak_depth=out["peak_depth"], final_depth=out["final_depth"],
                        t_end_s=s["duration_s"][:16] + 1200, imbalance=out["imbalance"])
    ref = np.load("results/pro/bruteforce_pilot.npz")["peak_depth"][:16]
    print("series shape", out["series"].shape, "| max |peak - pilot peak|", np.abs(out["peak_depth"] - ref).max(),
          "| max (peak - max of 30 s samples)", (out["peak_depth"] - np.nanmax(out["series"], 1)).max())

if sys.argv[1] == "order":       # larger storm (same shape and end time) must be at least as deep everywhere
    base = np.argsort(s["depth_mm"])[[12, 28, 44, 56]]
    fac = np.array([1.1, 1.2, 1.3, 1.2])
    prof = np.concatenate([s["profile"][base], s["profile"][base] * fac[:, None]])
    tend = np.tile(s["duration_s"][base] + 1200, 2)
    o = simulate(z, op, dx, rc, prof, pdt, np.tile(s["loss_mm_h"][base], 2), tend, return_fields=True)
    rows = []
    for j in range(4):
        dp = o["peak_depth"][j + 4] - o["peak_depth"][j]; df = o["final_depth"][j + 4] - o["final_depth"][j]
        fp = o["peak_field"][j + 4] - o["peak_field"][j]; ff = o["final_field"][j + 4] - o["final_field"][j]
        rows.append(dict(storm=int(base[j]), depth_mm=float(s["depth_mm"][base[j]]), factor=float(fac[j]),
                         min_peak_diff_receptors_m=float(dp.min()), min_final_diff_receptors_m=float(df.min()),
                         min_peak_diff_any_cell_m=float(fp.min()), min_final_diff_any_cell_m=float(ff.min()),
                         cells_final_lower_by_1mm=int((ff < -1e-3).sum()), cells_peak_lower_by_1mm=int((fp < -1e-3).sum()),
                         receptors_flooded_small=int((o["peak_depth"][j] >= thr).sum()),
                         receptors_flooded_large=int((o["peak_depth"][j + 4] >= thr).sum()),
                         flooded_small_not_large=int(((o["peak_depth"][j] >= thr) & (o["peak_depth"][j + 4] < thr)).sum())))
        print(rows[-1], flush=True)
    import json; json.dump(rows, open("results/pro/order_check.json", "w"), indent=1)
