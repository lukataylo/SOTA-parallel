"""Shared reading and attribution for the complete solver map (fill/map_run.py)."""
import glob, os, numpy as np
P, S, THR, NEAR, FAR = 30, 1, 0.01, 7.5, 75.0
op = np.load("shared/terrain_512.npz")["open"]; rc = np.load("shared/receptors.npz")["rc"]
def blocks_of(col): return [(i, j) for i in range(col // P or P, 101, P) for j in range(col % P or P, 101, P) if op[5 * i:5 * i + 5, 5 * j:5 * j + 5].any()]
def load(sign):
    """Returns base peak, dict colour -> change at receptors, integrity numbers."""
    files = {}; imb = 0.0; wall = []
    for m in ("air", "pro"):
        for f in glob.glob(f"results/{m}/map/s{S}_{sign}/c*.npz"): files.setdefault(int(os.path.basename(f)[1:4]), f)
    b = [np.load(f)["peak"].astype(np.float64) for m in ("air", "pro") for f in sorted(glob.glob(f"results/{m}/map/s{S}_{sign}/base_*.npz"))]
    if not b: return None, {}, {}
    ch = {}
    for c, f in files.items(): q = np.load(f); ch[c] = q["peak"].astype(np.float64) - b[0]; imb = max(imb, abs(float(q["imbalance"]))); wall.append(float(q["wall_s"]))
    return b[0], ch, dict(max_imbalance=imb, base_spread=max(np.abs(x - b[0]).max() for x in b), n_base=len(b), wall_s=float(np.sum(wall)))
def attribute(sign):
    """Per block: largest change at a receptor more than NEAR m away, attributed to the nearest block in the run. Returns records and counts."""
    base, ch, integ = load(sign); rec = {}; moved = unatt = 0
    for c, dch in ch.items():
        B = blocks_of(c); cen = np.array([(5 * i + 2, 5 * j + 2) for i, j in B], float); D = np.hypot(cen[:, None, 0] - rc[None, :, 0], cen[:, None, 1] - rc[None, :, 1]); near = D.argmin(0); dn = D.min(0)
        for k, b in enumerate(B): rec[b] = dict(effect=0.0, receptor=-1, dist=0.0, near_effect=0.0, colour=c)
        for q in np.flatnonzero(np.abs(dch) >= THR):
            moved += 1
            if dn[q] > FAR: unatt += 1; continue
            r = rec[B[near[q]]]
            if dn[q] <= NEAR: r["near_effect"] = max(r["near_effect"], abs(dch[q]), key=abs)
            elif abs(dch[q]) > abs(r["effect"]): r.update(effect=float(dch[q]), receptor=int(q), dist=float(dn[q]))
    return rec, dict(runs=len(ch), whatifs=len(rec), moved=moved, unattributed=unatt, **integ)
