"""Figure: one real packed run of the map. The squares changed together in colour 115 (raised), each with a 75 m circle.
uv run --with numpy --with matplotlib python fill/packed_figure.py"""
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "fill"); import map_lib as L
T = np.load("shared/terrain_512.npz"); op, z = T["open"], T["z"].astype(float); ASPH, CHALK, PINK = "#0e0f11", "#f2efe6", "#ff3d8b"
fig = plt.figure(figsize=(12, 12), facecolor=ASPH); ax = fig.add_axes([0, 0, 1, 1])
gy, gx = np.gradient(np.where(op, z, np.nan)); g = np.nan_to_num(np.clip(0.5 - 2.5 * (gx + gy), 0, 1), nan=0.5)[..., None]; a, t = np.array([0x1d, 0x20, 0x25]) / 255, np.array([0x3a, 0x3e, 0x46]) / 255
ax.imshow(np.where(op[..., None], a * (0.75 + 0.5 * g), t), interpolation="nearest"); B = L.blocks_of(115)
for i, j in B:
    ax.add_patch(plt.Circle((5 * j + 2, 5 * i + 2), 75, fc=PINK, ec=PINK, alpha=0.07, lw=0)); ax.add_patch(plt.Circle((5 * j + 2, 5 * i + 2), 75, fc="none", ec=PINK, alpha=0.55, lw=1.5)); ax.add_patch(plt.Rectangle((5 * j - 3.5, 5 * i - 3.5), 11, 11, fc=PINK, ec=CHALK, lw=1.2))
ax.set_xlim(0, 512); ax.set_ylim(512, 0); ax.axis("off"); fig.savefig("docs/figures/packed.png", dpi=160, facecolor=ASPH); print(len(B))
