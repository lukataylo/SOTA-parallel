"""Score the suspects from the pool test, run singly (packed 120 m apart). A suspect is a miss of the map if it moves a building
more than 7.5 m from it by 1 cm or more in the solver."""
import glob, numpy as np
Q = np.load("shared/pool_split.npz"); rc = np.load("shared/receptors.npz")["rc"]; S = int(Q["storm"]); base = np.load("results/air/p1_chunks/base.npz")["peak"][S].astype(np.float64)
K = int(Q["n_packs"]); ch = np.full((K, 207), np.nan)
for f in sorted(glob.glob("results/air/pool_split/split_*.npz")): c = np.load(f); ch[c["k"]] = c["peak"] - base[None]
n = len(Q["r"]); D = np.hypot(Q["r"][:, None] - rc[None, :, 0], Q["c"][:, None] - rc[None, :, 1]); own = (D > 7.5) & (D <= 60.0)
got = ~np.isnan(ch[Q["pack_of"], 0]); eff = np.where(own, np.abs(ch[Q["pack_of"]]), 0).max(1); mover = (eff >= 0.01) & got
fp = Q["fill_change_any"] >= 0.001
print("suspects run: %d of %d" % (got.sum(), n))
print("single dismissed what-ifs that move a building (7.5 to 60 m away) by 1 cm or more: %d of %d" % (mover.sum(), got.sum()))
print("   of those, the fill model predicted a depth change of 1 mm or more at some building: %d; predicted nothing: %d" % ((mover & fp).sum(), (mover & ~fp).sum()))
print("   suspects where the fill model predicted nothing: %d, of which movers: %d | predicted a depth change: %d, of which movers: %d" % ((got & ~fp).sum(), (mover & ~fp).sum(), (got & fp).sum(), (mover & fp).sum()))
print("   largest effect, cm: median %.2f, p90 %.2f, max %.2f; distinct blocks among movers: %d" % (np.median(eff[got]) * 100, np.percentile(eff[got], 90) * 100, eff[got].max() * 100, len({(r, c) for r, c in zip(Q["r"][mover], Q["c"][mover])})))
dmin = np.where(own, D, 1e9); print("   movers: distance to the building they move, m: %s" % np.round(np.sort([D[i, np.where(own[i], np.abs(ch[Q["pack_of"][i]]), 0).argmax()] for i in np.flatnonzero(mover)]), 0).astype(int).tolist())
np.savez("results/air/pool_split_scored.npz", effect=eff, mover=mover, got=got)
