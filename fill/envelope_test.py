"""Go/no-go for envelope ensembles: does simulating the pointwise-max (min) hyetograph of a group of storms
bound every member's peak depth from above (below) at every receptor? Uses the pilot storms already simulated by the Pro."""
import sys, time, numpy as np
sys.path.insert(0, "solver"); from flood import simulate, make_step
b = np.load("results/air/pilot_partial.npz"); idx = b["storm_index"]; pk = b["peak_depth"].astype(np.float64)
S = np.load("shared/storms_pilot.npz"); T = np.load("shared/terrain_512.npz"); rc = np.load("shared/receptors.npz")["rc"]; THR = 0.10
prof = S["profile"][idx]; kind = S["kind"][idx]; net = S["net_depth_mm"][idx]; dur = S["duration_s"][idx]
groups = []
for k in range(3):
    m = np.flatnonzero(kind == k); m = m[np.argsort(net[m])]
    groups.append(("kind%d all %d" % (k, len(m)), m))
    for i in range(0, len(m) - 1, 2): groups.append(("kind%d pair" % k, m[i:i + 2]))
env = []; meta = []
for name, m in groups:
    env.append(prof[m].max(0)); meta.append((name, m, "upper")); env.append(prof[m].min(0)); meta.append((name, m, "lower"))
env = np.array(env, np.float32); tend = np.array([dur[m].max() + 1200.0 for _, m, _ in meta], np.float32)
print("simulating %d envelope storms for %d groups" % (len(env), len(groups)), flush=True)
step = make_step(T["z"], T["open"], float(T["dx"])); out = []
t0 = time.time()
for c in range(0, len(env), 8):
    o = simulate(T["z"], T["open"], float(T["dx"]), rc, env[c:c + 8], 60.0, np.full(len(env[c:c + 8]), 12.0, np.float32), tend[c:c + 8], step=step, alpha=0.7, h_floor=0.05, n_manning=0.015, theta=1.0, rain_mult=1.0)
    out.append(o["peak_depth"]); print("  batch done %.0fs" % (time.time() - t0), flush=True)
E = np.concatenate(out).astype(np.float64)
np.savez("results/air/envelope_test.npz", env=env, peak=E, groups=np.array([m.tolist() for _, m, _ in meta], dtype=object), side=np.array([s for _, _, s in meta]))
tot_dec = tot = 0
for g, (name, m) in enumerate(groups):
    up, lo = E[2 * g], E[2 * g + 1]; mem = pk[m]
    vu = (mem - up[None]).max(); vl = (lo[None] - mem).max()
    nu = ((mem - up[None]) > 1e-3).sum(); nl = ((lo[None] - mem) > 1e-3).sum()
    dec = (up < THR)[None] | (lo >= THR)[None]; dec = np.broadcast_to(dec, mem.shape)
    wrong = ((up < THR)[None] & (mem >= THR)).sum() + ((lo >= THR)[None] & (mem < THR)).sum()
    if "pair" in name: tot_dec += dec.sum(); tot += dec.size
    print("%-14s net mm %s | upper bound broken by more than 1 mm at %d pairs (worst %.1f mm) | lower broken at %d (worst %.1f mm) | receptors decided for the whole group %.3f | wrong decisions %d" % (
        name, np.round(net[m], 0).astype(int).tolist(), nu, max(vu, 0) * 1e3, nl, max(vl, 0) * 1e3, dec[0].mean(), wrong))
print("pairs only: decided %.3f of member-receptor cases" % (tot_dec / max(tot, 1)))
