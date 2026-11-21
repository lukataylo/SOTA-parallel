"""How does the spread of each building's critical rainfall depend on the correlation length of the terrain error?
The 3 m length used so far is an assumption; the one published variogram we found gives 65-100 m. Fill model, fixed reference level,
5 cm sd, 60 terrains per length. Correlation is set by a Gaussian filter of the stated sigma (metres)."""
import sys, time, numpy as np, multiprocessing as mp
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op; PG = np.linspace(0.0, 0.130, 261)
REF = z0[rc[:, 0], rc[:, 1]] + THR
def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); wet = LL[M.lab[rc[:, 0], rc[:, 1]]].T >= REF[None]
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
def job(a):
    seed, sig, sd = a; n = gaussian_filter(np.random.default_rng(3000 + seed).normal(size=z0.shape), sig, mode="wrap"); n *= sd / n.std()
    return crit(np.where(op, z0 + n, z0))
if __name__ == "__main__":
    c0 = crit(z0); has = np.isfinite(c0); SIG = (1.0, 3.0, 10.0, 30.0, 60.0); t0 = time.time()
    jobs = [(s, sig, 0.05) for sig in SIG for s in range(60)]
    with mp.Pool(3) as p: res = np.array(p.map(job, jobs, chunksize=2))
    np.savez("results/air/noise_corr_sweep.npz", c0=c0, res=res, sig=np.array(SIG))
    for i, sig in enumerate(SIG):
        X = res[i * 60:(i + 1) * 60][:, has]; Xc = np.minimum(np.where(np.isfinite(X), X, 130.0), 130.0); sd = Xc.std(0)
        print("correlation sigma %4.0f m: median spread %.2f mm (%.0f%% of critical rain), mean %.2f mm; buildings with spread > 10%%: %d of %d; stop flooding in some terrain: %d" % (sig, np.median(sd), 100 * np.median(sd / c0[has]), sd.mean(), (sd / c0[has] > 0.10).sum(), has.sum(), (~np.isfinite(X)).any(0).sum()), flush=True)
    print("%d terrains in %.0f s" % (len(jobs), time.time() - t0))
