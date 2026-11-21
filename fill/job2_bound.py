"""Job 2: conservative volume bound per receptor on the real tile, and what the fill model decides before any band."""
import sys, time, numpy as np
from scipy.ndimage import label
sys.path.insert(0, "fill"); from fillmodel import FillModel
t = np.load("shared/terrain_512.npz"); z, op = t["z"].astype(np.float64), t["open"]
R = np.load("shared/receptors.npz"); rc = R["rc"]; THR = float(R["threshold_m"])
A = op.sum()
# volume bound: rain over the WHOLE open domain (an upper limit on any upstream catchment) must fill the connected
# below-level region around the receptor up to ground + threshold. No credit for outflow or drains.
bound = np.zeros(len(rc)); comp_frac = np.zeros(len(rc)); touches = np.zeros(len(rc), bool)
edge = np.zeros_like(op); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
for i, (r, c) in enumerate(rc):
    L = z[r, c] + THR
    lab, _ = label(op & (z < L)); comp = lab == lab[r, c]
    bound[i] = (L - z[comp]).sum() / A * 1e3; comp_frac[i] = comp.sum() / A; touches[i] = (comp & edge).any()
print("volume bound, mm of net rain: quantiles", np.round(np.percentile(bound, [0, 10, 25, 50, 75, 90, 100]), 1))
print("bound >120 mm (decides every storm dry): %d of %d; bound < 2 mm (decides nothing): %d; region touches the domain edge: %d" % ((bound > 120).sum(), len(bound), (bound < 2).sum(), touches.sum()))
print("below-level region as share of open ground: median %.2f max %.2f" % (np.median(comp_frac), comp_frac.max()))
outlet = edge & op
M = FillModel(z, op, outlet)
for nm in ("pilot", "main"):
    S = np.load(f"shared/storms_{nm}.npz"); P = S["net_depth_mm"].astype(np.float64)
    t0 = time.time(); LL, out = M.run(P * 1e-3); wall = time.time() - t0
    D = M.depth_at(LL, rc)
    np.savez_compressed(f"results/air/fill_{nm}.npz", fill_depth=D.astype(np.float32), wall_s=wall, net_depth_mm=P, build_note="terrain build 0.2 s, not included in wall_s")
    dry_by_bound = P[:, None] < bound[None, :]
    wet = D >= THR
    print(f"{nm}: {len(P)} storms, fill wall {wall:.2f} s | bound decides dry: {dry_by_bound.mean():.3f} of pairs, {dry_by_bound.all(1).mean():.3f} of whole storms | fill says wet: {wet.mean():.3f} of pairs; storms with no wet receptor {(~wet.any(1)).mean():.3f}")
    print("   fill-wet pairs that the bound called dry (should be 0):", int((wet & dry_by_bound).sum()))
    marg = np.abs(D - THR)
    for band in (0.02, 0.05, 0.10):
        und = (np.abs(D - THR) < band) & (D > 0)
        print(f"   band +-{band*100:.0f} cm around the threshold (wet side only counts where fill depth > 0): storms with a receptor in band {und.any(1).mean():.3f}")
np.savez("results/air/volume_bound.npz", bound_mm=bound, comp_frac=comp_frac, touches_edge=touches)
