"""Bet 1, second selection method. The first (pass-cell patch tests) cut spread by 24%, short of the 40% line.
Here the decisive ground is chosen from the ensemble itself: 600 training terrains, and for every cell the share of
variance in each building's critical rainfall explained by the error at that cell. Top-scoring cells up to 1% of open ground.
Tested on the SAME 100 held-out error fields as arms A and C in bet1_cpu.py (seeds 1000-1099); training uses seeds 5000-5599.
Kill lines unchanged: at least 40% cut in median spread; random ground no more than 10%."""
import sys, time, numpy as np, multiprocessing as mp
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op; PG = np.linspace(0.0, 0.130, 261)
REF = z0[rc[:, 0], rc[:, 1]] + THR
def noise(seed): n = gaussian_filter(np.random.default_rng(seed).normal(size=z0.shape), 3.0); return n * (0.05 / n.std())
def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); lev = LL[M.lab[rc[:, 0], rc[:, 1]]].T; wet = lev >= REF[None]
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
KNOWN = None
def train_job(seed): return crit(np.where(op, z0 + noise(seed), z0))
def test_job(seed): return crit(np.where(op, z0 + np.where(KNOWN, 0.0, noise(seed)), z0))
def init(k):
    global KNOWN; KNOWN = k
if __name__ == "__main__":
    prev = np.load("results/air/bet1_cpu.npz"); c0 = prev["c0"]; has = np.isfinite(c0); A = prev["res"][:100][:, has]; Cc = prev["res"][200:300][:, has]
    t0 = time.time(); seeds = list(range(5000, 5600))
    with mp.Pool(6) as p: Y = np.array(p.map(train_job, seeds, chunksize=8))
    print("training ensemble: 600 terrains in %.0f s" % (time.time() - t0), flush=True)
    Y = np.minimum(np.where(np.isfinite(Y[:, has]), Y[:, has], 130.0), 130.0); Ys = (Y - Y.mean(0)) / np.maximum(Y.std(0), 1e-9)
    N = np.stack([noise(s)[::2, ::2].astype(np.float32) for s in seeds]).reshape(len(seeds), -1); Ns = (N - N.mean(0)) / np.maximum(N.std(0), 1e-9)
    R = (Ns.T @ Ys.astype(np.float32)) / len(seeds)                                 # (cells/4, receptors) correlation
    score = (R ** 2).sum(1).reshape(256, 256); score = np.kron(score, np.ones((2, 2))); score[~op] = -1
    budget = int(0.01 * op.sum()); thr = np.sort(score[op])[-budget]; known = (score >= thr) & op
    np.savez("results/air/bet1_cpu2_selection.npz", score=score.astype(np.float32), known=known)
    with mp.Pool(6, initializer=init, initargs=(known,)) as p: B2 = np.array(p.map(test_job, list(range(1000, 1100)), chunksize=4))[:, has]
    f = lambda X: np.minimum(np.where(np.isfinite(X), X, 130.0), 130.0).std(0)
    sA, sB, sC = f(A), f(B2), f(Cc)
    print("selected %d cells = %.2f%% of open ground; top score %.2f, threshold score %.3f, noise floor about %.3f" % (known.sum(), 100 * known.sum() / op.sum(), score.max(), thr, has.sum() / len(seeds)))
    print("median spread mm: nothing known %.2f | ensemble-chosen ground known %.2f (cut %.0f%%) | random ground known %.2f (cut %.0f%%)" % (np.median(sA), np.median(sB), 100 * (1 - np.median(sB) / np.median(sA)), np.median(sC), 100 * (1 - np.median(sC) / np.median(sA))))
    print("mean spread mm: %.2f -> %.2f (cut %.0f%%); receptors whose spread fell by at least half: %d of %d; by at least a quarter: %d" % (sA.mean(), sB.mean(), 100 * (1 - sB.mean() / sA.mean()), (sB <= 0.5 * sA).sum(), has.sum(), (sB <= 0.75 * sA).sum()))
    d = np.sqrt(((np.argwhere(known)[:, None, :] - rc[None]) ** 2).sum(2)).min(1)
    print("selected cells: within 5 m of a receptor %.0f%%; 5-20 m %.0f%%; beyond 20 m %.0f%%" % (100 * (d <= 5).mean(), 100 * ((d > 5) & (d <= 20)).mean(), 100 * (d > 20).mean()))
    for frac in (0.02, 0.05):
        k2 = (score >= np.sort(score[op])[-int(frac * op.sum())]) & op
        with mp.Pool(6, initializer=init, initargs=(k2,)) as p: Bx = np.array(p.map(test_job, list(range(1000, 1100)), chunksize=4))[:, has]
        print("if %.0f%% of open ground is known: median spread %.2f mm (cut %.0f%%)" % (frac * 100, np.median(f(Bx)), 100 * (1 - np.median(f(Bx)) / np.median(sA))), flush=True)
