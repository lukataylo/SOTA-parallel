"""3D picture of the tile from our own data: ground from the 1 m terrain, building heights from the Environment Agency first-return surface model,
water from the solver's peak depth (35 mm storm). Writes docs/figures/flood3d_before.png and flood3d_after.png.
uv run --with numpy --with scipy --with rasterio --with pillow python fill/render3d.py"""
import numpy as np, rasterio
from rasterio.windows import from_bounds
from scipy import ndimage as ndi
from PIL import Image
t = np.load("shared/terrain_512.npz"); z = t["z"].astype(float); op = t["open"]; road = t["road"]; rc = np.load("shared/receptors.npz")["rc"]
L, B, R, T = 531365, 179787, 531877, 180299
dsm = np.full((512, 512), np.nan)
for f in ("data/raw/lidar_composite_first_return_dsm_2022_1m_TQ3080/TQ38sw_FZ_DSM_1m.tif", "data/raw/lidar_composite_first_return_dsm_2022_1m_TQ3075/TQ37nw_FZ_DSM_1m.tif"):
    with rasterio.open(f) as s:
        a = s.read(1, window=from_bounds(L, B, R, T, s.transform), boundless=True, fill_value=np.nan, out_shape=(512, 512)).astype(float)
        if s.nodata is not None: a[a == s.nodata] = np.nan
        a[a < -100] = np.nan; dsm = np.where(np.isnan(dsm), a, dsm)
g = np.where(op, z, np.nan); gf = ndi.generic_filter(np.nan_to_num(g, nan=np.nanmedian(g)), np.median, size=3)   # ground level under buildings
gz = np.where(op, z, ndi.gaussian_filter(np.where(op, z, 0), 8) / np.maximum(ndi.gaussian_filter(op.astype(float), 8), 1e-3))
bh = np.nan_to_num(dsm - t["dtm"], nan=10.0); bh = ndi.median_filter(bh, size=7); bh = np.clip(np.round(bh / 2) * 2, 4, 70)
z0 = np.nanmin(g); H = np.where(op, z, gz + bh) - z0; G = gz - z0; Hmax = H.max() + 1; Hs = ndi.gaussian_filter(H, 1.2); gy, gx = np.gradient(Hs)
amb = np.exp(-np.maximum(ndi.gaussian_filter(H, 7) - H, 0) / 9.0)                                                  # cheap ambient occlusion
W, Hh, S = 1600, 900, 0.40                                                                                           # metres per pixel
az, el = np.radians(38), np.radians(36); f = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), -np.sin(el)]); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
sun = np.array([-0.55, -0.35, 0.62]); sun /= np.linalg.norm(sun); C = np.array([256.0, 262.0, 8.0])
px, py = np.meshgrid((np.arange(W) - W / 2) * S, (Hh / 2 - np.arange(Hh)) * S); P0 = C + px.reshape(-1, 1) * r + py.reshape(-1, 1) * u; P0 = P0 + f * ((Hmax - P0[:, 2]) / f[2])[:, None]
def height(p):
    ix = np.rint(p[:, 0]).astype(int); iy = np.rint(p[:, 1]).astype(int); ins = (ix >= 0) & (ix < 512) & (iy >= 0) & (iy < 512); h = np.full(len(p), 1.5); h[ins] = H[iy[ins], ix[ins]]; return h, ix, iy, ins
def march(P, d, n, step=1.0):
    th = np.full(len(P), np.inf); act = np.arange(len(P)); tt = np.zeros(len(P))
    for _ in range(n):
        if not len(act): break
        tt[act] += step; p = P[act] + d * tt[act][:, None]; h = height(p)[0]; hit = p[:, 2] <= h; th[act[hit]] = tt[act[hit]]; act = act[~hit & (p[:, 2] > -1) & (p[:, 2] <= Hmax + 2)]
    return th
th = march(P0, f, 260); ok = np.isfinite(th); lo = th - 1.0; hi = th.copy()
for _ in range(6):
    mid = (lo + hi) / 2; p = P0[ok] + f * mid[ok][:, None]; below = p[:, 2] <= height(p)[0]; hi[ok] = np.where(below, mid[ok], hi[ok]); lo[ok] = np.where(below, lo[ok], mid[ok])
X = P0 + f * np.where(ok, hi, 0)[:, None]; hc, ix, iy, ins = height(X); ix = np.clip(ix, 0, 511); iy = np.clip(iy, 0, 511)
wall = ok & (hc - X[:, 2] > 0.4); nrm = np.zeros((len(X), 3)); nrm[:, 2] = 1.0
gn = np.stack([-gx[iy, ix], -gy[iy, ix]], 1); gl = np.maximum(np.linalg.norm(gn, axis=1), 1e-6); nrm[wall] = np.column_stack([gn[wall] / gl[wall, None], np.zeros(wall.sum())])
lit = np.zeros(len(X)); lit[ok] = ~np.isfinite(march(X[ok] + nrm[ok] * 0.3 + np.array([0, 0, 0.05]), sun, 150)); ndl = np.clip(nrm @ sun, 0, 1)
shade = 0.50 * np.where(wall, 0.8, amb[iy, ix]) + 0.62 * lit * ndl
isb = ins & ~op[iy, ix]; dist = np.hypot(X[:, 0] - 256, X[:, 1] - 256); fog = np.clip((dist - 215) / 170, 0, 1) ** 1.5; fog[~ok | ~ins] = 1
lab, nl = ndi.label(~op); tg = np.load("shared/map_design.npz"); tgt = set()
for q in tg["target"]:
    rr, cc = rc[q]; w = lab[max(rr - 6, 0):rr + 7, max(cc - 6, 0):cc + 7]; w = w[w > 0]
    if len(w): tgt.add(int(np.bincount(w).argmax()))
istgt = np.isin(lab, list(tgt)); sq = np.zeros((512, 512), bool)
for k, i, j in tg["blocks"]: sq[5 * i - 4:5 * i + 9, 5 * j - 4:5 * j + 9] = True                                     # drawn 13 m wide so a 5 m square can be seen
def picture(depth, name, change=None):
    col = np.where(isb[:, None], np.array([0.17, 0.18, 0.20]), np.where(road[iy, ix][:, None], np.array([0.84, 0.85, 0.87]), np.array([0.95, 0.95, 0.96])))
    d = depth[iy, ix]; wet = ins & ~isb & ~wall & (d >= 0.03); a = np.clip(d / 0.22, 0.35, 0.92)[:, None]; blue = np.array([0.10, 0.46, 0.92]) * (1 - np.clip(d / 0.8, 0, 1))[:, None] + np.array([0.02, 0.16, 0.50]) * np.clip(d / 0.8, 0, 1)[:, None]
    col = np.where(wet[:, None], col * (1 - a) + blue * a, col); img = col * shade[:, None]; img[wet] += 0.10 * lit[wet, None]
    if change is not None:
        roof = isb & ~wall & istgt[iy, ix]; img[roof] = np.array([1.0, 0.74, 0.25]) * (0.75 + 0.25 * shade[roof, None])
        s = ins & ~isb & sq[iy, ix]; img[s] = np.array([0.93, 0.16, 0.12]) * (0.6 + 0.4 * shade[s, None])
        c = change[iy, ix]; dn = ins & ~isb & ~wall & (c <= -0.01) & ~s; img[dn] = np.array([0.20, 0.80, 0.55]) * (0.6 + 0.4 * shade[dn, None])
    img = img * (1 - fog[:, None]) + 0.97 * fog[:, None]; img = np.clip(img, 0, 1).reshape(Hh, W, 3) ** (1 / 1.9)
    bl = ndi.gaussian_filter(img, (2.5, 2.5, 0)); m = np.clip((dist.reshape(Hh, W) - 200) / 180, 0, 1)[..., None]; fm = fog.reshape(Hh, W, 1); m = np.maximum(m, 0) * (1 - fm) + fm
    Image.fromarray((255 * (img * (1 - m) + bl * m)).astype(np.uint8)).save(name); print("wrote", name)
a = np.load("results/air/render/fields.npz")["peak_field"][0]; b = np.load("results/air/render/fields_design.npz")["peak_field"]
picture(a, "docs/figures/flood3d_before.png"); picture(b, "docs/figures/flood3d_after.png", change=b - a)
