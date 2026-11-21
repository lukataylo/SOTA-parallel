"""Build the pools for the pool test of the dismissed ground. See docs/G_CRITERIA.md."""
import numpy as np
T = np.load("shared/terrain_512.npz"); op = T["open"]; at = np.load("results/air/atlas.npz"); n = at["n_moved"]          # (2 signs: +5, -5; 512; 512)
M = 8; blocks = []
for i in range(1, 101):                                  # skip the outermost blocks at the domain edge
    for j in range(1, 101):
        r, c = 5 * i + 2, 5 * j + 2
        if op[r, c] and n[0, r, c] == 0 and n[1, r, c] == 0: blocks.append((i, j, r, c))
B = np.array(blocks); cls = (B[:, 0] % M) * M + (B[:, 1] % M); par = ((B[:, 0] // M) + (B[:, 1] // M)) % 2            # checkerboard sign within a pool
print("dismissed blocks tested (both signs dismissed, open centre): %d of %d interior blocks; cover %.1f%% of open ground" % (len(B), 100 * 100, 100 * len(B) * 25 / op.sum()))
sizes = np.bincount(cls, minlength=M * M); print("pools: %d, blocks per pool: min %d median %d max %d" % (M * M, sizes.min(), np.median(sizes), sizes.max()))
d = np.load("shared/p1_cases.npz"); sc = np.load("results/air/p1_scored.npz"); rc = np.load("shared/receptors.npz")["rc"]
cen = np.c_[(d["rect"][:, 0] + d["rect"][:, 1] - 1) / 2, (d["rect"][:, 2] + d["rect"][:, 3] - 1) / 2]; far = np.sqrt(((cen[:, None, :] - rc[None]) ** 2).sum(2)) > 7.5
mv = np.abs(np.where(far, sc["dS"][:, 1, :], 0)).max(1); movers = np.argsort(-mv)[:10]; movers = movers[mv[movers] >= 0.01]
print("positive controls: %d patches that moved a building by 1 cm or more at the 35 mm storm (largest %.1f cm, smallest %.1f cm)" % (len(movers), mv[movers].max() * 100, mv[movers].min() * 100))
rng = np.random.default_rng(31); ctrl_pool = rng.choice(M * M, len(movers), replace=False)
np.savez("shared/pool_test.npz", block_r=B[:, 2], block_c=B[:, 3], cls=cls, parity=par, n_pools=M * M, storm=1, control_case=movers, control_pool=ctrl_pool, spacing_m=5 * M)
