"""Local split of the tripped pools. For each pool where a building more than 7.5 m from every pooled block moved by 1 cm,
the suspects are the pooled blocks within 60 m of that building (no single patch reached further than 57 m in the 360 single runs).
Each suspect is then run on its own sign, packed 120 m apart. Also records what the fill model predicts for each suspect at this storm."""
import sys, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
P = np.load("shared/pool_test.npz"); NP = int(P["n_pools"]); rc = np.load("shared/receptors.npz")["rc"]; sc = np.load("results/air/pool_scored.npz"); ch, done = sc["change"], sc["done"]
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; d = np.load("shared/p1_cases.npz"); NET = float(d["net_mm"][int(P["storm"])]) * 1e-3
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
sus = {}
for k in np.flatnonzero(done[:2 * NP]):
    pool = k % NP; m = P["cls"] == pool; br, bc, par = P["block_r"][m], P["block_c"][m], P["parity"][m]; flip = k >= NP
    D = np.sqrt((br[:, None] - rc[None, :, 0]) ** 2 + (bc[:, None] - rc[None, :, 1]) ** 2); far = D.min(0) > 7.5
    for q in np.flatnonzero((np.abs(ch[k]) >= 0.01) & far):
        for b in np.flatnonzero(D[:, q] <= 60.0):
            dz = 0.05 if (par[b] == 0) != flip else -0.05; sus.setdefault((int(br[b]), int(bc[b]), dz), set()).add(int(q))
S = sorted(sus); print("tripped pools (far receptors): %d; suspect (block, sign) what-ifs: %d" % (len({1 for _ in S}) and sum(1 for k in np.flatnonzero(done[:2 * NP]) if True) * 0 + len(set()) or 0, len(S)))
def fill_depth(job):
    r, c, dz = job; z = z0.copy(); sl = (slice(r - 2, r + 3), slice(c - 2, c + 3)); z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    M = FillModel(z, op, outlet); LL, _ = M.run(np.array([NET])); return M.depth_at(LL, rc)[0]
if __name__ == "__main__":
    M0 = FillModel(z0, op, outlet); LL, _ = M0.run(np.array([NET])); base = M0.depth_at(LL, rc)[0]
    with mp.Pool(8) as p: FD = np.array(p.map(fill_depth, S, chunksize=4))
    fpred = np.array([np.abs(FD[i] - base)[sorted(sus[s])].max() for i, s in enumerate(S)]); fany = np.abs(FD - base[None]).max(1)
    print("suspects: %d. Fill model predicts a depth change of 1 mm or more at the tripped building for %d of them; at any building for %d" % (len(S), (fpred >= 0.001).sum(), (fany >= 0.001).sum()))
    # pack suspects 120 m apart
    cen = np.array([(r, c) for r, c, _ in S], float); packs = []
    for i in np.argsort(-fpred):
        for p_ in packs:
            if all(np.hypot(*(cen[i] - cen[j])) >= 120.0 for j in p_): p_.append(int(i)); break
        else: packs.append([int(i)])
    print("packed into %d terrains (sizes %s)" % (len(packs), sorted(len(p_) for p_ in packs)))
    np.savez("shared/pool_split.npz", r=np.array([s[0] for s in S]), c=np.array([s[1] for s in S]), dz=np.array([s[2] for s in S]), pack_of=np.array([next(k for k, p_ in enumerate(packs) if i in p_) for i in range(len(S))]),
             n_packs=len(packs), fill_change_at_tripped=fpred, fill_change_any=fany, tripped_receptors=np.array([sorted(sus[s]) + [-1] * (8 - len(sus[s])) for s in S])[:, :8], storm=int(P["storm"]))
