"""E1: adversarial active learning vs random labelling at equal label count.   python e1.py"""
import numpy as np, torch, torch.nn.functional as F, jax
from scipy.stats import spearmanr
import flood_exp as fx, harness as H

N0, ROUNDS, PER = 200, 5, 200        # 200 seed labels + 5 rounds x 200
MEMBERS = 4


def project_t(raw):
    K = raw
    for _ in range(30):
        vol = F.interpolate(K, size=fx.NF, mode="bilinear", align_corners=False).mean((1, 2, 3)) * fx.T_RAIN
        K = torch.clamp(K * (fx.VOL / vol)[:, None, None, None], max=fx.CAP)
    return K


def disagreement(models, x):
    """Per-storm ensemble variance of predicted peak depth (dm^2), averaged over cells."""
    return torch.stack([m(x)[:, 0] for m in models]).var(0).mean((1, 2))


def adversarial_storms(models, z, seed, iters=30):
    """Gradient ascent on ensemble disagreement, through the emulators, over storm logits."""
    th = (0.5 * torch.randn(len(z), fx.NK, fx.KS, fx.KS, generator=torch.Generator().manual_seed(seed))).to(H.DEV).requires_grad_()
    opt = torch.optim.Adam([th], 0.2); zt = torch.as_tensor(z).to(H.DEV)
    for _ in range(iters):
        loss = -disagreement(models, H.feats(zt, project_t(th.exp()))).sum(); opt.zero_grad(); loss.backward(); opt.step()
    return np.asarray(jax.vmap(fx.project)(np.exp(th.detach().cpu().numpy())))     # re-project with the solver's own definition


def ens_predict(models):
    ps = [H.predictor(m) for m in models]
    def predict(z, K):
        o = [p(z, K) for p in ps]
        return np.mean([a for a, _ in o], 0), np.mean([b for _, b in o], 0)
    return predict


def run(seed, adversarial, base, va, ts):
    D = {k: base[k][:N0] for k in ("z", "K", "hmax", "hfin")}
    torch.manual_seed(seed); models = [H.UNet(w=H.SMALL) for _ in range(MEMBERS)]; hist = []; train_s = 0.
    for r in range(ROUNDS + 1):
        for i, m in enumerate(models):                                   # warm-started retrain on the grown set
            m.train(); train_s += H.train(m, H.feats(D["z"], D["K"]), H.targets(D), epochs=40 if r == 0 else 15, lr=H.LR_SMALL, seed=seed * 100 + r * 10 + i); m.eval()
        with torch.no_grad():
            dis = disagreement(models, H.feats(va["z"], va["K"])).cpu().numpy()
        err = np.sqrt(((ens_predict(models)(va["z"], va["K"])[0] - va["hmax"]) ** 2).mean((1, 2)))
        rho = float(spearmanr(dis, err)[0])
        hist.append(dict(round=r, labels=len(D["z"]), spearman_val=rho, **H.evaluate(ens_predict(models), ts)))
        print(f"  [E1 {'adv' if adversarial else 'rand'} s{seed}] round {r} labels {len(D['z'])} spearman {rho:.2f} "
              f"T_tail {hist[-1]['T_tail']['rmse_all']:.4f} T_iid {hist[-1]['T_iid']['rmse_all']:.4f}", flush=True)
        if r == ROUNDS or (adversarial and r == 1 and rho < 0.2):         # kill condition
            break
        key = jax.random.PRNGKey(5000 + seed * 10 + r)                    # both arms get the same new terrains
        z = np.asarray(fx.make_terrains(key, "fractal", PER))
        K = adversarial_storms(models, z, seed * 10 + r) if adversarial else np.asarray(fx.make_storms(jax.random.fold_in(key, 1), PER))
        new = H.label(z, K)
        hist[-1]["acquired_true_tail_depth_m"] = float(np.sort(new["hmax"].reshape(PER, -1), 1)[:, -23:].mean())
        D = {k: np.concatenate([D[k], new[k]]) for k in D}
    return models, hist, train_s


def make(adv, s):
    base = H.train_fractal(); va = H.dataset("val_fractal", ("fractal",), 128, seed=4)
    models, hist, t = run(s, adv, base, va, H.testsets())
    return ens_predict(models), dict(train_s=t, labels=hist[-1]["labels"], spearman_round1=hist[min(1, len(hist) - 1)]["spearman_val"],
                                     killed=adv and len(hist) < ROUNDS + 1, history=hist)


if __name__ == "__main__":
    from functools import partial
    H.train_fractal(); H.dataset("val_fractal", ("fractal",), 128, seed=4)
    H.run_many({"E1": partial(make, True), "E1_control": partial(make, False)},
               extra=dict(note=f"ensemble of {MEMBERS} small U-Nets, mean prediction; {N0} seed labels + {ROUNDS}x{PER}"))
