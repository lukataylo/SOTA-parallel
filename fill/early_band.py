"""First real comparison: fill depth against solver peak depth at all receptors (8 pilot storms from the Pro's resolution check)."""
import numpy as np
c = np.load("results/pro/check_1m_vs_2m.npz"); idx = c["storm_index"]; pk = c["peak_1m"].astype(np.float64)
F = np.load("results/air/fill_pilot.npz")["fill_depth"].astype(np.float64)[idx]
P = np.load("shared/storms_pilot.npz"); THR = 0.10
print("storms (net mm):", np.round(P["net_depth_mm"][idx], 1), "duration min:", (P["duration_s"][idx] / 60).astype(int))
sw, fw = pk >= THR, F >= THR
print("pairs %d | solver wet %d, fill wet %d | both wet %d, both dry %d | MISS (solver wet, fill dry) %d | false alarm (fill wet, solver dry) %d | agreement %.3f" % (
    sw.size, sw.sum(), fw.sum(), (sw & fw).sum(), (~sw & ~fw).sum(), (sw & ~fw).sum(), (~sw & fw).sum(), (sw == fw).mean()))
d = pk - F
print("solver peak minus fill depth, cm: p1 %.1f p10 %.1f median %.1f p90 %.1f p99 %.1f max %.1f" % tuple(np.r_[np.percentile(d, [1, 10, 50, 90, 99]), d.max()] * 100))
dry = F == 0
print("receptor-storm pairs with zero fill depth: %d; of those solver peak >= 10 cm: %d, >= 5 cm: %d, >= 2 cm: %d; max solver peak %.2f m" % (dry.sum(), (pk[dry] >= .10).sum(), (pk[dry] >= .05).sum(), (pk[dry] >= .02).sum(), pk[dry].max()))
miss = sw & ~fw
print("misses: fill depth at those pairs cm:", np.round(np.sort(F[miss])[:20] * 100, 1), "... solver peak cm:", np.round(np.sort(pk[miss])[-10:] * 100, 1))
print("misses per storm:", miss.sum(1), " receptors ever missed:", miss.any(0).sum())
fa = ~sw & fw
print("false alarms: solver peak at those cm:", np.round(np.sort(pk[fa])[:10] * 100, 1), " fill cm:", np.round(np.sort(F[fa])[-10:] * 100, 1))
# smallest symmetric-in-depth band that would have caught every miss and false alarm
need_lo = (THR - F[miss]).max() if miss.any() else 0; need_hi = (F[fa] - THR).max() if fa.any() else 0
print("band needed to catch all: fill depth from %.1f cm below to %.1f cm above the threshold" % (need_lo * 100, need_hi * 100))
und = (F > THR - need_lo - 1e-9) & (F < THR + need_hi + 1e-9)
print("with that band: undecided pairs %.3f; storms fully decided %d of 8; site alone decided %d of 8" % (und.mean(), (~und.any(1)).sum(), (~und[:, -1]).sum()))
print("site: fill cm", np.round(F[:, -1] * 100, 1), "solver peak cm", np.round(pk[:, -1] * 100, 1))
