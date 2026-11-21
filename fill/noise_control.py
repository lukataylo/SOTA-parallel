"""Control for the survey-error result: where does the spread in critical rain depth come from?
 A: error everywhere (as before)        B: error everywhere EXCEPT within 5 m of any receptor (distant ground only)
 C: error ONLY within 5 m of receptors  All at sd 5 cm, 3 m correlation, 100 terrains each, same random fields."""
import sys, time, numpy as np, multiprocessing as mp
from scipy.ndimage import gaussian_filter, distance_transform_edt
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op; PG = np.linspace(0.0, 0.130, 261)
m = np.ones(z0.shape, bool); m[rc[:, 0], rc[:, 1]] = False; near = distance_transform_edt(m) <= 5.0
w_far = np.clip((distance_transform_edt(m) - 5.0) / 3.0, 0, 1)        # taper so the mask adds no step
def crit(z):
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); D = M.depth_at(LL, rc); wet = D >= THR
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
def job(a):
    seed, mode = a; n = gaussian_filter(np.random.default_rng(1000 + seed).normal(size=z0.shape), 3.0); n *= 0.05 / n.std()
    if mode == "B": n = n * w_far
    if mode == "C": n = n * (1 - w_far)
    return crit(np.where(op, z0 + n, z0))
if __name__ == "__main__":
    c0 = crit(z0); has = np.isfinite(c0); t0 = time.time()
    jobs = [(s, md) for md in "ABC" for s in range(100)]
    with mp.Pool(7) as p: res = np.array(p.map(job, jobs, chunksize=4))
    np.savez("results/air/noise_control.npz", c0=c0, res=res, modes=np.array([j[1] for j in jobs]))
    print("cells within 5 m of a receptor: %.1f%% of open ground; %d terrains in %.0f s" % (100 * (near & op).sum() / op.sum(), len(jobs), time.time() - t0))
    for i, (md, name) in enumerate((("A", "error everywhere"), ("B", "distant ground only (none within 5 m of any receptor)"), ("C", "only within 5 m of receptors"))):
        X = res[i * 100:(i + 1) * 100][:, has]; Xn = np.where(np.isfinite(X), X, np.nan); sd = np.nanstd(Xn, 0); rel = sd / c0[has]
        print("%s %-55s median spread %.1f mm (%.0f%% of critical depth); receptors with spread > 10%%: %d of %d; stop flooding in some terrain: %d; never-flood receptors flooding in >=10%% of terrains: %d" % (
            md, name, np.nanmedian(sd), 100 * np.nanmedian(rel), (rel > 0.10).sum(), has.sum(), (~np.isfinite(X)).any(0).sum(), (np.isfinite(res[i * 100:(i + 1) * 100][:, ~has]).mean(0) >= 0.1).sum()))
