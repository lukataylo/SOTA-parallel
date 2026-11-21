"""How many whole storms can the fill step decide, as a function of how many receptors must all be decided?"""
import numpy as np
D = np.load("results/air/fill_main.npz")["fill_depth"].astype(np.float64); THR = 0.10
lab = np.load("shared/receptors.npz")["label"]; n = D.shape[1]; rng = np.random.default_rng(0)
ever = (D >= THR).any(0)
print("receptors: %d; ever reach threshold in fill model: %d; never any water: %d" % (n, ever.sum(), (D.max(0) == 0).sum()))
for band in (0.01, 0.02, 0.05):
    und = (np.abs(D - THR) < band) & (D > 0)                      # undecided storm-receptor pairs
    print("band +-%.0f cm: undecided pairs %.4f of all; per-receptor share of storms undecided: median %.3f, p90 %.3f, max %.3f" % (band * 100, und.mean(), np.median(und.mean(0)), np.percentile(und.mean(0), 90), und.mean(0).max()))
    row = []
    for k in (1, 2, 5, 10, 20, 50, 100, 207):
        f = np.mean([(~und[:, rng.choice(n, k, replace=False)].any(1)).mean() for _ in range(400)]) if k < n else (~und.any(1)).mean()
        row.append("%d:%.2f" % (k, f))
    print("   share of storms fully decided, by number of receptors (random subsets):", "  ".join(row))
    print("   documented site alone: decided %.3f of storms" % (~und[:, -1]).mean())
