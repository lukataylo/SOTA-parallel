"""Build the packed terrains for the bet G check. See docs/G_CRITERIA.md."""
import numpy as np
SEP = 120.0
d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; op = np.load("shared/terrain_512.npz")["open"]
cen = np.c_[(d["rect"][:, 0] + d["rect"][:, 1] - 1) / 2, (d["rect"][:, 2] + d["rect"][:, 3] - 1) / 2]; n = len(cen)
fill_moves = (np.abs(d["fill_changed_depth"] - d["fill_base_depth"][None]) >= 0.001).any(1)             # (case, receptor)
def conflict(i, j): return np.hypot(*(cen[i] - cen[j])) < SEP or (fill_moves[i] & fill_moves[j]).any()
def colour(order, cen_, conf):
    packs = []
    for i in order:
        for p in packs:
            if not any(conf(i, j) for j in p): p.append(i); break
        else: packs.append([i])
    return packs
deg = [sum(conflict(i, j) for j in range(n) if j != i) for i in range(n)]
packs = colour(sorted(range(n), key=lambda i: -deg[i]), cen, conflict)
print("120 control patches packed into %d terrains; sizes %s" % (len(packs), sorted(len(p) for p in packs)))
# planted movers
sc = np.load("results/air/p1_scored.npz"); dS = sc["dS"].astype(np.float64); dist = np.sqrt(((cen[:, None, :] - rc[None]) ** 2).sum(2)); far = dist > 7.5
big = np.abs(np.where(far[:, None, :], dS, 0)); movers = np.flatnonzero(big.max((1, 2)) >= 0.01)[:20]
at = np.load("results/air/atlas.npz"); dismissed = np.argwhere((at["n_moved"].max(0) == 0) & op)
dismissed = dismissed[(dismissed[:, 0] > 12) & (dismissed[:, 0] < 500) & (dismissed[:, 1] > 12) & (dismissed[:, 1] < 500)]
rng = np.random.default_rng(909); planted = []
for m in movers:
    storm = int(big[m].max(1).argmax()); pts = [cen[m]]; rows = []
    for k in rng.permutation(len(dismissed))[:4000]:
        p = dismissed[k].astype(float)
        if all(np.hypot(*(p - q)) >= SEP for q in pts): pts.append(p); rows.append((int(p[0]), int(p[1]), float(rng.choice([0.05, -0.05]))))
        if len(rows) == 31: break
    planted.append(dict(mover=int(m), storm=storm, extra=rows))
print("planted terrains: %d; dismissed patches per terrain: %s" % (len(planted), sorted(len(p["extra"]) for p in planted)))
np.savez("shared/pack_check.npz", pack_of=np.array([next(k for k, p in enumerate(packs) if i in p) for i in range(n)]), n_packs=len(packs), sep_m=SEP,
         planted_mover=np.array([p["mover"] for p in planted]), planted_storm=np.array([p["storm"] for p in planted]),
         planted_extra=np.array([p["extra"] + [(-1, -1, 0.0)] * (31 - len(p["extra"])) for p in planted]))
