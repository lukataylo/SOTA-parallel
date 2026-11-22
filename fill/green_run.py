"""Smallest solver test of grass and street trees: 8 arms in one batched run per storm, 35 mm and 70 mm (2 runs in all).
uv run --with mlx --with numpy python fill/green_run.py            writes results/air/green/s{1,2}.npz and prints the table

Arms (placed once, from the unchanged 35 mm run and the fill model's contributing ground; the same placement at 70 mm):
  0 base                 nothing
  1 grass targeted       1,000 m2 of grass on the non-road blocks that drain to the most at-risk buildings
  2 grass random         1,000 m2 of grass on random non-road blocks
  3 grass everywhere     every open cell that is not road (ceiling)
  4 trees targeted       20 trees at the kerb sites with the deepest unchanged peak water, 10 m apart
  5 trees random         20 trees at random kerb sites, 10 m apart
  6 trees every 10 m     a tree at every kerb site, 10 m apart (ceiling)
  7 grass + trees        arms 1 and 4 together

Written before the run (docs/ABSORPTION.md, predictions 2 and 3): 1,000 m2 of grass moves no receptor by 1 cm, targeted or
not; trees help only where water reaches the pit, so targeted beats random; no arm raises a receptor by 1 cm.
"""
import os, sys, numpy as np
sys.path.insert(0, "solver"); from flood_sink import simulate_sink; import green as G
t = np.load("shared/terrain_512.npz"); d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]
z, op, road, dx = t["z"], t["open"], t["road"], float(t["dx"])
pf = np.load("results/air/render/fields.npz")["peak_field"][0]                 # unchanged peak depth, 35 mm
ac = np.load("results/air/e0_absorb.npz")["absorb_count"]                      # at-risk buildings each cell drains to (fill model)
rng = np.random.default_rng(2026); NB, NT = 40, 20                             # 40 blocks of 25 m2 = 1,000 m2; 20 trees

gb = G.grass_blocks(op, road); blk = lambda a: a[:510, :510].reshape(102, 5, 102, 5).sum((1, 3))
score = blk(ac * (op & ~road))[gb[:, 0], gb[:, 1]] + 1e-3 * blk(pf * op)[gb[:, 0], gb[:, 1]]
g_t = G.blocks_mask(gb[np.argsort(-score)[:NB]], op, road); g_r = G.blocks_mask(gb[rng.choice(len(gb), NB, replace=False)], op, road)
ts = G.tree_sites(op, road); depth = np.array([pf[r:r + 2, c:c + 2].max() for r, c in ts])
t_t = G.spaced(ts, np.argsort(-depth), NT); t_r = G.spaced(ts, rng.permutation(len(ts)), NT); t_a = G.spaced(ts, np.arange(len(ts)), 10 ** 6)

E = lambda: G.empty(z.shape)
arms = [("base", E()), ("grass targeted", G.add_grass(E(), g_t)), ("grass random", G.add_grass(E(), g_r)),
        ("grass everywhere", G.add_grass(E(), op & ~road)), ("trees targeted", G.add_trees(E(), t_t, op)),
        ("trees random", G.add_trees(E(), t_r, op)), ("trees every 10 m", G.add_trees(E(), t_a, op)),
        ("grass + trees", G.add_trees(G.add_grass(E(), g_t), t_t, op))]
size = ["", "%d m2" % g_t.sum(), "%d m2" % g_r.sum(), "%d m2" % (op & ~road).sum(), "%d trees" % len(t_t), "%d trees" % len(t_r),
        "%d trees" % len(t_a), "%d m2, %d trees" % (g_t.sum(), len(t_t))]
B = len(arms); st = lambda k: np.stack([L[k] for _, L in arms])
os.makedirs("results/air/green", exist_ok=True)
np.savez_compressed("results/air/green/placement.npz", grass_targeted=g_t, grass_random=g_r, trees_targeted=t_t, trees_random=t_r, trees_all=t_a)
for S in (1, 2):
    o = simulate_sink(np.repeat(z[None], B, 0), op, dx, rc, np.repeat(d["profile"][S][None], B, 0), float(d["profile_dt_s"]),
                      np.full(B, float(d["loss_mm_h"]), np.float32), np.full(B, float(d["t_end_s"]), np.float32),
                      s1_m=st("s1"), s2_m=st("s2"), f_m_s=st("f"), n_manning=st("n"))
    pk = o["peak_depth"].astype(np.float64); ch = pk - pk[0]
    np.savez("results/air/green/s%d.npz" % S, arm=[a for a, _ in arms], size=size, peak=pk, absorbed_m3=o["absorbed_m3"],
             capacity_m3=o["sink_capacity_m3"], imbalance=o["imbalance"], rain_net_m3=o["rain_net_m3"], wall_s=o["wall_s"])
    print("\n%d mm storm: one run of %d arms, %.0f s, largest mass imbalance %.1e, net rain %.0f m3; %d of 207 receptors flooded (0.10 m) unchanged"
          % (d["net_mm"][S], B, o["wall_s"], np.abs(o["imbalance"]).max(), o["rain_net_m3"][0], (pk[0] >= 0.1).sum()))
    print("%-18s %-20s %9s %6s %8s %8s %8s %9s %9s" % ("arm", "size", "taken m3", "full", "flooded", "fell 1cm", "rose 1cm", "best cm", "worst cm"))
    for b in range(1, B):
        print("%-18s %-20s %9.1f %5.0f%% %8d %8d %8d %9.2f %9.2f" % (arms[b][0], size[b], o["absorbed_m3"][b], 100 * o["sink_fill_frac"][b],
              (pk[b] >= 0.1).sum(), (ch[b] <= -0.01).sum(), (ch[b] >= 0.01).sum(), 100 * ch[b].min(), 100 * ch[b].max()))
