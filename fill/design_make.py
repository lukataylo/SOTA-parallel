"""Choose a design from the solver map only: see docs/G_CRITERIA.md. Uses movers that have a true single run (confirm and trace stages)."""
import sys, glob, numpy as np
sys.path.insert(0, "fill"); import map_lib as L
rc = L.rc; F = np.load("results/air/map_final.npz"); cand = []
for k, (s, m) in enumerate((("raise", "air"), ("lower", "pro"))):
    d = f"results/{m}/map/confirm_s1_{s}"; P = np.load(f"{d}/plan.npz"); base = np.load(f"results/{m}/map/s1_{s}/base_start.npz")["peak"].astype(float)
    for f in sorted(glob.glob(f"{d}/k*.npz")):
        c = np.load(f)
        for t, pk in zip(c["k"], c["peak"]):
            if t < int(P["n_single"]): i, j = P["blocks"][t][0]; cand.append((k, int(i), int(j), pk - base))
thr = float(np.load("shared/receptors.npz")["threshold_m"]); b35 = np.load("results/air/map/s1_raise/base_start.npz")["peak"].astype(float); good = []
for k, i, j, ch in cand:
    D = np.hypot(5 * i + 2 - rc[:, 0], 5 * j + 2 - rc[:, 1]); far = np.where(D > L.NEAR, ch, 0); q = far.argmin()
    if far[q] <= -0.01 and ch.max() <= 0.003: good.append((far[q], k, i, j, int(q), ch))
good.sort(key=lambda g: g[0]); pick, seen = [], set()
for g in good:
    if g[4] not in seen and len(pick) < 5: pick.append(g); seen.add(g[4])
print("movers with a true single run: %d; lower a building 1 cm and raise none above 0.3 cm: %d; chosen: %d" % (len(cand), len(good), len(pick)))
for e, k, i, j, q, ch in pick: print("  %s block (%d,%d): building %d falls %.1f cm (base depth %.2f m), %.0f m away; receptors falling 1 cm: %d; largest rise %.2f cm" % (("raise", "lower")[k], i, j, q, -100 * e, b35[q], np.hypot(5 * i + 2 - rc[q, 0], 5 * j + 2 - rc[q, 1]), (ch <= -0.01).sum(), 100 * ch.max()))
np.savez("shared/map_design.npz", blocks=np.array([(k, i, j) for _, k, i, j, _, _ in pick]), target=np.array([g[4] for g in pick]), single=np.array([g[5] for g in pick]))
mv = F["mover"]; q = F["receptor"][mv]; e = F["effect"][mv]; b = np.where(np.nonzero(mv)[0] == 0, b35[q], np.load("results/pro/map/s1_lower/base_start.npz")["peak"].astype(float)[q])
print("of the 98 movers: take a building across 0.10 m: %d (into flood %d, out of flood %d); buildings already above 0.10 m: %d" % (((b >= thr) != (b + e >= thr)).sum(), ((b < thr) & (b + e >= thr)).sum(), ((b >= thr) & (b + e < thr)).sum(), (b >= thr).sum()))
