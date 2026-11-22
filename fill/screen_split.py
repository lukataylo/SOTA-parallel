"""After-the-fact split test of the shortcut filter. Protocol in docs/G_CRITERIA.md (committed before this was run)."""
import numpy as np
F = np.load("results/air/map_final.npz"); m = F["mover"]; r1 = F["rule1"]; r2 = F["rule2"]; x = 5 * F["j"] + 2
e = r2[0] | r2[1]; A = np.stack([e, e]); B = r1 | r2; C = r1 | A; cand = {"A sign-free rule 2": A, "B rule 1 or rule 2": B, "C rule 1 or A": C}
west = np.stack([x < 256, x < 256]); east = ~west
def score(f, half):
    mv = m & half; n = half.sum(); fl = (f & half).sum(); hit = (f & mv).sum(); dis = (~f & half).sum(); return hit, mv.sum(), fl, n, (mv & ~f).sum(), dis
print("west half (choose here)"); ok = []
for k, f in cand.items():
    hit, tot, fl, n, missed, dis = score(f, west); print("  %-20s finds %d of %d (%.0f%%), flags %d of %d (%.1f%%)" % (k, hit, tot, 100 * hit / tot, fl, n, 100 * fl / n))
    if hit / tot >= 0.8: ok.append((fl, k))
if not ok: print("no candidate reaches 80% on the west half: stop, fail")
else:
    k = min(ok)[1]; f = cand[k]; hit, tot, fl, n, missed, dis = score(f, east)
    print("chosen:", k); print("east half (scored once): finds %d of %d (%.0f%%), flags %d of %d (%.1f%%), wrongly dismissed %d of %d (%.2f%%)" % (hit, tot, 100 * hit / tot, fl, n, 100 * fl / n, missed, dis, 100 * missed / dis))
    nr = east & (F["receptor"] != 161); mv = m & nr; print("  without the railway wall point: finds %d of %d (%.0f%%)" % ((f & mv).sum(), mv.sum(), 100 * (f & mv).sum() / max(mv.sum(), 1)))
    print("  verdict:", "inconclusive (fewer than 30 movers)" if tot < 30 else "PASS" if hit / tot >= 0.8 and fl / n <= 0.10 and missed / dis <= 0.01 else "FAIL")
    hit, tot, fl, n, missed, dis = score(r2, east); print("  for comparison, rule 2 as committed on the east half: %d of %d (%.0f%%), flags %.1f%%" % (hit, tot, 100 * hit / tot, 100 * fl / n))
