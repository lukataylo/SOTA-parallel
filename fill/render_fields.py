"""Peak-depth field of the unchanged terrain at the 35 and 70 mm storms, for the 3D picture. Writes results/air/render/fields.npz."""
import sys, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"])
o = simulate(np.repeat(z[None], 2, 0), op, dx, rc, d["profile"][[1, 2]], float(d["profile_dt_s"]), np.full(2, float(d["loss_mm_h"]), np.float32), np.full(2, float(d["t_end_s"]), np.float32), n_manning=0.015, return_fields=True)
print({k: np.asarray(v).shape for k, v in o.items()}); np.savez_compressed("results/air/render/fields.npz", **{k: np.asarray(v) for k, v in o.items()})
