"""E2: procedural terrain randomisation, with and without a roughness curriculum.   python e2.py"""
import os, sys, time, numpy as np, torch, torch.nn.functional as F
import harness as H

N, EPOCHS, BS, LR = 4096, 30, 32, 1e-3
LEVELS = (0.5, 0.65, 0.8, 1.01)                 # curriculum: max terrain roughness parameter in play
TAU = float(os.environ.get("E2_TAU", 0.02))     # advance when val RMSE (m) at the current level drops below this


def fit(tr, va, seed, curriculum):
    torch.manual_seed(seed); g = torch.Generator().manual_seed(seed); m = H.UNet()
    X, Y = H.feats(tr["z"], tr["K"]), H.targets(tr); Xv, Yv = H.feats(va["z"], va["K"]), H.targets(va)
    steps = EPOCHS * (N // BS); opt = torch.optim.AdamW(m.parameters(), LR, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, LR, total_steps=steps, pct_start=0.1)
    lvl = 0 if curriculum else len(LEVELS) - 1; since = 0; log = []; t0 = time.time()
    for st in range(steps):
        pool = torch.as_tensor(np.flatnonzero(tr["rough"] <= LEVELS[lvl]))
        j = pool[torch.randint(len(pool), (BS,), generator=g)].to(H.DEV); x, y = X[j], Y[j]
        if torch.rand((), generator=g) < 0.5:
            x, y = x.flip(-1), y.flip(-1)
        loss = F.mse_loss(m(x), y); opt.zero_grad(); loss.backward(); opt.step(); sched.step(); since += 1
        if curriculum and lvl < len(LEVELS) - 1 and since % 32 == 0:
            with torch.no_grad():
                v = torch.as_tensor(va["rough"] <= LEVELS[lvl]).to(H.DEV)
                rm = float(((m(Xv[v])[:, 0] - Yv[v][:, 0]) ** 2).mean().sqrt()) / H.OUT_SCALE
            if rm < TAU or since >= steps // 5:          # forced advance so full difficulty always gets >= 40% of the budget
                log.append(dict(step=st, level=LEVELS[lvl], val_rmse=rm, forced=rm >= TAU)); lvl += 1; since = 0
    return m.eval(), time.time() - t0, log


def by_kind(p):
    return {k: H.metrics(*p(d["z"], d["K"]), d) for k, d in H.kind_sets().items()}


def make(cur, s):
    m, t, log = H.cached_unet("E2_curriculum" if cur else "E2", s, lambda: fit(H.dataset("train_multi", H.TRAIN_KINDS, N, seed=2),
                                                                                H.dataset("val_multi", H.TRAIN_KINDS, 192, seed=3), s, cur))
    p = H.predictor(m)
    return p, dict(train_s=t, labels=N, curriculum_log=log, by_kind=by_kind(p))


def b3_kind(s):
    m = H.UNet(); m.load_state_dict(torch.load(os.path.join(H.DATA, f"B3_{s}.pt"), map_location=H.DEV)); return by_kind(H.predictor(m.eval()))


if __name__ == "__main__":
    from functools import partial
    H.dataset("train_multi", H.TRAIN_KINDS, N, seed=2); H.dataset("val_multi", H.TRAIN_KINDS, 192, seed=3); H.kind_sets()
    # "E2" (no curriculum) is the control arm and the E10 teacher
    H.run_many({"E2_curriculum": partial(make, True), "E2": partial(make, False)}, extra=dict(tau=TAU, levels=LEVELS,
               note="trained on fractal+valley+basin, one storm per terrain; street is held out"))
    H.save("B3_by_kind", dict(by_kind=H.summarise(H.pmap(b3_kind, list(H.SEEDS)))))
