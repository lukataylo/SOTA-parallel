"""Peak-depth field at 35 mm with the five-square design from the map applied. Writes results/air/render/fields_design.npz."""
import sys, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); zc = z.copy()
for k, i, j in np.load("shared/map_design.npz")["blocks"]: sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], 0.05 if k == 0 else -0.05, 0).astype(np.float32)
o = simulate(zc[None], op, dx, rc, d["profile"][[1]], float(d["profile_dt_s"]), np.full(1, float(d["loss_mm_h"]), np.float32), np.full(1, float(d["t_end_s"]), np.float32), n_manning=0.015, return_fields=True)
np.savez_compressed("results/air/render/fields_design.npz", peak_field=np.asarray(o["peak_field"])[0], peak_depth=np.asarray(o["peak_depth"])[0])
