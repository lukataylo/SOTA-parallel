"""P1: build the control experiment. 60 patches the fill model says do nothing, 30 random open-ground patches,
30 fresh remote patches it says matter, each at 3 standard storms. Writes shared/p1_cases.npz with the fill predictions."""
import sys, time, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill"); from fillmodel import FillModel
T = np.load("shared/terrain_512.npz"); z0, op = T["z"].astype(np.float64), T["open"]; rc = np.load("shared/receptors.npz")["rc"]
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True; outlet = edge & op
NET = np.array([15.0, 35.0, 70.0]); LOSS = 12.0; DUR = 40
def depths(z): M = FillModel(z, op, outlet); LL, _ = M.run(NET * 1e-3); return M.depth_at(LL, rc)       # (3, receptors)
def rect_of(r, c): return (max(r - 2, 0), min(r + 3, 512), max(c - 2, 0), min(c + 3, 512))
def job(a):
    r, c, dz = a; z = z0.copy(); a0, a1, b0, b1 = rect_of(int(r), int(c)); z[a0:a1, b0:b1] += np.where(op[a0:a1, b0:b1], dz, 0); return depths(z)
def profile_for_net(net_mm):
    m = DUR; t = (np.arange(m) + 0.5) / m; w = np.where(t <= 0.5, t / 0.5, (1 - t) / 0.5); w /= w.sum(); lo, hi = net_mm, net_mm + 40.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if np.maximum(w * mid * 60.0 - LOSS, 0).sum() / 60.0 < net_mm: lo = mid
        else: hi = mid
    p = np.zeros(60, np.float32); p[:m] = w * hi * 60.0; return p
if __name__ == "__main__":
    rng = np.random.default_rng(777); D0 = depths(z0)
    d = np.load("results/air/decisive.npz"); pj = [(int(r), int(c), float(dz)) for r, c, dz, _ in d["jobs"]]
    opc = np.argwhere(op); opc = opc[(opc[:, 0] > 20) & (opc[:, 0] < 492) & (opc[:, 1] > 20) & (opc[:, 1] < 492)]
    rj = [(int(r), int(c), float(rng.choice([-0.05, 0.05]))) for r, c in opc[rng.choice(len(opc), 30, replace=False)]]
    t0 = time.time()
    with mp.Pool(9) as p: Dp = np.array(p.map(job, pj + rj, chunksize=8))
    print("fill depth changes for %d patches x 3 storms in %.0f s" % (len(Dp), time.time() - t0), flush=True)
    dD = Dp - D0[None]; mx = np.abs(dD).max((1, 2))                       # largest predicted change at any receptor, any storm
    cen = np.array([(r, c) for r, c, _ in pj + rj]); dmin = np.sqrt(((cen[:, None, :] - rc[None]) ** 2).sum(2))       # patch to every receptor
    used = set()
    for f in ("shared/interventions.npz", "shared/interventions_retest.npz"):
        for rect in np.load(f)["rect"].tolist(): used.add(tuple(rect))
    npass = len(pj); idx = np.arange(npass); fresh = np.array([tuple(rect_of(*pj[i][:2])) not in used for i in idx])
    far_all = dmin[:npass].min(1) >= 8                                    # at least 8 m from every receptor
    null = idx[(mx[:npass] < 0.001) & far_all & fresh]
    tgt = np.abs(dD[:npass]).reshape(npass, -1).argmax(1); t_s, t_r = tgt // dD.shape[2], tgt % dD.shape[2]
    far_t = dmin[idx, t_r] >= 8
    pos = idx[(mx[:npass] >= 0.01) & far_t & fresh]
    print("candidates: fill-null and >= 8 m from every receptor %d; fill-positive (>= 1 cm) and >= 8 m from the target %d" % (len(null), len(pos)))
    pick_null = rng.choice(null, 60, replace=False)
    order = pos[np.argsort(mx[pos])]; pick_pos = order[np.linspace(0, len(order) - 1, 30).round().astype(int)]; pick_pos = np.unique(pick_pos)
    sel = [("null", i) for i in pick_null] + [("random", npass + k) for k in range(30)] + [("positive", i) for i in pick_pos]
    perm = rng.permutation(len(sel)); sel = [sel[i] for i in perm]; allj = pj + rj
    np.savez("shared/p1_cases.npz", kind=np.array([k for k, _ in sel]), rect=np.array([rect_of(*allj[i][:2]) for _, i in sel]), dz=np.array([allj[i][2] for _, i in sel]),
             fill_base_depth=D0, fill_changed_depth=np.array([Dp[i] for _, i in sel]), min_dist_to_receptor_m=np.array([dmin[i].min() for _, i in sel]),
             net_mm=NET, profile=np.array([profile_for_net(n) for n in NET]), loss_mm_h=np.float32(LOSS), duration_s=np.float32(DUR * 60), t_end_s=np.float32(DUR * 60 + 1200), profile_dt_s=np.float32(60.0), threshold_m=np.float32(0.10))
    k = np.array([k for k, _ in sel]); m2 = np.array([np.abs(Dp[i] - D0).max() for _, i in sel])
    for nm in ("null", "random", "positive"):
        print("%-9s %3d cases | largest fill-predicted change cm: min %.2f median %.2f max %.1f" % (nm, (k == nm).sum(), m2[k == nm].min() * 100, np.median(m2[k == nm]) * 100, m2[k == nm].max() * 100))
