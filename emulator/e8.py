"""E8: multi-fidelity training at equal solver compute (cell-steps).   python e8.py"""
import os, numpy as np, torch, torch.nn.functional as F
import flood_exp as fx, harness as H

BUDGETS = (100, 200, 400)                       # in fine-solve equivalents (1 fine storm = 5.53M cell-steps)
COST = (12 * 12 * fx.grid(12)[2]) / (fx.NF ** 2 * fx.grid(fx.NF)[2])     # coarse storm = 1/64 of a fine one
STEPS = int(os.environ.get("E8_STEPS", 800))    # same gradient-step budget for every arm


def up(a):
    return F.interpolate(torch.as_tensor(a)[:, None], size=fx.NF, mode="bilinear", align_corners=False)[:, 0].numpy()


def X_of(z, K, flag):
    x = H.feats(z, K); return torch.cat([x, torch.full_like(x[:, :1], float(flag))], 1)     # resolution embedding: one flag channel


def fit(parts, seed, steps=STEPS):
    """parts: list of (dataset, row indices, flag). Small U-Net on the union."""
    X = torch.cat([X_of(d["z"][i], d["K"][i], f) for d, i, f in parts if len(i)])
    Y = torch.cat([torch.as_tensor(np.stack([d["hmax"][i], d["hfin"][i]], 1)) * H.OUT_SCALE for d, i, f in parts if len(i)]).to(H.DEV)
    torch.manual_seed(seed); m = H.UNet(cin=10, w=H.SMALL)
    t = H.train(m, X, Y, epochs=max(1, round(steps / -(-len(X) // 32))), lr=H.LR_SMALL, seed=seed)
    return m.eval(), t


def predictor(m, flag=0.):
    @torch.no_grad()
    def predict(z, K):
        o = m(X_of(z, K, flag)).clamp(min=0).cpu().numpy() / H.OUT_SCALE; return o[:, 0], o[:, 1]
    return predict


def adaptive(fine, coarse, B, seed):
    """Buy labels in 3 tranches. After the first (90/10 mix), score every candidate at both fidelities by
    two-member ensemble variance per unit cost and buy greedily."""
    n0 = int(B / 3 / (0.1 + 0.9 * COST)); fi, ci = np.arange(int(0.1 * n0)), np.arange(int(0.9 * n0)); spent = len(fi) + len(ci) * COST
    for r in range(2):
        ens = [fit([(fine, fi, 0.), (coarse, ci, 1.)], seed * 10 + k, steps=300)[0] for k in range(2)]
        cf, cc = np.setdiff1d(np.arange(len(fine["z"])), fi), np.setdiff1d(np.arange(len(coarse["z"])), ci)
        with torch.no_grad():
            var = lambda d, i, f: torch.stack([m(X_of(d["z"][i], d["K"][i], f))[:, 0] for m in ens]).var(0).mean((1, 2)).cpu().numpy()
            sc = np.concatenate([var(fine, cf, 0.), var(coarse, cc, 1.) / COST]); cost = np.concatenate([np.ones(len(cf)), np.full(len(cc), COST)])
        order = np.argsort(-sc); take = order[np.cumsum(cost[order]) <= B * (r + 2) / 3 - spent]
        fi = np.concatenate([fi, cf[take[take < len(cf)]]]); ci = np.concatenate([ci, cc[take[take >= len(cf)] - len(cf)]])
        spent = len(fi) + len(ci) * COST
    return fi, ci


ARMS = ("a_all_fine", "b_fixed_90_10", "c_adaptive")


def load():
    fine = H.train_fractal(); coarse = H.dataset("pool_coarse", ("fractal",), 4000, seed=5, res=12)
    return fine, dict(coarse, hmax=up(coarse["hmax"]), hfin=up(coarse["hfin"]))


def job(a):
    arm, B, s = a; fine, coarse = load(); ts = H.testsets(); n = int(B / (0.1 + 0.9 * COST))
    fi, ci = (np.arange(B), np.arange(0)) if arm[0] == "a" else (np.arange(int(0.1 * n)), np.arange(int(0.9 * n))) if arm[0] == "b" else adaptive(fine, coarse, B, s)
    m, t = fit([(fine, fi, 0.), (coarse, ci, 1.)], s); p = predictor(m)
    r = dict(H.evaluate(p, ts), train_s=t, n_fine=len(fi), n_coarse=len(ci), compute=len(fi) + len(ci) * COST)
    print(f"[E8 {arm} B={B}] seed {s}: fine {len(fi)} coarse {len(ci)} T_iid rmse {r['T_iid']['rmse_all']:.4f}", flush=True)
    if (arm[0], B, s) == ("b", BUDGETS[-1], 0):
        H.plot_examples("E8", p, ts["T_iid"]); r["_timing"] = H.time_per_storm(p, ts["T_iid"])
    return r


if __name__ == "__main__":
    load(); jobs = [(arm, B, s) for B in BUDGETS for arm in ARMS for s in H.SEEDS]; res = H.pmap(job, jobs, workers=7)
    timing = next(r.pop("_timing") for r in res if "_timing" in r); out = {}
    for B in BUDGETS:
        for arm in ARMS:
            per = [r for (a, b, _), r in zip(jobs, res) if (a, b) == (arm, B)]; out[f"{arm}_B{B}"] = dict(per_seed=per, summary=H.summarise(per))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    for arm in ARMS:
        r = [out[f"{arm}_B{B}"]["summary"]["T_iid"]["rmse_all"] for B in BUDGETS]
        ax.errorbar(BUDGETS, [x["median"] for x in r], yerr=[[x["median"] - x["min"] for x in r], [x["max"] - x["median"] for x in r]], marker="o", capsize=3, label=arm)
    ax.set_xscale("log"); ax.set_xlabel("solver compute (fine-storm equivalents; 1 = 5.53M cell-steps)"); ax.set_ylabel("T_iid RMSE, peak depth (m)")
    ax.set_title(f"E8: accuracy vs solver compute, median and range of 3 seeds\n{H.CAPTION}", fontsize=8); ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(H.RES, "E8", "compute_curve.png"), dpi=110)
    H.save("E8", dict(out, budgets=BUDGETS, coarse_cost=COST, steps=STEPS, timing=timing,
                      note="small U-Net (0.12M) for every arm; coarse labels are 12x12 solves bilinearly upsampled, flagged by an input channel"))
