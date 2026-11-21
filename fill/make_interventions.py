"""Write 20 predicted flips for the Pro agent: (storm, receptor, 5x5 m patch raised or lowered 5 cm)."""
import numpy as np
d = np.load("results/air/decisive.npz"); c0, jobs, C = d["c0"], d["jobs"], d["crit_patch"]
LOSS = 12.0; DUR = 40; THR = 0.10
cap = lambda x: np.where(np.isfinite(x), x, 200.0)
shift = cap(C) - cap(c0)[None]                               # mm of net rain; +-inf handled as 200
cands = [(abs(shift[j, r]), j, r) for j in range(len(jobs)) for r in range(len(c0)) if abs(shift[j, r]) >= 6.0 and min(cap(C[j, r]), cap(c0[r])) < 110]
cands.sort(reverse=True)
used_r, used_j, pick = {}, set(), []
for s, j, r in cands:
    if used_r.get(r, 0) >= 2 or j in used_j: continue
    pick.append((j, r)); used_r[r] = used_r.get(r, 0) + 1; used_j.add(j)
    if len(pick) == 20: break
def profile_for_net(net_mm):
    m = DUR; t = (np.arange(m) + 0.5) / m; w = np.where(t <= 0.5, t / 0.5, (1 - t) / 0.5); w = w / w.sum()
    lo, hi = net_mm, net_mm + 40.0
    for _ in range(60):
        mid = (lo + hi) / 2; p = w * mid * 60.0
        if np.maximum(p - LOSS, 0).sum() / 60.0 < net_mm: lo = mid
        else: hi = mid
    p = np.zeros(60, np.float32); p[:m] = w * hi * 60.0; return p
out = dict(receptor=[], profile=[], net_mm=[], rect=[], dz=[], crit_base_mm=[], crit_changed_mm=[], fill_base_wet=[], fill_changed_wet=[])
for j, r in pick:
    a, b = cap(c0[r]), cap(C[j, r]); lo, hi = min(a, b), max(a, b)
    P = (lo + min(hi, lo + 30.0)) / 2                           # storm between the two critical depths
    rr, cc, dz, rad = jobs[j]; rr, cc, rad = int(rr), int(cc), int(rad)
    out["receptor"].append(r); out["profile"].append(profile_for_net(P)); out["net_mm"].append(P)
    out["rect"].append([max(rr - rad, 0), rr + rad + 1, max(cc - rad, 0), cc + rad + 1]); out["dz"].append(dz)
    out["crit_base_mm"].append(c0[r]); out["crit_changed_mm"].append(C[j, r]); out["fill_base_wet"].append(P >= a); out["fill_changed_wet"].append(P >= b)
o = {k: np.array(v) for k, v in out.items()}
np.savez("shared/interventions.npz", **o, loss_mm_h=np.full(len(pick), LOSS, np.float32), duration_s=np.full(len(pick), DUR * 60.0, np.float32),
         t_end_s=np.full(len(pick), DUR * 60.0 + 1200.0, np.float32), profile_dt_s=np.float32(60.0), threshold_m=np.float32(THR))
rc = np.load("shared/receptors.npz")["rc"]
for i, (j, r) in enumerate(pick):
    print("%2d receptor %3d at %s | patch rows %d-%d cols %d-%d %+.0f cm (%.0f m away) | critical %.1f -> %.1f mm | storm net %.1f mm | predicted %s -> %s" % (
        i, r, tuple(rc[r]), *o["rect"][i][:2], *o["rect"][i][2:], o["dz"][i] * 100, np.hypot(rc[r][0] - jobs[j][0], rc[r][1] - jobs[j][1]), o["crit_base_mm"][i], o["crit_changed_mm"][i], o["net_mm"][i],
        "wet" if o["fill_base_wet"][i] else "dry", "wet" if o["fill_changed_wet"][i] else "dry"))
print("distinct receptors", len(set(o["receptor"])), "raise", (o["dz"] > 0).sum(), "lower", (o["dz"] < 0).sum(), "dry->wet", (~o["fill_base_wet"] & o["fill_changed_wet"]).sum(), "wet->dry", (o["fill_base_wet"] & ~o["fill_changed_wet"]).sum())
