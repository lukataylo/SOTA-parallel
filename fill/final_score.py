"""Score the Sunday morning checks against docs/G_CRITERIA.md. uv run --with numpy python fill/final_score.py"""
import glob, os, numpy as np
rc = np.load("shared/receptors.npz")["rc"]; op = np.load("shared/terrain_512.npz")["open"]; F = np.load("results/air/map_final.npz"); THR = 0.01
def load(job):
    """change at receptors per terrain index, each against the unchanged run from its own machine"""
    ch = {}
    for m in ("air", "pro"):
        b = f"results/{m}/final/{job}/base.npz"
        if not os.path.exists(b): continue
        base = np.load(b)["peak"].astype(float)
        for f in glob.glob(f"results/{m}/final/{job}/r*.npz"): q = np.load(f); ch.setdefault(int(q["n"]), q["peak"].astype(float) - base)
    return ch
MV = [(int(k), int(n)) for k in (0, 1) for n in np.flatnonzero(F["mover"][k])]
print("== persist (line: at least 66 of 98 at 70 mm and at n 0.03)")
for job, nm in (("persist70", "70 mm"), ("persistn", "35 mm, Manning n 0.03"), ("persist15", "15 mm")):
    ch = load(job)
    if not ch: print("  %s: not run" % nm); continue
    same = [abs(ch[t][F["receptor"][k, n]]) >= THR and np.sign(ch[t][F["receptor"][k, n]]) == np.sign(F["effect"][k, n]) for t, (k, n) in enumerate(MV) if t in ch]
    anyr = [np.abs(np.where(np.hypot(5 * F["i"][n] + 2 - rc[:, 0], 5 * F["j"][n] + 2 - rc[:, 1]) > 7.5, ch[t], 0)).max() >= THR for t, (k, n) in enumerate(MV) if t in ch]
    print("  %s: %d of %d move the same building 1 cm the same way (%s); move any building more than 7.5 m away: %d" % (nm, sum(same), len(same), "no line" if job == "persist15" else ("pass" if sum(same) >= 66 and len(same) == 98 else "FAIL" if len(same) == 98 else "incomplete"), sum(anyr)))
print("== dense (75 m apart; line: 95% of known lowered movers seen, zero unexplained moves)")
ch = load("dense"); P = 15; idx = {(int(a), int(b)): n for n, (a, b) in enumerate(zip(F["i"], F["j"]))}
if ch:
    seen = tot = 0; unexpl = []; nw = 0
    for c, d in ch.items():
        B = [(i, j) for i in range(c // P or P, 101, P) for j in range(c % P or P, 101, P) if op[5 * i:5 * i + 5, 5 * j:5 * j + 5].any()]; nw += len(B); known = [b for b in B if F["mover"][1, idx[b]]]
        for b in known: n = idx[b]; q = F["receptor"][1, n]; tot += 1; seen += abs(d[q]) >= THR and np.sign(d[q]) == np.sign(F["effect"][1, n])
        for q in np.flatnonzero(np.abs(d) >= THR):
            D = [np.hypot(5 * i + 2 - rc[q, 0], 5 * j + 2 - rc[q, 1]) for i, j in B]
            if min(D) <= 7.5: continue                                   # a square next to the building: not a remote move
            if not any(np.hypot(5 * i + 2 - rc[q, 0], 5 * j + 2 - rc[q, 1]) <= 125 for i, j in known): unexpl.append((c, int(q), round(100 * d[q], 1), round(min(D))))
    print("  runs %d of 225, what-ifs %d (%.1f per run); known lowered movers seen %d of %d (%.0f%%; line 95%%); moves with no known mover within 125 m: %d %s" % (len(ch), nw, nw / len(ch), seen, tot, 100 * seen / max(tot, 1), len(unexpl), unexpl[:12]))
    np.save("results/air/dense_unexplained.npy", np.array(unexpl, float).reshape(-1, 4))
else: print("  not run")
print("== random dismissed, alone (line: 0 of 240)")
ch = load("random")
if ch:
    sc = np.load("results/air/map_scored.npz")["mover"] | F["mover"]; kk, nn = np.nonzero(~sc); pick = sorted(np.random.default_rng(2026).choice(len(kk), 240, replace=False)); hit = []
    for t, d in ch.items():
        n = nn[pick[t]]; D = np.hypot(5 * F["i"][n] + 2 - rc[:, 0], 5 * F["j"][n] + 2 - rc[:, 1]); e = np.where(D > 7.5, d, 0); q = np.abs(e).argmax()
        if abs(e[q]) >= THR: hit.append((int(kk[pick[t]]), int(F["i"][n]), int(F["j"][n]), int(q), round(100 * e[q], 1), round(D[q])))
    print("  run %d of 240; move a building more than 7.5 m away by 1 cm: %d %s; largest change anywhere among the rest %.2f cm" % (len(ch), len(hit), hit, 100 * max(np.abs(d).max() for d in ch.values())))
else: print("  not run")
print("== design from the map (line: targets fall 1 cm, none rises 1 cm, within 5 mm of the sum of singles)")
ch = load("design")
if ch:
    G = np.load("shared/map_design.npz"); d = ch[0]; s = G["single"].sum(0); tg = G["target"]
    print("  targets %s fall by %s cm (sum of singles said %s); receptors falling 1 cm: %d; largest rise %.2f cm; largest gap from the sum of singles %.2f mm -> %s" % (tg.tolist(), np.round(-100 * d[tg], 1).tolist(), np.round(-100 * s[tg], 1).tolist(), (d <= -THR).sum(), 100 * d.max(), 1000 * np.abs(d - s).max(), "pass" if (d[tg] <= -THR).all() and d.max() < THR and np.abs(d - s).max() <= 0.005 else "FAIL"))
    b = np.load("results/air/final/design/base.npz")["peak"].astype(float); print("  targets' peak depth before -> after, m: %s" % [(round(b[q], 2), round(b[q] + d[q], 2)) for q in tg])

print("== derivative (ten times a 5 mm change; line: names 90% of movers, flags at most 1% of dismissed)")
ch = load("deriv"); rnd = load("random")
if ch:
    hit = [abs(10 * ch[t][F["receptor"][k, n]]) >= THR and np.sign(ch[t][F["receptor"][k, n]]) == np.sign(F["effect"][k, n]) for t, (k, n) in enumerate(MV) if t in ch]
    ratio = [10 * ch[t][F["receptor"][k, n]] / F["effect"][k, n] for t, (k, n) in enumerate(MV) if t in ch]
    sc = np.load("results/air/map_scored.npz")["mover"] | F["mover"]; kk, nn = np.nonzero(~sc); pick = sorted(np.random.default_rng(2026).choice(len(kk), 240, replace=False)); fa = tot = 0
    for u in range(120):
        t = 98 + u
        if t not in ch or 2 * u not in rnd: continue
        n = nn[pick[2 * u]]; D = np.hypot(5 * F["i"][n] + 2 - rc[:, 0], 5 * F["j"][n] + 2 - rc[:, 1]) > 7.5; tot += 1; fa += (np.abs(10 * ch[t])[D].max() >= THR) and not (np.abs(rnd[2 * u])[D].max() >= THR)
    print("  movers named by the slope: %d of %d (%.0f%%); predicted over true effect: median %.2f, quartiles %.2f to %.2f; dismissed falsely flagged: %d of %d" % (sum(hit), len(hit), 100 * np.mean(hit), np.median(ratio), np.percentile(ratio, 25), np.percentile(ratio, 75), fa, tot))
else: print("  not run")
print("== drainage at inlets (line: at least 66 of 98)")
ch = load("drain")
if ch:
    same = [abs(ch[t][F["receptor"][k, n]]) >= THR and np.sign(ch[t][F["receptor"][k, n]]) == np.sign(F["effect"][k, n]) for t, (k, n) in enumerate(MV) if t in ch]
    b0 = np.load("results/air/map/s1_raise/base_start.npz")["peak"].astype(float); b1 = np.load("results/air/final/drain/base.npz")["peak"].astype(float)
    print("  %d of %d move the same building 1 cm the same way; receptors at 0.10 m or more: uniform loss %d, inlets %d; median peak depth %.3f -> %.3f m" % (sum(same), len(same), (b0 >= 0.1).sum(), (b1 >= 0.1).sum(), np.median(b0), np.median(b1)))
else: print("  not run")
