"""Bet 1, CPU go/no-go (fill model): does knowing the height of a small set of high-leverage ground collapse the
uncertainty in each building's critical rainfall, while knowing the same area of random ground does not?
Flooding is judged against a FIXED reference level (nominal ground at the receptor + 0.10 m), so moving the receptor's own cell does not count.
Arms, 100 terrains each, same error fields (5 cm sd, 3 m correlation):
  A nothing known: error everywhere      B decisive ground known: error removed on the top-leverage patches (<= 1% of open ground)
  C random ground known: error removed on the same number of random 5x5 m open-ground patches
Kill lines (set before running): B must cut the median spread by at least 40%; C must cut it by no more than 10%."""
import sys, time, numpy as np, multiprocessing as mp
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op; PG = np.linspace(0.0, 0.130, 261)
REF = z0[rc[:, 0], rc[:, 1]] + THR
def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); lev = LL[M.lab[rc[:, 0], rc[:, 1]]].T          # (P, receptors) water level
    wet = lev >= REF[None]; return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
d = np.load("results/air/decisive.npz"); c0m, jobs, C = d["c0"], d["jobs"], d["crit_patch"]
cap = lambda x: np.minimum(np.where(np.isfinite(x), x, 200.0), 200.0)
lev_score = np.minimum(np.abs(cap(C) - cap(c0m)[None]), 50.0).sum(1)                                  # per patch test
loc = {}
for j, (r, c, dz, rad) in enumerate(jobs): loc[(int(r), int(c))] = max(loc.get((int(r), int(c)), 0.0), lev_score[j])
ranked = sorted(loc, key=lambda k: -loc[k]); budget = int(0.01 * op.sum())
known_B = np.zeros(z0.shape, bool); nB = 0
for (r, c) in ranked:
    if loc[(r, c)] <= 0: break
    m = np.zeros(z0.shape, bool); m[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3] = True; m &= op
    if (known_B | m).sum() > budget: break
    known_B |= m; nB += 1
rng = np.random.default_rng(4242); opc = np.argwhere(op); known_C = np.zeros(z0.shape, bool)
while known_C.sum() < known_B.sum():
    r, c = opc[rng.integers(len(opc))]; known_C[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3] = True; known_C &= op
def job(a):
    seed, arm = a; n = gaussian_filter(np.random.default_rng(1000 + seed).normal(size=z0.shape), 3.0); n *= 0.05 / n.std()
    if arm == "B": n = np.where(known_B, 0.0, n)
    if arm == "C": n = np.where(known_C, 0.0, n)
    return crit(np.where(op, z0 + n, z0))
if __name__ == "__main__":
    c0 = crit(z0); has = np.isfinite(c0); t0 = time.time()
    jobsN = [(s, arm) for arm in "ABC" for s in range(100)]
    with mp.Pool(6) as p: res = np.array(p.map(job, jobsN, chunksize=4))
    np.savez("results/air/bet1_cpu.npz", c0=c0, res=res, known_B=known_B, known_C=known_C)
    print("decisive set: %d patches, %d cells = %.2f%% of open ground; random set %d cells; at-risk receptors (fixed reference) %d; %d terrains in %.0f s" % (nB, known_B.sum(), 100 * known_B.sum() / op.sum(), known_C.sum(), has.sum(), len(jobsN), time.time() - t0))
    sds = {}
    for i, arm in enumerate("ABC"):
        X = res[i * 100:(i + 1) * 100][:, has]; Xc = np.where(np.isfinite(X), X, 130.0)             # never-flood counted at the top of the range
        sd = Xc.std(0); iqr = np.percentile(Xc, 75, 0) - np.percentile(Xc, 25, 0); sds[arm] = sd
        print("arm %s: spread of critical rain per receptor: median sd %.2f mm, mean sd %.2f mm, median IQR %.2f mm; shift of the median from the true value: median %.2f mm" % (arm, np.median(sd), sd.mean(), np.median(iqr), np.median(np.median(Xc, 0) - c0[has])))
    for arm in "BC":
        print("arm %s vs A: median spread cut by %.0f%%; mean spread cut by %.0f%%; receptors whose spread fell by at least half: %d of %d" % (arm, 100 * (1 - np.median(sds[arm]) / np.median(sds["A"])), 100 * (1 - sds[arm].mean() / sds["A"].mean()), (sds[arm] <= 0.5 * sds["A"]).sum(), has.sum()))
