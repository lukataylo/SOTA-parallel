"""Shared harness: cached solver datasets, frozen test sets, metrics, U-Net, training, plots.

Solver (JAX) is ground truth and runs on CPU: JAX has no supported Apple-GPU backend. Emulators are
PyTorch on the Apple GPU (MPS), shared with another job on this machine; FLOOD_DEVICE=cpu forces CPU.
Seeds / arms of an experiment run side by side in a small process pool.
"""
import os, json, time, multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import jax
import flood_exp as fx

torch.set_num_threads(1)
DEV = torch.device(os.environ.get("FLOOD_DEVICE", "mps" if torch.backends.mps.is_available() else "cpu"))
HERE = os.path.dirname(os.path.abspath(__file__))
DATA, RES = os.path.join(HERE, "data"), os.path.join(HERE, "results")
SEEDS = (0, 1, 2)
TRAIN_KINDS, HELD_KINDS = ("fractal", "valley", "basin"), ("street",)
HW = "Apple M3 Pro (6P+6E cores, 36 GB), shared with another job. Solver: JAX on CPU (4-process pool). Emulator training: PyTorch on the Apple GPU (MPS)"
CAPTION = f"rain cap {fx.CAP*3.6e6:.0f} mm/h, volume {fx.VOL*1e3:.0f} mm/storm, grid {fx.NF}x{fx.NF} @ {fx.L/fx.NF:.0f} m"


# ---------- data ----------
def dataset(name, kinds, n, seed, rough=None, res=fx.NF):
    """n (terrain, storm) pairs, a fresh terrain per storm, solved at `res`. Cached in data/."""
    p = os.path.join(DATA, f"{name}.npz")
    if os.path.exists(p) and len((d := dict(np.load(p)))["z"]) == n:      # a cache of the wrong size is rebuilt, never reused
        return d
    os.makedirs(DATA, exist_ok=True)
    key = jax.random.PRNGKey(seed); per = -(-n // len(kinds))
    z = np.concatenate([np.asarray(fx.make_terrains(jax.random.fold_in(key, i), k, per, rough)) for i, k in enumerate(kinds)])[:n]
    kind = np.concatenate([np.full(per, fx.KINDS.index(k)) for k in kinds])[:n]
    rough = np.concatenate([np.asarray(jax.vmap(lambda k: jax.random.uniform(jax.random.split(k, 8)[0], (), minval=0.3, maxval=1.0))(
        jax.random.split(jax.random.fold_in(key, i), per))) for i in range(len(kinds))])[:n] if rough is None else np.full(n, rough)
    perm = np.random.default_rng(seed).permutation(n); z, kind, rough = z[perm], kind[perm], rough[perm]
    K = np.asarray(fx.make_storms(jax.random.fold_in(key, 99), n))
    t0 = time.time(); d = dict(z=z, K=K, kind=kind, rough=rough, **fx.solve_batch(z, K, res)); d["solve_s"] = time.time() - t0
    np.savez(p, **d); print(f"[data] {name}: {n} storms @ {res} in {d['solve_s']:.0f}s", flush=True)
    return d


def dataset_fixed(name, z, K, res=fx.NF):
    """Cached solver labels for given terrains and storms."""
    p = os.path.join(DATA, f"{name}.npz")
    if not os.path.exists(p):
        np.savez(p, **label(z, K, res))
    return dict(np.load(p))


def label(z, K, res=fx.NF, **kw):
    return dict(z=np.asarray(z), K=np.asarray(K), **fx.solve_batch(z, K, res, **kw))


def tail_set():
    """T_tail: gradient search for deep flooding at a target cell, under the cap and fixed volume.
    64 searches (one per fresh fractal terrain) x 4 harvested iterates = 256 storms."""
    p = os.path.join(DATA, "T_tail.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    key = jax.random.PRNGKey(1003)
    z = np.asarray(fx.make_terrains(key, "fractal", 64)); tgt = fx.find_targets(z)
    t0 = time.time(); Ks, ds = fx.search_batch(z, tgt, jax.random.fold_in(key, 1), iters=25)
    it = [6, 12, 18, 24]
    d = label(np.tile(z, (4, 1, 1)), Ks[it].reshape(-1, *Ks.shape[2:]), tgt=np.tile(tgt, (4, 1)))
    d.update(kind=np.zeros(256, int), tgt=np.tile(tgt, (4, 1)), search_depth=ds, search_s=time.time() - t0)
    np.savez(p, **d); print(f"[data] T_tail in {d['search_s']:.0f}s; target depth iter0 {ds[0].mean():.3f} -> iter24 {ds[24].mean():.3f} m", flush=True)
    return d


def testsets():
    """Frozen, created once, never trained on. Seeds are disjoint from every training set."""
    return dict(T_iid=dataset("T_iid", ("fractal",), 256, 1001), T_tail=tail_set(),
                T_terrain=dataset("T_terrain", HELD_KINDS, 256, 1002))


def real_set():
    """T_real: Environment Agency LIDAR Composite 2022 DTM (1 m, OGL v3) at Blackfriars Road / Southwark, from ../data.
    Centre 480 m block-averaged to 48x48 @ 10 m; a cell that is mostly building footprint (OpenStreetMap) is raised 3 m.
    256 random storms. The solver's outflow edge is the south edge here too, which is a modelling choice, not a fact."""
    p = os.path.join(DATA, "T_real.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    d = np.load(os.path.join(HERE, "..", "data", "blackfriars_512.npz")); blk = lambda a: a[16:496, 16:496].reshape(48, 10, 48, 10).mean((1, 3))
    z = (blk(d["dtm"]) + 3.0 * (blk(d["buildings"].astype(np.float32)) > 0.5)).astype(np.float32)
    K = np.asarray(fx.make_storms(jax.random.PRNGKey(1006), 256)); out = dict(label(np.broadcast_to(z, (256, 48, 48)).copy(), K), kind=np.full(256, -1))
    np.savez(p, **out); return out


def train_fractal():
    return dataset("train_fractal", ("fractal",), 2000, seed=1)


def kind_sets():
    return dict(fractal=dataset("T_iid", ("fractal",), 256, 1001), valley=dataset("T_valley", ("valley",), 128, 1004),
                basin=dataset("T_basin", ("basin",), 128, 1005), street=dataset("T_terrain", HELD_KINDS, 256, 1002))


# ---------- metrics ----------
def metrics(peak, fin, d):
    """peak, fin: predicted peak / final depth (B,NF,NF) m; d: solver dataset at fine resolution."""
    t = d["hmax"]; e2 = (peak - t) ** 2; wet = t > 0.01
    m = dict(rmse_all=float(np.sqrt(e2.mean())), rmse_wet=float(np.sqrt(e2[wet].mean())))
    for th in (0.1, 0.3):
        a, b = peak >= th, t >= th
        m[f"csi_{th}"] = float((a & b).sum() / max((a | b).sum(), 1))
    top = np.argsort(t.reshape(len(t), -1), 1)[:, -(t[0].size // 100):]          # deepest 1% of cells per storm
    m["tail_rmse"] = float(np.sqrt(np.take_along_axis(e2.reshape(len(t), -1), top, 1).mean()))
    rain, drain, out, _ = fx.volume_m3(d["acc"], d["hfin"], fx.NF)
    m["mass_err"] = float(np.mean(np.abs(fin.sum((1, 2)) * (fx.L / fx.NF) ** 2 - (rain - drain - out)) / rain))
    return m


def evaluate(predict, sets=None):
    """predict(z, K) -> (peak, fin). Returns {set: metrics}."""
    return {k: metrics(*predict(d["z"], d["K"]), d) for k, d in (sets or testsets()).items()}


def summarise(per_seed):
    """list of nested metric dicts -> {.. 'median','min','max'} per leaf."""
    def rec(xs):
        if isinstance(xs[0], dict):
            return {k: v for k in xs[0] if (v := rec([x[k] for x in xs])) is not None}
        if isinstance(xs[0], (int, float, np.floating)) and not isinstance(xs[0], bool):
            return dict(median=float(np.median(xs)), min=float(np.min(xs)), max=float(np.max(xs)))
    return rec(per_seed)


def save(exp, obj):
    os.makedirs(os.path.join(RES, exp), exist_ok=True)
    obj = dict(obj, hardware=HW, config=CAPTION)
    json.dump(obj, open(os.path.join(RES, exp, "metrics.json"), "w"), indent=1, default=float)
    return obj


# ---------- emulator ----------
def feats(z, K):
    """(B,NF,NF), (B,NK,KS,KS) -> (B,9,NF,NF): rain knots in units of the cap, de-meaned terrain."""
    z = torch.as_tensor(z, dtype=torch.float32); K = torch.as_tensor(K, dtype=torch.float32)
    z, K = z.to(DEV), K.to(DEV)
    r = F.interpolate(K / fx.CAP, size=z.shape[-2:], mode="bilinear", align_corners=False)
    return torch.cat([r, ((z - z.mean((-1, -2), keepdim=True)) / 2.0)[:, None]], 1)


class UNet(nn.Module):
    def __init__(s, cin=9, cout=2, w=(32, 64, 128, 256)):
        super().__init__()
        # GroupNorm chosen on the validation split: without it 1 in 3 seeds of the 2M net stalls near the predict-zero loss
        blk = lambda a, b: nn.Sequential(nn.Conv2d(a, b, 3, padding=1), nn.GroupNorm(8, b), nn.SiLU(), nn.Conv2d(b, b, 3, padding=1), nn.GroupNorm(8, b), nn.SiLU())
        s.down = nn.ModuleList([blk(a, b) for a, b in zip((cin,) + w[:-1], w)])
        s.up = nn.ModuleList([blk(a + b, b) for a, b in zip(w[:0:-1], w[-2::-1])])
        s.out = nn.Conv2d(w[0], cout, 1)
        s.to(DEV)

    def forward(s, x):
        skips = []
        for i, d in enumerate(s.down):
            x = d(x if i == 0 else F.max_pool2d(x, 2)); skips.append(x)
        for u, k in zip(s.up, skips[-2::-1]):
            x = u(torch.cat([F.interpolate(x, size=k.shape[-2:], mode="nearest"), k], 1))
        return s.out(x)


SMALL = (16, 32, 64)        # ~0.12M params: ensemble members, students
LR_SMALL = 2e-3             # chosen on the validation split: the 2M net stalls at 2e-3 and needs 1e-3; the small net is better at 2e-3
OUT_SCALE = 10.0            # nets work in decimetres


def nparams(m):
    return sum(p.numel() for p in m.parameters())


def targets(d):
    return torch.as_tensor(np.stack([d["hmax"], d["hfin"]], 1), dtype=torch.float32).to(DEV) * OUT_SCALE


def train(model, X, Y, epochs=60, lr=1e-3, bs=32, seed=0, loss_fn=F.mse_loss, log=None):
    """AdamW + cosine. Left-right flip augmentation (an exact symmetry: outflow is on the last row)."""
    g = torch.Generator().manual_seed(seed); opt = torch.optim.AdamW(model.parameters(), lr, weight_decay=1e-5)
    steps = epochs * -(-len(X) // bs); sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=steps, pct_start=0.1)
    t0 = time.time()
    for ep in range(epochs):
        perm = torch.randperm(len(X), generator=g); tot = 0.
        for i in range(0, len(X), bs):
            j = perm[i:i + bs].to(X.device); x, y = X[j], Y[j]
            if torch.rand((), generator=g) < 0.5:
                x, y = x.flip(-1), y.flip(-1)
            loss = loss_fn(model(x), y); opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tot += loss.item() * len(j)
        if log and (ep % 10 == 9 or ep == epochs - 1):
            print(f"  [{log}] ep {ep+1}/{epochs} loss {tot/len(X):.4f} {time.time()-t0:.0f}s", flush=True)
    return time.time() - t0


def cached_unet(name, seed, fit):
    """Train-once cache: fit() -> (model, train_s, extra). Weights in data/<name>_<seed>.pt, train time + extras in a .json beside it."""
    p = os.path.join(DATA, f"{name}_{seed}")
    if os.path.exists(p + ".pt"):
        m = UNet(); m.load_state_dict(torch.load(p + ".pt", map_location=DEV)); return (m.eval(), *json.load(open(p + ".json")))
    m, t, extra = fit(); torch.save(m.state_dict(), p + ".pt"); json.dump([t, extra], open(p + ".json", "w"), default=float)
    return m, t, extra


def fit_unet(d, seed, w=(32, 64, 128, 256), epochs=60, log=None, **kw):
    torch.manual_seed(seed); m = UNet(w=w)
    t = train(m, feats(d["z"], d["K"]), targets(d), epochs=epochs, seed=seed, log=log, **kw)
    return m.eval(), t


def predictor(model, bs=256):
    @torch.no_grad()
    def predict(z, K):
        o = torch.cat([model(feats(z[i:i + bs], K[i:i + bs])) for i in range(0, len(z), bs)]).clamp(min=0).cpu().numpy() / OUT_SCALE
        return o[:, 0], o[:, 1]
    return predict


def time_per_storm(predict, d, reps=3):
    """seconds per storm at batch 1 and batch 256, CPU."""
    z, K = d["z"][:256], d["K"][:256]
    def best(f, n):
        f(); ts = []
        for _ in range(reps):
            t0 = time.perf_counter(); f(); ts.append(time.perf_counter() - t0)
        return min(ts) / n
    return dict(b1=best(lambda: [predict(z[i:i + 1], K[i:i + 1]) for i in range(8)], 8), b256=best(lambda: predict(z, K), 256))


def pmap(fn, args, workers=4):
    """Run top-level fn over args in separate single-thread processes (non-daemonic, so they can label with the solver pool)."""
    with ProcessPoolExecutor(min(workers, len(args), 4 if DEV.type == 'mps' else 99), mp_context=mp.get_context("spawn")) as ex:
        return list(ex.map(fn, args))


def _seed_job(a):
    exp, make, seed = a
    predict, info = make(seed); sets = testsets()
    r = dict(info, **evaluate(predict, sets))
    print(f"[{exp}] seed {seed}: " + "  ".join(f"{k} rmse {r[k]['rmse_all']:.4f} tail {r[k]['tail_rmse']:.3f}" for k in sets), flush=True)
    if seed == SEEDS[0]:
        plot_examples(exp, predict, sets["T_iid"]); r["_timing"] = time_per_storm(predict, sets["T_iid"])
    return r


def run_many(makes, extra=None, workers=4):
    """makes: {exp: make}, make(seed) -> (predict, info) a picklable top-level function. All (exp, seed) jobs run in
    parallel; each is scored on the frozen test sets and saved to results/<exp>/metrics.json."""
    jobs = [(e, m, s) for e, m in makes.items() for s in SEEDS]; res = pmap(_seed_job, jobs, workers); out = {}
    for e in makes:
        per = [r for (je, _, _), r in zip(jobs, res) if je == e]; timing = per[0].pop("_timing")
        out[e] = save(e, dict(per_seed=per, summary=summarise(per), timing=timing, **(extra or {})))
    return out


def plot_examples(exp, predict, d, idx=(0, 1, 2), name="examples.png"):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    idx = list(idx); p = predict(d["z"][idx], d["K"][idx])[0]; t = d["hmax"][idx]
    fig, ax = plt.subplots(3, 3, figsize=(10, 9))
    for r in range(3):
        vm = max(t[r].max(), 0.05)
        for c, (a, ttl, cm, lim) in enumerate(((t[r], "solver peak depth (m)", "Blues", (0, vm)), (p[r], "predicted", "Blues", (0, vm)),
                                               (p[r] - t[r], "error (m)", "RdBu", (-vm / 2, vm / 2)))):
            im = ax[r, c].imshow(a, cmap=cm, vmin=lim[0], vmax=lim[1]); ax[r, c].set_title(ttl, fontsize=9); ax[r, c].axis("off")
            fig.colorbar(im, ax=ax[r, c], fraction=0.046)
    fig.suptitle(f"{exp}: three test storms ({CAPTION})", fontsize=9); fig.tight_layout()
    os.makedirs(os.path.join(RES, exp), exist_ok=True); fig.savefig(os.path.join(RES, exp, name), dpi=110); plt.close(fig)


if __name__ == "__main__":      # build and sanity-check the frozen test sets
    ts = testsets(); ks = kind_sets()
    for k, d in {**ts, **ks}.items():
        rain, drain, out, st = fx.volume_m3(d["acc"], d["hfin"], fx.NF)
        print(f"{k:10s} n={len(d['z'])} peak depth: mean-of-max {d['hmax'].max((1,2)).mean():.2f} m, p99 cell {np.quantile(d['hmax'],0.99):.2f} m, "
              f"frac>0.1m {(d['hmax']>0.1).mean():.3f}, >0.3m {(d['hmax']>0.3).mean():.4f} | f32 mass imbalance max {np.abs((rain-drain-out-st)/rain).max():.1e} "
              f"| rain max {jax.vmap(fx.rain_field)(d['K']).max()*3.6e6:.0f} mm/h")
        assert np.isfinite(d["hmax"]).all()
    z = feats(ts["T_iid"]["z"][:4], ts["T_iid"]["K"][:4]); m = UNet()
    print("UNet params", nparams(m), "small", nparams(UNet(w=SMALL)), "out", m(z).shape)
