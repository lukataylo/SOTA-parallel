"""Score the Bet 1 solver pilot. Pass line (docs/BETS.md): the spread of critical rainfall with the chosen ground known (arm B)
is at most 75% of the spread with nothing known (arm A). Flooding judged against a fixed reference level, as in the fill-model test."""
import numpy as np, glob
out = "results/pro/bet1_pilot"; su = np.load(f"{out}/setup.npz"); L = su["levels_net_mm"]; NT = int(su["n_terrains"])
z0 = np.load("shared/terrain_512.npz")["z"]; rc = np.load("shared/receptors.npz")["rc"]; REF = z0[rc[:, 0], rc[:, 1]] + 0.10
def crit(arm):
    C = np.full((NT, len(rc)), np.nan)
    for t in range(NT):
        d = np.load(f"{out}/t{t:03d}_{arm}.npz"); lev = d["peak"] + d["ground_at_receptors"][None]; ex = lev - REF[None]      # (levels, receptors), >= 0 means flooded
        for r in range(len(rc)):
            w = ex[:, r] >= 0
            if not w.any(): C[t, r] = np.inf
            elif w[0]: C[t, r] = -np.inf
            else:
                k = np.argmax(w); C[t, r] = L[k - 1] + (L[k] - L[k - 1]) * (0 - ex[k - 1, r]) / (ex[k, r] - ex[k - 1, r])
    return C
A, B = crit("A"), crit("B")
inside = np.isfinite(A).sum(0) + np.isfinite(B).sum(0)
use = np.flatnonzero((np.isfinite(A).sum(0) >= NT - 1) & (np.isfinite(B).sum(0) >= NT - 1))
cl = lambda X: np.clip(np.where(np.isposinf(X), L[-1] + 5, np.where(np.isneginf(X), L[0] - 2, X)), L[0] - 2, L[-1] + 5)
sA, sB = cl(A)[:, use].std(0, ddof=1), cl(B)[:, use].std(0, ddof=1)
print("terrains %d, ladder %s mm net. Receptors with a critical rain inside the ladder in at least %d of %d terrains in both arms: %d" % (NT, L.tolist(), NT - 1, NT, len(use)))
print("spread of critical rain per receptor (sd over terrains), mm: nothing known: median %.2f, mean %.2f | chosen 1%% known: median %.2f, mean %.2f" % (np.median(sA), sA.mean(), np.median(sB), sB.mean()))
ratio = np.median(sB) / np.median(sA)
print("RATIO of medians B/A = %.2f (pass line: at most 0.75) -> %s | ratio of means %.2f | receptors whose spread fell: %d of %d; fell by half or more: %d" % (ratio, "PASS" if ratio <= 0.75 else "FAIL", sB.mean() / sA.mean(), (sB < sA).sum(), len(use), (sB <= 0.5 * sA).sum()))
rng = np.random.default_rng(0); bs = []
for _ in range(2000):
    i = rng.integers(0, NT, NT); j = rng.integers(0, len(use), len(use))
    a = cl(A)[i][:, use[j]].std(0, ddof=1); b = cl(B)[i][:, use[j]].std(0, ddof=1); bs.append(np.median(b) / max(np.median(a), 1e-9))
print("bootstrap over terrains and receptors: ratio 5th-95th percentile %.2f to %.2f" % tuple(np.percentile(bs, [5, 95])))
print("mean critical rain: A %.1f mm, B %.1f mm; per-receptor spreads A:", np.round(sA, 1)); print("   B:", np.round(sB, 1))
np.savez("results/air/bet1_pilot_scored.npz", A=A, B=B, use=use)
