"""Confirm stage for the map: re-run this sign's movers. First 40 runs are true singles of randomly drawn movers; the rest are movers repacked 300 m apart.
Capped at 100 runs. uv run --with mlx --with numpy python fill/map_confirm.py <raise|lower> <air|pro>"""
import sys, os, time, numpy as np
sys.path.insert(0, "solver"); sys.path.insert(0, "fill"); from flood import simulate; import map_lib as L
SIGN, MACH = sys.argv[1], sys.argv[2]; DZ = 0.05 if SIGN == "raise" else -0.05; out = f"results/{MACH}/map/confirm_s1_{SIGN}"; os.makedirs(out, exist_ok=True)
plan = f"{out}/plan.npz"
if not os.path.exists(plan):
    rec, _ = L.attribute(SIGN); mv = sorted([b for b, r in rec.items() if abs(r["effect"]) >= L.THR], key=lambda b: -abs(rec[b]["effect"]))
    rng = np.random.default_rng(7); single = [mv[k] for k in sorted(rng.choice(len(mv), min(40, len(mv)), replace=False))]; packs = []
    for b in mv:
        for p_ in packs:
            if all(5 * np.hypot(b[0] - a[0], b[1] - a[1]) >= 300 for a in p_): p_.append(b); break
        else: packs.append([b])
    T = [[b] for b in single] + packs[:60]; n = max(len(p_) for p_ in T)
    np.savez(plan, blocks=np.array([p_ + [(-1, -1)] * (n - len(p_)) for p_ in T]), n_single=len(single), n_movers=len(mv)); print("movers %d; true singles %d; repacked terrains %d of %d" % (len(mv), len(single), min(60, len(packs)), len(packs)))
Q = np.load(plan)["blocks"]; t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); z, op, dx = t["z"], t["open"], float(t["dx"])
def terrain(k):
    zc = z.copy()
    for i, j in Q[k]:
        if i >= 0: sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); zc[sl] += np.where(op[sl], DZ, 0).astype(np.float32)
    return zc
for c in range(0, len(Q), 6):
    f = f"{out}/k{c:03d}.npz"
    if os.path.exists(f): continue
    kk = np.arange(c, min(c + 6, len(Q))); m = len(kk); t0 = time.time()
    o = simulate(np.array([terrain(k) for k in kk]), op, dx, L.rc, np.repeat(d["profile"][1][None], m, 0), float(d["profile_dt_s"]), np.full(m, float(d["loss_mm_h"]), np.float32), np.full(m, float(d["t_end_s"]), np.float32))
    np.savez(f + ".tmp.npz", k=kk, peak=o["peak_depth"], imbalance=o["imbalance"], wall_s=time.time() - t0); os.replace(f + ".tmp.npz", f); print("confirm %d-%d: %.0fs" % (kk[0], kk[-1], time.time() - t0), flush=True)
print("done")
