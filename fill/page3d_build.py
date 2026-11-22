"""Build the interactive 3D page (docs/southwark_flood_3d.html) from our own data: 1 m ground, surveyed building heights, simulated peak water
with and without the five-square fix at 15, 35 and 70 mm, and an OpenStreetMap street map draped on the ground.
uv run --with numpy --with scipy --with rasterio --with pillow --with pyproj --with requests python fill/page3d_build.py"""
import numpy as np, rasterio, gzip, base64, io, json, os, time, pathlib
from rasterio.windows import from_bounds
from scipy import ndimage as ndi
from PIL import Image
t = np.load("shared/terrain_512.npz"); z = t["z"].astype(float); op = t["open"]; road = t["road"]; rc = np.load("shared/receptors.npz")["rc"]; thr = 0.10
L, B, R, T = 531365, 179787, 531877, 180299
dsm = np.full((512, 512), np.nan)
for f in ("data/raw/lidar_composite_first_return_dsm_2022_1m_TQ3080/TQ38sw_FZ_DSM_1m.tif", "data/raw/lidar_composite_first_return_dsm_2022_1m_TQ3075/TQ37nw_FZ_DSM_1m.tif"):
    with rasterio.open(f) as s:
        a = s.read(1, window=from_bounds(L, B, R, T, s.transform), boundless=True, fill_value=np.nan, out_shape=(512, 512)).astype(float); a[a < -100] = np.nan; dsm = np.where(np.isnan(dsm), a, dsm)
gz_ = np.where(op, z, ndi.gaussian_filter(np.where(op, z, 0), 8) / np.maximum(ndi.gaussian_filter(op.astype(float), 8), 1e-3))
bh = np.nan_to_num(dsm - t["dtm"], nan=10.0); bh = ndi.median_filter(bh, size=7); bh = np.clip(np.round(bh / 2) * 2, 4, 70)
z0 = np.nanmin(np.where(op, z, np.nan)); H = np.where(op, z, gz_ + bh) - z0; G = gz_ - z0
amb = np.exp(-np.maximum(ndi.gaussian_filter(H, 7) - H, 0) / 9.0)
lab, _ = ndi.label(~op); tg = np.load("shared/map_design.npz"); tgt = set()
for q in tg["target"]:
    rr, cc = rc[q]; w = lab[max(rr - 6, 0):rr + 7, max(cc - 6, 0):cc + 7]; w = w[w > 0]
    if len(w): tgt.add(int(np.bincount(w).argmax()))
flags = (~op).astype(np.uint8) | (np.isin(lab, list(tgt)).astype(np.uint8) << 1)
sq = np.zeros((512, 512), bool)
for k, i, j in tg["blocks"]: sq[5 * i - 4:5 * i + 9, 5 * j - 4:5 * j + 9] = True
flags |= (sq & op).astype(np.uint8) << 2
F = np.load("results/air/render/fields_all.npz"); base = F["base"]; diff = F["design"] - F["base"]
blob = b"".join([np.round(H * 100).astype("<u2").tobytes(), np.round(G * 100).astype("<u2").tobytes(), np.round(amb * 255).astype(np.uint8).tobytes(), flags.tobytes(),
                 np.clip(np.round(base * 1000), 0, 65535).astype("<u2").tobytes(), np.clip(np.round(diff * 1000), -127, 127).astype(np.int8).tobytes()])
data64 = base64.b64encode(gzip.compress(blob, 9)).decode()
# ---- street map texture (OpenStreetMap standard tiles, zoom 18), resampled to the tile ----
N = 2048; tex = None
try:
    import requests; from pyproj import Transformer
    tr = Transformer.from_crs(27700, 4326, always_xy=True); e, n = np.meshgrid(L + (np.arange(N) + 0.5) * 512 / N, T - (np.arange(N) + 0.5) * 512 / N); lon, lat = tr.transform(e, n); Z = 18
    gx = (lon + 180) / 360 * 2 ** Z * 256; gy = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * 2 ** Z * 256
    x0, x1, y0, y1 = int(gx.min() // 256), int(gx.max() // 256), int(gy.min() // 256), int(gy.max() // 256); mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.uint8); cache = pathlib.Path("data/raw/osm_tiles"); cache.mkdir(exist_ok=True)
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            p = cache / f"{Z}_{tx}_{ty}.png"
            if not p.exists():
                r = requests.get(f"https://tile.openstreetmap.org/{Z}/{tx}/{ty}.png", headers={"User-Agent": "flood-map-demo/0.1 (hackathon, one-off)"}, timeout=20); r.raise_for_status(); p.write_bytes(r.content); time.sleep(0.15)
            mos[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = np.asarray(Image.open(p).convert("RGB"))
    tex = mos[np.clip((gy - y0 * 256).astype(int), 0, mos.shape[0] - 1), np.clip((gx - x0 * 256).astype(int), 0, mos.shape[1] - 1)]; print("street map tiles:", (x1 - x0 + 1) * (y1 - y0 + 1))
except Exception as ex: print("no street map:", ex)
if tex is None: tex = np.where(np.kron(road, np.ones((4, 4), bool))[..., None], 214, 240).astype(np.uint8).repeat(3, 2)
g = tex.astype(float).mean(2, keepdims=True); tex = (0.55 * tex + 0.45 * g) * 0.5 + 255 * 0.5                           # quieter, lighter map so water reads
tex[np.kron(~op, np.ones((4, 4), bool))] = 255; buf = io.BytesIO(); Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).save(buf, "JPEG", quality=82); tex64 = base64.b64encode(buf.getvalue()).decode()
names = [str(x) for x in np.load("shared/receptors.npz")["label"]] if "label" in np.load("shared/receptors.npz").files else []
stats = {"storms": [15, 35, 70], "flooded": [[int((F["base_rc"][s] >= thr).sum()), int((F["design_rc"][s] >= thr).sum())] for s in range(3)],
         "targets": [[round(float(100 * (F["design_rc"][s] - F["base_rc"][s])[q]), 1) for q in tg["target"]] for s in range(3)],
         "rise": [round(float(100 * (F["design_rc"][s] - F["base_rc"][s]).max()), 2) for s in range(3)], "tpos": [[int(rc[q][0]), int(rc[q][1])] for q in tg["target"]]}
br = np.argwhere(t["blackfriars_road"]); bfr = [int(np.percentile(br[:, 0], 22)), int(np.median(br[br[:, 0] < np.percentile(br[:, 0], 30), 1]))] if len(br) else [150, 256]
html = pathlib.Path("fill/page3d_template.html").read_text().replace("__DATA__", data64).replace("__TEX__", tex64).replace("__STATS__", json.dumps(stats)).replace("__BFR__", json.dumps(bfr))
pathlib.Path("docs/southwark_flood_3d.html").write_text(html); print("page %.1f MB; data %.1f MB; map %.1f MB" % (len(html) / 1e6, len(data64) / 1e6, len(tex64) / 1e6), stats)
