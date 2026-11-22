"""Peak-depth fields for the interactive 3D page: unchanged terrain and the five-square design, at 15, 35 and 70 mm. Writes results/air/render/fields_all.npz."""
import sys, numpy as np
sys.path.insert(0, "solver"); from flood import simulate
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; z, op, dx = t["z"], t["open"], float(t["dx"]); zc = z.copy()
for k, i, j in np.load("shared/map_design.npz")["blocks"]: sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], 0.05 if k == 0 else -0.05, 0).astype(np.float32)
Z = np.array([z, zc, zc]); o = simulate(Z, op, dx, rc, d["profile"][[0, 0, 2]], float(d["profile_dt_s"]), np.full(3, float(d["loss_mm_h"]), np.float32), np.full(3, float(d["t_end_s"]), np.float32), n_manning=0.015, return_fields=True)
a = np.load("results/air/render/fields.npz"); b = np.load("results/air/render/fields_design.npz"); pf = np.asarray(o["peak_field"]); pd = np.asarray(o["peak_depth"])
np.savez_compressed("results/air/render/fields_all.npz", base=np.array([pf[0], a["peak_field"][0], a["peak_field"][1]]), design=np.array([pf[1], b["peak_field"], pf[2]]), base_rc=np.array([pd[0], a["peak_depth"][0], a["peak_depth"][1]]), design_rc=np.array([pd[1], b["peak_depth"], pd[2]]))
