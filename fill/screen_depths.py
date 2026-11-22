"""Score the shortcut re-run at other depths. Protocol and its one deviation (a sample for the flag rate) in docs/G_CRITERIA.md."""
import numpy as np
F = np.load("results/air/map_final.npz"); R = np.load("results/air/map_fill_depths.npz"); idx = R["index"]; ms = R["is_mover_square"]; ch = R["change"]; dm = list(R["depths_mm"].round().astype(int)); fire = ch >= 1e-3
m = F["mover"][:, idx]; x = 5 * F["j"][idx] + 2; rcp = F["receptor"][:, idx]; allx = 5 * F["j"] + 2; nonmv = ~(F["mover"][0] | F["mover"][1])
def rule(ds): f = fire[:, :, [dm.index(d) for d in ds]].any(2); return f[0] | f[1]                      # per square, sign-free
cand = {"D1 fires at 43 mm": rule([43]), "D2 any of 35, 43, 50": rule([35, 43, 50]), "D3 any of six depths": rule(dm)}
def score(f, half):
    hm = half & ms; hit = (m[:, hm] & f[hm][None]).sum(); tot = m[:, hm].sum(); smp = half & ~ms; rate_other = f[smp].mean()                      # flag rate among non-mover squares, from the sample
    n_other = (nonmv & ((allx < 256) if half[np.flatnonzero(half)[0]] and x[np.flatnonzero(half)[0]] < 256 else (allx >= 256))).sum(); n_mvsq = hm.sum()
    flagged_sq = rate_other * n_other + f[hm].sum(); frac = flagged_sq / (n_other + n_mvsq); dismissed = 2 * (n_other + n_mvsq) - 2 * flagged_sq; return hit, tot, frac, tot - hit, dismissed, smp.sum()
print("check: 35 mm alone, with sign, finds", (fire[:, :, dm.index(35)] & m).sum(), "of", m.sum(), "movers (the committed rule 2 found 75)")
west = x < 256; east = ~west; print("west half (choose here)"); ok = []
for k, f in cand.items():
    hit, tot, frac, missed, dis, ns = score(f, west); print("  %-22s finds %d of %d (%.0f%%), flags about %.1f%% (from %d sampled squares)" % (k, hit, tot, 100 * hit / tot, 100 * frac, ns))
    if hit / tot >= 0.8: ok.append((frac, k))
if not ok: print("no candidate reaches 80% on the west half: stop, fail")
else:
    k = min(ok)[1]; f = cand[k]; hit, tot, frac, missed, dis, ns = score(f, east)
    print("chosen:", k); print("east half (scored once): finds %d of %d (%.0f%%), flags about %.1f%% (from %d sampled squares), wrongly dismissed about %d of %d (%.2f%%)" % (hit, tot, 100 * hit / tot, 100 * frac, ns, missed, dis, 100 * missed / dis))
    nr = (east & ms)[None] & (rcp != 161) & m; print("  without the railway wall point: finds %d of %d" % ((nr & f[None]).sum(), nr.sum()))
    print("  verdict:", "PASS" if hit / tot >= 0.8 and frac <= 0.10 and missed / dis <= 0.01 else "FAIL")
