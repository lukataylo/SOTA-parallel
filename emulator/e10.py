"""E10: distil the multi-terrain teacher (E2) into a small single-site student.   python e10.py"""
import os, numpy as np, torch, jax
import flood_exp as fx, harness as H

NS, NT, FRAC = 1000, 256, 0.05      # student storms on the target site, test storms, share given solver labels
ARMS = ("uncertainty", "random", "none")


def setup():
    """Target site, student storms, teacher outputs, the solver-labelled picks per arm."""
    key = jax.random.PRNGKey(1010)
    z1 = np.asarray(fx.make_terrain(key, "fractal")); rep = lambda n: np.broadcast_to(z1, (n,) + z1.shape).copy()
    Ks = np.asarray(fx.make_storms(jax.random.fold_in(key, 1), NS))
    test = H.dataset_fixed("e10_test", rep(NT), np.asarray(fx.make_storms(jax.random.fold_in(key, 2), NT)))
    teachers = []
    for s in H.SEEDS:
        m = H.UNet(); m.load_state_dict(torch.load(os.path.join(H.DATA, f"E2_{s}.pt"), map_location=H.DEV)); teachers.append(H.predictor(m.eval()))
    tp = np.stack([np.stack(t(rep(NS), Ks)) for t in teachers])            # (3 teachers, 2 channels, NS, H, W)
    var = tp[:, 0].var(0).mean((1, 2)); k = int(NS * FRAC)
    picks = dict(uncertainty=np.argsort(var)[-k:], random=np.random.default_rng(0).choice(NS, k, replace=False), none=np.array([], int))
    idx = np.unique(np.concatenate(list(picks.values()))); lab = H.dataset_fixed("e10_labels", rep(len(idx)), Ks[idx])
    return rep, Ks, test, teachers, tp, picks, lab, {int(i): n for n, i in enumerate(idx)}


def job(a):
    arm, s = a; rep, Ks, test, teachers, tp, picks, lab, pos = setup(); pk = picks[arm]
    d = dict(z=rep(NS), K=Ks, hmax=tp[s, 0].copy(), hfin=tp[s, 1].copy())                  # teacher s's outputs as labels
    for i in pk:
        d["hmax"][i], d["hfin"][i] = lab["hmax"][pos[int(i)]], lab["hfin"][pos[int(i)]]
    rows = np.concatenate([np.arange(NS)] + [pk] * 4).astype(int)                          # solver-labelled storms count 5x
    m, t = H.fit_unet({k: v[rows] for k, v in d.items()}, s, w=H.SMALL, epochs=40, lr=H.LR_SMALL); p = H.predictor(m)
    tm = H.metrics(*teachers[s](test["z"], test["K"]), test); mm = H.metrics(*p(test["z"], test["K"]), test)
    r = dict(student=mm, teacher=tm, train_s=t, rmse_vs_teacher=mm["rmse_all"] / tm["rmse_all"], solver_labels=len(pk))
    print(f"[E10 {arm}] seed {s}: student rmse {mm['rmse_all']:.4f} teacher {tm['rmse_all']:.4f} ratio {r['rmse_vs_teacher']:.2f}", flush=True)
    if (arm, s) == ("uncertainty", 0):
        H.plot_examples("E10", p, test); r["_timing"] = dict(student=H.time_per_storm(p, test), teacher=H.time_per_storm(teachers[0], test))
    return r


if __name__ == "__main__":
    setup(); jobs = [(arm, s) for arm in ARMS for s in H.SEEDS]; res = H.pmap(job, jobs, workers=9)
    tm = next(r.pop("_timing") for r in res if "_timing" in r); out = {}
    for arm in ARMS:
        per = [r for (a, _), r in zip(jobs, res) if a == arm]; out[arm] = dict(per_seed=per, summary=H.summarise(per))
    H.save("E10", dict(out, timing=tm["student"], teacher_timing=tm["teacher"],
                       speedup_vs_teacher={k: tm["teacher"][k] / tm["student"][k] for k in ("b1", "b256")},
                       params=dict(teacher=H.nparams(H.UNet()), student=H.nparams(H.UNet(w=H.SMALL))),
                       note="teacher = E2 no-curriculum model; uncertainty = variance across the 3 teacher seeds; one fractal target terrain"))
