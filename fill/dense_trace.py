"""Trace of the one unexplained move in the dense re-map: lower block (48,56) alone, 35 mm. Writes results/air/final/dense/trace_48_56.npz."""
import sys, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
zc = z.copy(); sl = (slice(240, 245), slice(280, 285)); zc[sl] -= np.where(op[sl], 0.05, 0).astype(np.float32)
o = simulate(zc[None], op, dx, rc, d["profile"][1][None], float(d["profile_dt_s"]), np.full(1, float(d["loss_mm_h"]), np.float32), np.full(1, float(d["t_end_s"]), np.float32), n_manning=0.015)
pk = np.asarray(o["peak_depth"])[0]; np.savez("results/air/final/dense/trace_48_56.npz", peak=pk)
ch = pk.astype(float) - np.load("results/air/final/dense/base.npz")["peak"].astype(float)
print("alone: receptor 206 changes %.4f cm; largest change at any receptor %.4f cm (receptor %d)" % (100 * ch[206], 100 * ch[np.abs(ch).argmax()], np.abs(ch).argmax()))
