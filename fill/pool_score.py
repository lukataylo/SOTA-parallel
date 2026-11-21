"""Score the pool test against docs/G_CRITERIA.md. A pool trips if any building's peak differs from the unchanged run by 1 cm or more."""
import glob, numpy as np
P = np.load("shared/pool_test.npz"); NP = int(P["n_pools"]); S = int(P["storm"]); rc = np.load("shared/receptors.npz")["rc"]
base = np.load("results/air/p1_chunks/base.npz")["peak"][S].astype(np.float64); K = 2 * NP + len(P["control_case"])
ch = np.full((K, 207), np.nan); wall = 0.0; imb = 0.0
for f in sorted(glob.glob("results/air/pool_test/pool_*.npz")):
    c = np.load(f); ch[c["k"]] = c["peak"] - base[None]; wall += float(c["wall_s"]); imb = max(imb, float(np.abs(c["imbalance"]).max()))
done = ~np.isnan(ch[:, 0]); mx = np.abs(ch).max(1); trip = mx >= 0.01
pools = np.arange(K) < 2 * NP; ctrl = ~pools
print("terrains run: %d of %d (pools %d of %d, controls %d of %d); wall %.0f s; max mass imbalance %.1e" % (done.sum(), K, (done & pools).sum(), 2 * NP, (done & ctrl).sum(), ctrl.sum(), wall, imb))
nb = np.array([(P["cls"] == (k % NP)).sum() for k in range(2 * NP)])
print("POOLS tripped (some building moves 1 cm): %d of %d run (line: at most 25%%) -> %s" % ((trip & pools & done).sum(), (pools & done).sum(), "ok so far" if (trip & pools & done).sum() <= 0.25 * max((pools & done).sum(), 1) else "OVER"))
print("   largest change per pool, cm: median %.2f, p90 %.2f, max %.2f; pools with largest change under 0.5 cm: %d" % (np.median(mx[pools & done]) * 100, np.percentile(mx[pools & done], 90) * 100, mx[pools & done].max() * 100, (mx[pools & done] < 0.005).sum()))
cleared = nb[(~trip & done)[:2 * NP]].sum(); print("   dismissed what-ifs cleared in untripped pools: %d of %d in the pools run so far" % (cleared, nb[done[:2 * NP]].sum()))
for k in np.flatnonzero(trip & pools & done):
    r = np.flatnonzero(np.abs(ch[k]) >= 0.01); pool = k % NP; br, bc = P["block_r"][P["cls"] == pool], P["block_c"][P["cls"] == pool]
    info = []
    for q in r:
        dd = np.hypot(br - rc[q, 0], bc - rc[q, 1]); info.append("receptor %d %+.1f cm (nearest pooled block %.0f m)" % (q, ch[k, q] * 100, dd.min()))
    print("   tripped: terrain %d (pool %d, %s): %s" % (k, pool, "flipped signs" if k >= NP else "signs as drawn", "; ".join(info)))
if (ctrl & done).any():
    print("POSITIVE CONTROLS tripped: %d of %d run (line: at least 8 of 9)" % ((trip & ctrl & done).sum(), (ctrl & done).sum()))
np.savez("results/air/pool_scored.npz", change=ch, tripped=trip, done=done)
