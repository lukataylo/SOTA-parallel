"""A second, larger test of street trees (pass lines in docs/G_CRITERIA.md, committed before this ran).
uv run --with mlx --with numpy python fill/green_validate.py      writes results/air/green/validate_b{0..5}.npz
uv run --with numpy python fill/green_validate.py score           prints the scores from the saved batches

48 simulated arms in six batches of eight. The targeted placement is the one from fill/green_run.py, unchanged.
  b0-b3  35 mm: unchanged, targeted 20 trees, and 30 independent random draws of 20 trees (seeds 3000..3029)
  b4     35 mm: targeted 5, 10, 40, 80 trees; targeted 20 with pits at half and at a quarter of the volume; random 40 and 80
  b5     1.4 times the rain of the 35 mm storm: unchanged, the same targeted 20, and 6 random draws (seeds 3000..3005)
"""
import os, sys, numpy as np
sys.path.insert(0, "solver"); import green as G
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]
z, op, road, dx = t["z"], t["open"], t["road"], float(t["dx"])
pf = np.load("results/air/render/fields.npz")["peak_field"][0]
ts = G.tree_sites(op, road); depth = np.array([pf[r:r + 2, c:c + 2].max() for r, c in ts]); order = np.argsort(-depth)
tgt = lambda k: G.spaced(ts, order, k); rnd = lambda seed, k=20: G.spaced(ts, np.random.default_rng(seed).permutation(len(ts)), k)
assert np.array_equal(tgt(20), np.load("results/air/green/placement.npz")["trees_targeted"])
def layers(sites, pit=1.0):
    L = G.empty(z.shape)
    if sites is None: return L
    L = G.add_trees(L, sites, op)
    if pit != 1.0:                                                   # shrink the pits only; the 1 mm canopy stays
        for r, c in sites: L["s1"][r:r + 2, c:c + 2] -= (1 - pit) * G.TREE["pit_m3"] / 4
        L["s1"] *= op
    return L
R = [("random %d" % s, rnd(3000 + s), 1.0) for s in range(30)]
B = [[("base", None, 1.0), ("targeted 20", tgt(20), 1.0)] + R[:6], R[6:14], R[14:22], R[22:30],
     [("targeted 5", tgt(5), 1.0), ("targeted 10", tgt(10), 1.0), ("targeted 40", tgt(40), 1.0), ("targeted 80", tgt(80), 1.0),
      ("targeted 20 half pit", tgt(20), .5), ("targeted 20 quarter pit", tgt(20), .25), ("random 40", rnd(4000, 40), 1.0), ("random 80", rnd(4001, 80), 1.0)],
     [("base", None, 1.0), ("targeted 20", tgt(20), 1.0)] + R[:6]]
P = lambda b: "results/air/green/validate_b%d.npz" % b
if len(sys.argv) < 2:
    from flood_sink import simulate_sink
    for b, arms in enumerate(B):
        if os.path.exists(P(b)): continue
        Ls = [layers(s, p) for _, s, p in arms]; st = lambda k: np.stack([L[k] for L in Ls]); n = len(arms)
        prof = d["profile"][1] * (1.4 if b == 5 else 1.0)
        o = simulate_sink(np.repeat(z[None], n, 0), op, dx, rc, np.repeat(prof[None], n, 0), float(d["profile_dt_s"]), np.full(n, float(d["loss_mm_h"]), np.float32),
                          np.full(n, float(d["t_end_s"]), np.float32), s1_m=st("s1"), s2_m=st("s2"), f_m_s=st("f"), n_manning=st("n"))
        np.savez(P(b), arm=[a for a, _, _ in arms], ntrees=[0 if s is None else len(s) for _, s, _ in arms], peak=o["peak_depth"].astype(np.float64),
                 absorbed_m3=o["absorbed_m3"], imbalance=o["imbalance"], rain_net_m3=o["rain_net_m3"], wall_s=o["wall_s"])
        print("batch %d done, %.0f s" % (b, o["wall_s"]), flush=True)
else:
    L = [np.load(P(b), allow_pickle=True) if os.path.exists(P(b)) else None for b in range(6)]
    def rows(bs, base):
        for b in bs:
            if L[b] is None: continue
            for a, n, pk, ab in zip(L[b]["arm"], L[b]["ntrees"], L[b]["peak"], L[b]["absorbed_m3"]):
                ch = pk - base; fl = base >= 0.1
                yield str(a), dict(n=int(n), fell=int((ch <= -.01).sum()), rose=int((ch >= .01).sum()), best=100 * ch.min(), worst=100 * ch.max(), dried=int((fl & (pk < .1)).sum()), wetted=int((~fl & (pk >= .1)).sum()), total=100 * ch[fl].sum(), taken=float(ab))
    def show(title, bs, base):
        print("\n" + title); print("%-24s %5s %8s %8s %8s %8s %8s %9s %9s" % ("arm", "trees", "fell 1cm", "rose 1cm", "best cm", "worst cm", "unflood", "sum cm", "taken m3")); out = {}
        for a, r in rows(bs, base):
            if a == "base": continue
            out[a] = r; print("%-24s %5d %8d %8d %8.2f %8.2f %8d %9.1f %9.1f" % (a, r["n"], r["fell"], r["rose"], r["best"], r["worst"], r["dried"] - r["wetted"], r["total"], r["taken"]))
        return out
    if L[0] is not None:
        b0 = L[0]["peak"][0]; o = show("35 mm storm (%d receptors flooded unchanged; imbalance up to %.1e)" % ((b0 >= .1).sum(), max(np.abs(L[b]["imbalance"]).max() for b in range(6) if L[b] is not None)), [0, 1, 2, 3, 4], b0)
        T = o["targeted 20"]; rs = [v for k, v in o.items() if k.startswith("random ") and v["n"] == 20]
        print("\nP1 targeting: targeted fell-count %d; random draws scored %d; targeted strictly above %d of them (line: at least %d of 30). Random counts: %s; mean %.1f" % (T["fell"], len(rs), sum(T["fell"] > r["fell"] for r in rs), 28, sorted(r["fell"] for r in rs), np.mean([r["fell"] for r in rs])))
        print("   secondary, summed fall at flooded receptors: targeted %.1f cm; random median %.1f, max %.1f" % (-T["total"], -np.median([r["total"] for r in rs]), -min(r["total"] for r in rs)))
        print("P2 no harm: arms of 20 trees with a receptor rising 1 cm: %d of %d (line 0)" % (sum(v["rose"] > 0 for k, v in o.items() if v["n"] == 20), sum(v["n"] == 20 for v in o.values())))
        if "targeted 80" in o:
            ds = [o["targeted %d" % k]["fell"] for k in (5, 10, 20, 40, 80)]; print("P3 dose: fell-count at 5, 10, 20, 40, 80 targeted trees:", ds, "non-decreasing:", all(a <= b for a, b in zip(ds, ds[1:])))
            print("P4 pit volume: half pit %d, quarter pit %d (line: half pit at least 4)" % (o["targeted 20 half pit"]["fell"], o["targeted 20 quarter pit"]["fell"]))
    if L[5] is not None:
        b5 = L[5]["peak"][0]; o = show("1.4 x rain (net %.1f mm; %d receptors flooded unchanged)" % (1000 * L[5]["rain_net_m3"][0] / (op.sum() * dx * dx), (b5 >= .1).sum()), [5], b5)
        rs = [v["fell"] for k, v in o.items() if k.startswith("random")]; print("P5 other storm: targeted %d, random %s, median %.1f (line: targeted above the median and above 0)" % (o["targeted 20"]["fell"], sorted(rs), np.median(rs)))
