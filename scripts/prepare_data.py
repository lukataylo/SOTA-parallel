"""Crop EA 1 m LiDAR to the Blackfriars Road study area and rasterise OSM buildings.

Inputs  (data/raw, not committed): EA LIDAR Composite 2022 1 m DTM + first-return DSM
        for tiles TQ3075 and TQ3080, and an Overpass extract (see data/README.md).
Outputs (data/): blackfriars_{512,1024}.npz with dtm, dsm, building mask, rail mask; meta json; preview png.
Run:    uv run --with rasterio --with pyproj --with numpy --with matplotlib python scripts/prepare_data.py
"""
import json, glob, pathlib, numpy as np, rasterio
from rasterio.merge import merge
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data"
CENTRE_LATLON = (51.5040, -0.1050)   # Blackfriars Road at Southwark station / The Cut
tf = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
cx, cy = tf.transform(CENTRE_LATLON[1], CENTRE_LATLON[0])
cx, cy = round(cx), round(cy)

def mosaic(pattern, bounds):
    srcs = [rasterio.open(p) for p in sorted(glob.glob(str(RAW / pattern)))]
    assert len(srcs) == 2, pattern
    arr, tr = merge(srcs, bounds=bounds, res=1.0, nodata=np.nan)
    return arr[0].astype(np.float32), tr

osm = json.load(open(RAW / "osm_blackfriars.json"))["elements"]
def shapes(pred, polygon):
    out = []
    for e in osm:
        if e["type"] != "way" or "geometry" not in e or not pred(e.get("tags", {})):
            continue
        xy = [tf.transform(p["lon"], p["lat"]) for p in e["geometry"]]
        if polygon and len(xy) >= 4 and xy[0] == xy[-1]:
            out.append({"type": "Polygon", "coordinates": [xy]})
        elif not polygon and len(xy) >= 2:
            out.append({"type": "LineString", "coordinates": xy})
    return out
buildings = shapes(lambda t: "building" in t, True)
rail = shapes(lambda t: "railway" in t and t.get("railway") in ("rail", "light_rail"), False)
entr = [(e, tf.transform(e["lon"], e["lat"])) for e in osm if e["type"] == "node"]

for size in (512, 1024):
    h = size // 2
    b = (cx - h, cy - h, cx + h, cy + h)          # left, bottom, right, top (OSGB metres)
    dtm, tr = mosaic("lidar_composite_dtm_*/*.tif", b)
    dsm, _ = mosaic("lidar_composite_first_return_dsm_*/*.tif", b)
    bmask = rasterize(buildings, out_shape=dtm.shape, transform=tr, fill=0, default_value=1, dtype="uint8") if buildings else np.zeros(dtm.shape, "uint8")
    rmask = rasterize(rail, out_shape=dtm.shape, transform=tr, fill=0, default_value=1, dtype="uint8", all_touched=True) if rail else np.zeros(dtm.shape, "uint8")
    doors = np.array([[(x - b[0]), (b[3] - y)] for _, (x, y) in entr if b[0] <= x < b[2] and b[1] < y <= b[3]], dtype=np.float32).reshape(-1, 2)
    np.savez_compressed(OUT / f"blackfriars_{size}.npz", dtm=dtm, dsm=dsm, buildings=bmask, rail=rmask, osm_entrances_colrow=doors)
    meta = dict(crs="EPSG:27700", res_m=1.0, shape=list(dtm.shape), bounds_osgb=dict(left=b[0], bottom=b[1], right=b[2], top=b[3]),
                centre_latlon=CENTRE_LATLON, row0="north edge; row index increases southward", vertical="metres above Ordnance Datum Newlyn",
                dtm_nan=int(np.isnan(dtm).sum()), dsm_nan=int(np.isnan(dsm).sum()),
                dtm_min=float(np.nanmin(dtm)), dtm_max=float(np.nanmax(dtm)), dtm_p1_p99=[float(v) for v in np.nanpercentile(dtm, [1, 99])],
                building_frac=float(bmask.mean()), rail_cells=int(rmask.sum()), osm_entrances=int(len(doors)),
                dsm_minus_dtm_gt2m_frac=float((np.nan_to_num(dsm - dtm) > 2).mean()),
                source="Environment Agency LIDAR Composite 2022, 1 m DTM and first-return DSM (Open Government Licence v3.0); OpenStreetMap contributors (ODbL)")
    json.dump(meta, open(OUT / f"blackfriars_{size}.meta.json", "w"), indent=1)
    print(size, json.dumps(meta)[:700])

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = np.load(OUT / "blackfriars_512.npz")
fig, ax = plt.subplots(1, 3, figsize=(18, 6))
lo, hi = np.nanpercentile(d["dtm"], [1, 99])
im = ax[0].imshow(d["dtm"], vmin=lo, vmax=hi, cmap="terrain"); ax[0].set_title("Ground height (DTM), m"); plt.colorbar(im, ax=ax[0], fraction=0.046)
im = ax[1].imshow(np.clip(d["dsm"] - d["dtm"], 0, 30), cmap="magma"); ax[1].set_title("Surface minus ground, m (buildings, viaducts, trees)"); plt.colorbar(im, ax=ax[1], fraction=0.046)
ax[2].imshow(d["buildings"] + 2 * d["rail"], cmap="viridis"); ax[2].set_title("OSM buildings (1) and railway (2)")
if len(d["osm_entrances_colrow"]): ax[2].scatter(*d["osm_entrances_colrow"].T, s=8, c="red")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(OUT / "blackfriars_512_preview.png", dpi=90)
