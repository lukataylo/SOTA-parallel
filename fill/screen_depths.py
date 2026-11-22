"""Score the shortcut re-run at other depths. Protocol in docs/G_CRITERIA.md (committed before the run)."""
import numpy as np
F = np.load("results/air/map_final.npz"); m = F["mover"]; x = 5 * F["j"] + 2; R = np.load("results/air/map_fill_depths.npz"); ch = R["change"]; dm = list(R["depths_mm"].round().astype(int)); fire = ch >= 1e-3
def rule(ds): f = fire[:, :, [dm.index(d) for d in ds]].any(2); e = f[0] | f[1]; return np.stack([e, e])
cand = {"D1 fires at 43 mm": rule([43]), "D2 any of 35, 43, 50": rule([35, 43, 50]), "D3 any of six depths": rule(dm)}
west = np.stack([x < 256, x < 256]); east = ~west
def score(f, half): mv = m & half; return (f & mv).sum(), mv.sum(), (f & half).sum(), half.sum(), (mv & ~f).sum(), (~f & half).sum()
print("check: 35 mm alone, with sign, whole tile finds", (fire[:, :, dm.index(35)] & m).sum(), "of", m.sum(), "(the committed rule 2 found 75)")
print("west half (choose here)"); ok = []
for k, f in cand.items():
    hit, tot, fl, n, missed, dis = score(f, west); print("  %-22s finds %d of %d (%.0f%%), flags %.1f%%" % (k, hit, tot, 100 * hit / tot, 100 * fl / n))
    if hit / tot >= 0.8: ok.append((fl, k))
if not ok: print("no candidate reaches 80% on the west half: stop, fail")
else:
    k = min(ok)[1]; f = cand[k]; hit, tot, fl, n, missed, dis = score(f, east)
    print("chosen:", k); print("east half (scored once): finds %d of %d (%.0f%%), flags %d of %d (%.1f%%), wrongly dismissed %d of %d (%.2f%%)" % (hit, tot, 100 * hit / tot, fl, n, 100 * fl / n, missed, dis, 100 * missed / dis))
    nr = east & (F["receptor"] != 161); mv = m & nr; print("  without the railway wall point: finds %d of %d (%.0f%%)" % ((f & mv).sum(), mv.sum(), 100 * (f & mv).sum() / max(mv.sum(), 1)))
    print("  verdict:", "PASS" if hit / tot >= 0.8 and fl / n <= 0.10 and missed / dis <= 0.01 else "FAIL")
    hit, tot, fl, n, missed, dis = score(f, west | east); print("  whole tile, for information: finds %d of %d (%.0f%%), flags %.1f%%" % (hit, tot, 100 * hit / tot, 100 * fl / n))
