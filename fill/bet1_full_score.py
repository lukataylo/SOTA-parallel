"""Score the Bet 1 full solver run on whatever terrains have all three arms. Same rule as the pilot (fill/bet1_pilot_score.py):
flooding judged against a fixed reference level; receptors whose critical rain lies inside the ladder in all but one terrain, in every arm.
Arms: A error everywhere, B error removed on the chosen 1%, C error removed on a random 1%. Pass line from docs/BETS.md: B/A at most 0.75."""
import numpy as np, os
out = "results/pro/bet1_full"; su = np.load(f"{out}/setup.npz"); L = su["levels_net_mm"]
z0 = np.load("shared/terrain_512.npz")["z"]; rc = np.load("shared/receptors.npz")["rc"]; REF = z0[rc[:, 0], rc[:, 1]] + 0.10
terr = [t for t in range(int(su["n_terrains"])) if all(os.path.exists(f"{out}/t{t:03d}_{a}.npz") for a in "ABC")]
def crit(arm):
    C = np.full((len(terr), len(rc)), np.nan)
    for i, t in enumerate(terr):
        d = np.load(f"{out}/t{t:03d}_{arm}.npz"); ex = d["peak"] + d["ground_at_receptors"][None] - REF[None]
        for r in range(len(rc)):
            w = ex[:, r] >= 0
            if not w.any(): C[i, r] = np.inf
            elif w[0]: C[i, r] = -np.inf
            else: k = np.argmax(w); C[i, r] = L[k - 1] + (L[k] - L[k - 1]) * (0 - ex[k - 1, r]) / (ex[k, r] - ex[k - 1, r])
    return C
A, B, C = crit("A"), crit("B"), crit("C"); n = len(terr)
use = np.flatnonzero((np.isfinite(A).sum(0) >= n - 1) & (np.isfinite(B).sum(0) >= n - 1) & (np.isfinite(C).sum(0) >= n - 1))
cl = lambda X: np.clip(np.where(np.isposinf(X), L[-1] + 5, np.where(np.isneginf(X), L[0] - 2, X)), L[0] - 2, L[-1] + 5)
sd = lambda X: cl(X)[:, use].std(0, ddof=1); sA, sB, sC = sd(A), sd(B), sd(C)
print("terrains with all three arms: %d of %d; receptors used: %d; ladder %d levels" % (n, int(su["n_terrains"]), len(use), len(L)))
print("median spread of critical rain, mm: nothing known %.2f | chosen 1%% known %.2f | random 1%% known %.2f" % (np.median(sA), np.median(sB), np.median(sC)))
print("ratios of medians: chosen/nothing %.2f (line: at most 0.75) -> %s | random/nothing %.2f | means: chosen %.2f, random %.2f" % (np.median(sB) / np.median(sA), "PASS" if np.median(sB) / np.median(sA) <= 0.75 else "FAIL", np.median(sC) / np.median(sA), sB.mean() / sA.mean(), sC.mean() / sA.mean()))
rng = np.random.default_rng(0); bb, bc, bd = [], [], []
for _ in range(3000):
    i = rng.integers(0, n, n); j = rng.integers(0, len(use), len(use)); f = lambda X: np.median(cl(X)[i][:, use[j]].std(0, ddof=1)); a, b, c = f(A), f(B), f(C)
    bb.append(b / a); bc.append(c / a); bd.append(b / c)
print("bootstrap 5th-95th percentile: chosen/nothing %.2f to %.2f | random/nothing %.2f to %.2f | chosen/random %.2f to %.2f (share of resamples where chosen beats random: %.0f%%)" % (*np.percentile(bb, [5, 95]), *np.percentile(bc, [5, 95]), *np.percentile(bd, [5, 95]), 100 * np.mean(np.array(bd) < 1)))
print("receptors whose spread fell with chosen ground: %d of %d; with random ground: %d" % ((sB < sA).sum(), len(use), (sC < sA).sum()))
