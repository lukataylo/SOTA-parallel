"""Job 1: write the shared inputs (terrain, receptors, storms). See docs/BRIEF.md for the contract.
Run: uv run --with numpy --with scipy --with pyproj --with rasterio --with matplotlib python fill/make_shared.py
Needs data/raw/osm_blackfriars.json for street centrelines (not committed); the outputs in shared/ are committed.
"""
import json, pathlib, numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, uniform_filter, label
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin

ROOT = pathlib.Path(__file__).resolve().parents[1]
d = np.load(ROOT / "data/blackfriars_512.npz"); meta = json.load(open(ROOT / "data/blackfriars_512.meta.json"))
dtm, bld = d["dtm"].astype(np.float32), d["buildings"].astype(bool)
ny, nx = dtm.shape; b = meta["bounds_osgb"]
WALL = 20.0; THRESH = 0.10; LOSS = 12.0

# ---- terrain: buildings become walls
open_ = ~bld
z = np.where(bld, dtm + WALL, dtm).astype(np.float32)

# ---- streets from OSM (vehicle and pedestrian ways), used only to pick street-facing receptors
tf = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
tr = from_origin(b["left"], b["top"], 1.0, 1.0)
osm = json.load(open(ROOT / "data/raw/osm_blackfriars.json"))["elements"]
ROADS = {"primary", "secondary", "tertiary", "residential", "unclassified", "service", "pedestrian", "living_street", "trunk"}
lines, bfr = [], []
for e in osm:
    t = e.get("tags", {})
    if e["type"] == "way" and t.get("highway") in ROADS and "geometry" in e and t.get("tunnel") != "yes":
        g = {"type": "LineString", "coordinates": [tf.transform(p["lon"], p["lat"]) for p in e["geometry"]]}
        lines.append(g)
        if t.get("name") == "Blackfriars Road": bfr.append(g)
road = rasterize(lines, out_shape=z.shape, transform=tr, fill=0, default_value=1, dtype="uint8", all_touched=True).astype(bool)
bfr_m = rasterize(bfr, out_shape=z.shape, transform=tr, fill=0, default_value=1, dtype="uint8", all_touched=True).astype(bool)
droad = distance_transform_edt(~road)

# ---- receptors: open cells touching a building, within 12 m of a street centreline, away from the domain edge
cand = open_ & binary_dilation(bld, structure=np.array([[0,1,0],[1,1,1],[0,1,0]], bool)) & (droad <= 12)
EDGE = 16
cand[:EDGE] = cand[-EDGE:] = False; cand[:, :EDGE] = cand[:, -EDGE:] = False
rng = np.random.default_rng(20261121)
pts = np.argwhere(cand); pts = pts[rng.permutation(len(pts))]
SPACING = 22.0
chosen = []
for p in pts:
    if all((p[0]-q[0])**2 + (p[1]-q[1])**2 >= SPACING**2 for q in chosen): chosen.append(p)
rc = [tuple(p) for p in chosen]; labels = [f"edge_{i:03d}" for i in range(len(rc))]
allc = np.argwhere(open_ & binary_dilation(bld, iterations=2))
for k, (c, r) in enumerate(d["osm_entrances_colrow"]):          # mapped entrances, snapped to nearest open cell by a building
    r, c = int(r), int(c)
    if not (EDGE <= r < ny-EDGE and EDGE <= c < nx-EDGE): continue
    dd = ((allc - [r, c])**2).sum(1); j = dd.argmin()
    if dd[j] <= 36 and tuple(allc[j]) not in rc: rc.append(tuple(allc[j])); labels.append(f"osm_entrance_{k:02d}")
# documented site: lowest stretch of Blackfriars Road within 150 m of the station (domain centre).
# Chosen as the centreline cell whose 9 m moving-average carriageway height is lowest (pits beside the road are ignored).
carr = open_ & (distance_transform_edt(~bfr_m) <= 4)             # carriageway strip: within 4 m of the OSM centreline
yy, xx = np.mgrid[:ny, :nx]; near = carr & ((yy-ny//2)**2 + (xx-nx//2)**2 <= 150**2)
cnt = uniform_filter(carr.astype(np.float32), 9)
zavg = np.where(near & bfr_m, uniform_filter(np.where(carr, dtm, 0.0), 9) / np.maximum(cnt, 1e-6), np.inf)
site = tuple(int(v) for v in np.unravel_index(zavg.argmin(), zavg.shape))   # centreline cell with the lowest 9 m average height
rc.append(site); labels.append("blackfriars_road_low_point_documented_site")
rc = np.array(rc, dtype=np.int32)

np.savez_compressed(ROOT / "shared/terrain_512.npz", z=z, open=open_, dx=np.float32(1.0), dtm=dtm, road=road, blackfriars_road=bfr_m, wall_height_m=np.float32(WALL))
np.savez_compressed(ROOT / "shared/receptors.npz", rc=rc, threshold_m=np.float32(THRESH), label=np.array(labels))

# ---- storms
STEP = 60.0; NT = 60
def storms(n, seed):
    r = np.random.default_rng(seed)
    edges = np.linspace(10, 120, n + 1)
    depth = r.uniform(edges[:-1], edges[1:])                    # one storm per depth stratum
    lo = np.clip(np.ceil(depth / 2.0), 15, 60).astype(int)      # mean intensity capped at 120 mm/h, so the triangular peak is at most 240 mm/h
    dur_min = r.integers(lo, 61)
    kind = r.permutation(np.arange(n) % 3)                     # 0 front-loaded, 1 centred, 2 back-loaded
    peak_frac = np.array([0.15, 0.5, 0.85])[kind]
    prof = np.zeros((n, NT), np.float32)
    for i in range(n):
        m = dur_min[i]; t = (np.arange(m) + 0.5) / m; p = peak_frac[i]
        w = np.where(t <= p, t / p, (1 - t) / (1 - p))           # triangular hyetograph
        prof[i, :m] = w / w.sum() * depth[i] / (STEP / 3600.0)  # mm/h, so that sum(rate)*step = depth
    net = (np.maximum(prof - LOSS, 0).sum(1) * STEP / 3600.0)
    o = r.permutation(n)
    return dict(depth_mm=depth[o].astype(np.float32), duration_s=(dur_min[o] * 60).astype(np.float32), profile=prof[o],
                profile_step_s=np.float32(STEP), kind=kind[o].astype(np.int8), loss_mm_h=np.full(n, LOSS, np.float32),
                net_depth_mm=net[o].astype(np.float32), seed=np.int64(seed))
P = storms(64, 101); M = storms(1000, 202)
np.savez_compressed(ROOT / "shared/storms_pilot.npz", **P); np.savez_compressed(ROOT / "shared/storms_main.npz", **M)

# ---- report
lab, nlab = label(open_); sizes = np.bincount(lab.ravel())[1:]
print("open fraction %.3f; open components %d; largest %.3f of open; cells in small enclosed components %d" % (open_.mean(), nlab, sizes.max()/open_.sum(), sizes.sum()-sizes.max()))
print("receptors", len(rc), "edge", sum(l.startswith('edge') for l in labels), "entrances", sum(l.startswith('osm') for l in labels))
print("site rc", site, "ground %.2f m; Blackfriars Rd carriageway within 150 m: min %.2f median %.2f max %.2f" % (dtm[site], dtm[near].min(), np.median(dtm[near]), dtm[near].max()))
print("receptor ground heights: min %.2f median %.2f max %.2f" % (dtm[rc[:,0], rc[:,1]].min(), np.median(dtm[rc[:,0], rc[:,1]]), dtm[rc[:,0], rc[:,1]].max()))
for nm, S in (("pilot", P), ("main", M)):
    print(nm, "n", len(S["depth_mm"]), "depth %.0f-%.0f mm" % (S["depth_mm"].min(), S["depth_mm"].max()), "net depth after loss: min %.1f median %.1f max %.1f mm" % (S["net_depth_mm"].min(), np.median(S["net_depth_mm"]), S["net_depth_mm"].max()),
          "peak rate max %.0f mm/h" % S["profile"].max(), "storms with zero net rain", int((S["net_depth_mm"] == 0).sum()))

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(15, 7.5))
lo, hi = np.percentile(dtm[open_], [1, 99])
ax[0].imshow(np.where(open_, dtm, np.nan), vmin=lo, vmax=hi, cmap="terrain"); ax[0].imshow(np.where(bld, 1.0, np.nan), cmap="gray", vmin=0, vmax=2)
ax[0].scatter(rc[:-1,1], rc[:-1,0], s=10, c="red"); ax[0].scatter([site[1]], [site[0]], s=120, marker="*", c="magenta")
ax[0].set_title("Open ground height, receptors (red), documented site (star)")
ax[1].imshow(road + 2*bfr_m + 4*bld, cmap="tab10"); ax[1].set_title("streets, Blackfriars Road, buildings")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(ROOT / "shared/shared_preview.png", dpi=80)
