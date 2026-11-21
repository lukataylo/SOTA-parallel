"""Score the audit against docs/AUDIT_CRITERIA.md. No thresholds are chosen here.
  uv run --with numpy --with scipy python fill/audit_score.py 1"""
import sys, glob, numpy as np
from scipy.stats import beta
S = int(sys.argv[1]); Q = np.load("shared/audit.npz"); rc = np.load("shared/receptors.npz")["rc"]; r, c, pk, K = Q["r"], Q["c"], Q["pack_of"], int(Q["n_packs"])
peak = np.full((K + 1, len(rc)), np.nan); imb = 0.0
for f in glob.glob(f"results/pro/audit/s{S}/audit_*.npz"):
    o = np.load(f); peak[o["k"]] = o["peak"]; imb = max(imb, float(np.abs(o["imbalance"]).max()))
assert not np.isnan(peak[K]).any(), "unchanged terrain not run yet"
ch = peak[:K] - peak[K][None]; done = ~np.isnan(ch[:, 0]); have = done[pk]
D = np.hypot(r[:, None] - rc[None, :, 0], c[:, None] - rc[None, :, 1]); win = (D > 7.5) & (D <= 60.0)
sol = np.where(win & have[:, None], np.abs(ch[pk]), 0.0); smax = sol.max(1); mover = smax >= 0.01; flag = Q["fill_max"][:, S] >= 0.001
ci = lambda k, n: (beta.ppf(0.025, k, n - k + 1) if k else 0.0, beta.ppf(0.975, k + 1, n - k) if k < n else 1.0)
print("storm %d (%.0f mm net): terrains run %d of %d; what-ifs scored %d of %d; max mass imbalance %.1e" % (S, Q["net_mm"][S], done.sum(), K, have.sum(), len(r), imb))
for nm, m in (("DISMISSED", ~flag & have), ("FLAGGED", flag & have)):
    k, n = int((mover & m).sum()), int(m.sum()); lo, hi = ci(k, n) if n else (0, 0)
    print("%s what-ifs: %d; move a building 7.5 to 60 m away by 1 cm: %d (%.2f%%, 95%% interval %.2f%% to %.2f%%)" % (nm, n, k, 100 * k / max(n, 1), 100 * lo, 100 * hi))
k, n = int((mover & ~flag & have).sum()), int((~flag & have).sum())
print("MISS RATE line (at most 1%%): %s. Mythos's line (at most 2 misses): %s" % ("PASS" if k <= 0.01 * n else "FAIL", "PASS" if k <= 2 else "FAIL"))
nm_ = int((mover & have).sum()); print("RECALL in the sample: %d of %d movers flagged%s" % ((mover & flag & have).sum(), nm_, " (%.0f%%)" % (100 * (mover & flag & have).sum() / nm_) if nm_ else ""))
print("   weighted to all open ground: dismissed movers per flagged mover = %.2f" % ((mover & ~flag & have).sum() / max((mover & flag & have).sum(), 1)))
for i in np.flatnonzero(mover & ~flag & have):
    q = sol[i].argmax(); print("   missed: block (%d, %d) %+.0f cm -> receptor %d at %.0f m, %+.1f cm; fill predicted %+.2f mm there" % (r[i], c[i], Q["dz"][i] * 100, q, D[i, q], ch[pk[i], q] * 100, Q["fill_change"][i, S, q] * 1e3))
near = (D <= 60.0)[:, None, :] & (np.arange(K)[None, :, None] == pk[:, None, None]) if False else None
un = 0
for k_ in np.flatnonzero(done):
    m = pk == k_; cov = (D[m] <= 60.0).any(0); un += int(((np.abs(ch[k_]) >= 0.01) & ~cov).sum())
print("receptor moves of 1 cm with no block within 60 m (unattributed): %d" % un)
big = smax[~flag & have] * 100; print("dismissed: largest change per what-if, cm: median %.3f, p99 %.2f, max %.2f; at 0.5 cm or more: %d" % (np.median(big), np.percentile(big, 99), big.max(), (big >= 0.5).sum()))
np.savez(f"results/pro/audit_scored_s{S}.npz", solver_max=smax, mover=mover, flagged=flag, scored=have)
