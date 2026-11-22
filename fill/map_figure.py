"""Figure for the complete solver map: every confirmed block that moves a building, coloured by direction, joined to the building.
uv run --with numpy --with matplotlib python fill/map_figure.py"""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
T = np.load("shared/terrain_512.npz"); op, z = T["open"], T["z"].astype(float); rc = np.load("shared/receptors.npz")["rc"]; M = np.load("results/air/map_final.npz")
ASPH, TAR, CHALK, PINK, WATER, SEAM = "#0e0f11", "#17191d", "#f2efe6", "#ff3d8b", "#2f6bff", "#2a2d33"
fig = plt.figure(figsize=(12, 12), facecolor=ASPH); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(ASPH)
gy, gx = np.gradient(np.where(op, z, np.nan)); sh = np.clip(0.5 - 2.5 * (gx + gy), 0, 1); img = np.zeros((512, 512, 3)); a, t = np.array([0x1d, 0x20, 0x25]) / 255, np.array([0x3a, 0x3e, 0x46]) / 255
img[:] = np.array([0x0e, 0x0f, 0x11]) / 255; g = np.nan_to_num(sh, nan=0.5)[..., None]; img = np.where(op[..., None], a * (0.75 + 0.5 * g), t)
ax.imshow(img, interpolation="nearest")
r2 = M["rule2"].any(0)
for i, j in zip(M["i"][r2], M["j"][r2]): ax.add_patch(plt.Rectangle((5 * j - .5, 5 * i - .5), 5, 5, fc="none", ec=CHALK, lw=0.5, alpha=0.35))
cm = M["mover"]; seg, col = [], []
for k in (0, 1):
    for n in np.flatnonzero(cm[k]):
        i, j, q, e = M["i"][n], M["j"][n], M["receptor"][k, n], M["effect"][k, n]; c = PINK if e > 0 else WATER
        seg.append([(5 * j + 2, 5 * i + 2), (rc[q, 1], rc[q, 0])]); col.append(c); ax.add_patch(plt.Rectangle((5 * j - .5, 5 * i - .5), 5, 5, fc=c, ec="none"))
ax.add_collection(LineCollection(seg, colors=col, lw=1.3, alpha=0.9)); qs = sorted(set(M["receptor"][cm])); ax.scatter(rc[qs, 1], rc[qs, 0], s=26, c=CHALK, zorder=5, lw=0)
ax.set_xlim(0, 512); ax.set_ylim(512, 0); ax.axis("off"); fig.savefig("docs/figures/map.png", dpi=160, facecolor=ASPH); print("blocks drawn %d, buildings %d, quick-estimate outlines %d" % (cm.sum(), len(qs), r2.sum()))
