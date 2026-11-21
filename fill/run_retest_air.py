"""Run the retest cases on this machine with the Pro's solver (same code path as solver/interventions.py)."""
import sys, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz"); d = np.load("shared/interventions_retest.npz")
z, op, dx, rc, thr = t["z"], t["open"], float(t["dx"]), r["rc"], 0.10
n = len(d["receptor"]); out = {k: [] for k in ("peak_base", "peak_changed", "final_base", "final_changed", "imbalance")}; t0 = time.time()
for c in range(0, n, 4):
    ii = np.arange(c, min(c + 4, n)); m = len(ii); zc = np.repeat(z[None], m, 0)
    for j, i in enumerate(ii):
        a, b, lo, hi = d["rect"][i]; zc[j, a:b, lo:hi] += np.where(op[a:b, lo:hi], d["dz"][i], 0).astype(np.float32)
    zz = np.concatenate([np.repeat(z[None], m, 0), zc]); two = lambda x: np.concatenate([x, x])
    o = simulate(zz, op, dx, rc, two(d["profile"][ii]), float(d["profile_dt_s"]), two(d["loss_mm_h"][ii]), two(d["t_end_s"][ii]))
    out["peak_base"].append(o["peak_depth"][:m]); out["peak_changed"].append(o["peak_depth"][m:]); out["final_base"].append(o["final_depth"][:m]); out["final_changed"].append(o["final_depth"][m:]); out["imbalance"].append(o["imbalance"].reshape(2, m).T)
    print(f"cases {ii[0]}..{ii[-1]} done, {time.time() - t0:.0f}s", flush=True)
out = {k: np.concatenate(v) for k, v in out.items()}
np.savez_compressed("results/air/interventions_retest.npz", **out, receptor=d["receptor"], wall_s=time.time() - t0, machine="M4 Air")
k = np.arange(n); rcp = d["receptor"]; pb, pc = d["pred_peak_base_m"], d["pred_peak_changed_m"]; sb, sc = out["peak_base"][k, rcp], out["peak_changed"][k, rcp]
ok = ((sb >= thr) == (pb >= thr)) & ((sc >= thr) == (pc >= thr))
for i in range(n):
    print("%2d rec %3d %3.0f m %+.0f cm | predicted %.3f -> %.3f | solver %.3f -> %.3f | %s" % (i, rcp[i], d["distance_m"][i], d["dz"][i] * 100, pb[i], pc[i], sb[i], sc[i], "FLIP CONFIRMED" if ok[i] else ("direction ok" if np.sign(sc[i] - sb[i]) == np.sign(pc[i] - pb[i]) else "wrong direction")))
print("CONFIRMED %d of %d | direction right %d | base-peak prediction error cm: median %.1f max %.1f | change prediction error cm: median %.1f max %.1f | max imbalance %.1e" % (
    ok.sum(), n, (np.sign(sc - sb) == np.sign(pc - pb)).sum(), np.median(np.abs(sb - pb)) * 100, np.abs(sb - pb).max() * 100, np.median(np.abs((sc - sb) - (pc - pb))) * 100, np.abs((sc - sb) - (pc - pb)).max() * 100, np.abs(out["imbalance"]).max()))
