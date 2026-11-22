"""Score the complete solver map against the lines in docs/G_CRITERIA.md. uv run --with numpy python fill/map_score.py
Screen rule 1 (whole-tile map) is applied as the pool test applied it: a block is dismissed if the earlier map shows no change of
any building's critical rain for either sign at the block's centre cell (any open cell, where the centre is under a building)."""
import sys, glob, numpy as np
sys.path.insert(0, "fill"); import map_lib as L
rc, op, THR, NEAR, FAR = L.rc, L.op, L.THR, L.NEAR, L.FAR
SIGNS = ("raise", "lower"); REC, INFO = {}, {}
for s in SIGNS: REC[s], INFO[s] = L.attribute(s)
B = sorted(REC["raise"]); assert B == sorted(REC["lower"]); nb = len(B)
eff = np.array([[REC[s][b]["effect"] for b in B] for s in SIGNS]); dist = np.array([[REC[s][b]["dist"] for b in B] for s in SIGNS]); rcp = np.array([[REC[s][b]["receptor"] for b in B] for s in SIGNS])
mover = np.abs(eff) >= THR; idx = {b: k for k, b in enumerate(B)}

print("== integrity")
ok_int = True
for s in SIGNS:
    I = INFO[s]; ok = I["max_imbalance"] <= 5e-5 and I["base_spread"] == 0; ok_int &= ok
    print("  %s: runs %d of 900, what-ifs %d, worst mass imbalance %.1e, unchanged runs %d, start against end on the same machine %.1e m, Air against Pro %.1e m, solver time %.1f h -> %s" % (s, I["runs"], I["whatifs"], I["max_imbalance"], I["n_base"], I["base_spread"], I["cross_machine"], I["wall_s"] / 3600, "ok" if ok else "FAIL"))
runs = sum(INFO[s]["runs"] for s in SIGNS); wi = sum(INFO[s]["whatifs"] for s in SIGNS); moved = sum(INFO[s]["moved"] for s in SIGNS); un = sum(INFO[s]["unattributed"] for s in SIGNS)
print("  total: %d what-ifs in %d runs = %.2f per run" % (wi, runs, wi / runs))

print("== the map")
for k, s in enumerate(SIGNS): print("  %s: %d of %d blocks move a building more than 7.5 m away by 1 cm or more (%.2f%%); deeper %d, shallower %d" % (s, mover[k].sum(), nb, 100 * mover[k].mean(), (eff[k][mover[k]] > 0).sum(), (eff[k][mover[k]] < 0).sum()))
either = mover.any(0); d_all = dist[mover]; e_all = np.abs(eff[mover])
print("  what-ifs that move a building: %d of %d (%.2f%%); blocks where either sign does: %d (%.2f%% of blocks); both signs: %d" % (mover.sum(), 2 * nb, 100 * mover.mean(), either.sum(), 100 * either.mean(), mover.all(0).sum()))
print("  distance to the building moved, m: median %.0f, 90th percentile %.0f, max %.0f; effect, cm: median %.1f, max %.1f; distinct buildings moved: %d" % (np.median(d_all), np.percentile(d_all, 90), d_all.max(), 100 * np.median(e_all), 100 * e_all.max(), len(set(rcp[mover]))))

print("== packing holds at scale")
print("  unattributed moves: %d of %d moved receptors (%.2f%%; line 2%%) -> %s" % (un, moved, 100 * un / moved, "pass" if un / moved <= 0.02 else "FAIL"))
Q = np.load("shared/pool_split.npz"); base1 = np.load("results/air/p1_chunks/base.npz")["peak"][1].astype(np.float64); ch1 = np.full((int(Q["n_packs"]), 207), np.nan)
for f in sorted(glob.glob("results/air/pool_split/split_*.npz")): c = np.load(f); ch1[c["k"]] = c["peak"] - base1[None]
D1 = np.hypot(Q["r"][:, None] - rc[None, :, 0], Q["c"][:, None] - rc[None, :, 1]); c1 = ch1[Q["pack_of"]]
for far in (FAR, 60.0):
    own = (D1 > NEAR) & (D1 <= far); a = np.where(own, np.abs(c1), 0); q1 = a.argmax(1); e1 = c1[np.arange(len(q1)), q1] * (a.max(1) > 0); v1 = np.abs(e1) >= THR
    km = np.array([idx.get(((r - 2) // 5, (c - 2) // 5), -1) for r, c in zip(Q["r"], Q["c"])]); sg = np.where(Q["dz"] > 0, 0, 1); have = km >= 0
    vm = mover[sg[have], km[have]]; same = vm == v1[have]; df = np.abs(eff[sg[have], km[have]] - e1[have])
    print("  276 earlier singles (reach %d m): compared %d; verdict kept %d (%.1f%%; line 95%%) -> %s; single says mover, map says not: %d; map says mover, single not: %d; median difference in the change %.2f mm" % (far, have.sum(), same.sum(), 100 * same.mean(), "pass" if same.mean() >= 0.95 else "FAIL", (v1[have] & ~vm).sum(), (~v1[have] & vm).sum(), 1000 * np.median(df)))
    if far == FAR: single_scored = dict(kept=int(same.sum()), n=int(have.sum()), med=float(np.median(df)))
conf = {}; CONF = np.full(eff.shape, np.nan)
for s, m in (("raise", "air"), ("lower", "pro")):
    k = SIGNS.index(s); d = f"results/{m}/map/confirm_s1_{s}"; P = np.load(f"{d}/plan.npz"); Qb = P["blocks"]; ns = int(P["n_single"]); base = L.load(s)[0]; ch = np.full((len(Qb), 207), np.nan); imb = 0.0
    for f in sorted(glob.glob(f"{d}/k*.npz")): c = np.load(f); ch[c["k"]] = c["peak"] - base[None]; imb = max(imb, float(np.abs(c["imbalance"]).max()))
    res = {"single": [], "repack": []}
    for t in range(len(Qb)):
        if np.isnan(ch[t, 0]): continue
        bl = [tuple(b) for b in Qb[t] if b[0] >= 0]; cen = np.array([(5 * i + 2, 5 * j + 2) for i, j in bl], float); D = np.hypot(cen[:, None, 0] - rc[None, :, 0], cen[:, None, 1] - rc[None, :, 1]); near = D.argmin(0)
        for n_, b in enumerate(bl):
            own = (near == n_) & (D[n_] > NEAR) & (D[n_] <= FAR); e = np.abs(ch[t])[own].max() if own.any() else 0.0; kb = idx[b]
            res["single" if t < ns else "repack"].append((e >= THR, abs(ch[t, rcp[k, kb]] - eff[k, kb])))
            if e < THR: print("    lost: %s block %s, map said %.1f cm at building %d, %.0f m away; alone it is %.1f cm" % (s, b, 100 * eff[k, kb], rcp[k, kb], dist[k, kb], 100 * ch[t, rcp[k, kb]]))
            if t >= ns: CONF[k, kb] = e >= THR
            elif not np.isfinite(CONF[k, kb]): CONF[k, kb] = e >= THR
    conf[s] = res
    for nm, line in (("single", 0.9), ("repack", 0.9)):
        r = np.array(res[nm], float)
        if len(r): print("  confirm, %s, %s: %d movers re-run; still movers %d (%.1f%%); median difference at the same building %.2f mm; worst imbalance %.1e" % (s, "true singles" if nm == "single" else "repacked 300 m apart", len(r), r[:, 0].sum(), 100 * r[:, 0].mean(), 1000 * np.median(r[:, 1]), imb))
    print("  %s: movers in plan %d, true singles %d, terrains run %d of %d" % (s, int(P["n_movers"]), ns, (~np.isnan(ch[:, 0])).sum(), len(Qb)))
sg_all = np.array(conf["raise"]["single"] + conf["lower"]["single"], float); rp_all = np.array(conf["raise"]["repack"] + conf["lower"]["repack"], float)
print("  true singles, both signs: %d of %d keep the verdict (%.1f%%; line 36 of 40 = 90%%) -> %s" % (sg_all[:, 0].sum(), len(sg_all), 100 * sg_all[:, 0].mean(), "pass" if sg_all[:, 0].mean() >= 0.9 else "FAIL"))
print("  repacked, both signs: %d of %d keep the verdict (%.1f%%; line 90%%) -> %s" % (rp_all[:, 0].sum(), len(rp_all), 100 * rp_all[:, 0].mean(), "pass" if rp_all[:, 0].mean() >= 0.9 else "FAIL"))
md = 1000 * np.median(np.r_[sg_all[:, 1], rp_all[:, 1]]); print("  median difference in the change, confirm runs: %.2f mm (line 1 mm) -> %s" % (md, "pass" if md <= 1 else "FAIL"))

print("== screen")
at = np.load("results/air/atlas.npz")["n_moved"]; F = np.load("results/air/map_fill.npz"); assert [(int(a), int(b)) for a, b in zip(F["i"], F["j"])] == B
def r1(b):
    i, j = b; r, c = 5 * i + 2, 5 * j + 2
    if op[r, c]: return at[0, r, c] > 0 or at[1, r, c] > 0
    sl = (slice(5 * i, 5 * i + 5), slice(5 * j, 5 * j + 5)); return bool(((at[0][sl] > 0) | (at[1][sl] > 0))[op[sl]].any())
rule1 = np.repeat(np.array([r1(b) for b in B])[None], 2, 0); rule2 = np.abs(F["fill_change"]) >= 1e-3; scr = {}
for nm, fl in (("rule 1, earlier whole-tile map", rule1), ("rule 2, predicted depth change of 1 mm", rule2)):
    dis = ~fl; miss = (dis & mover).sum(); hit = (fl & mover).sum(); em = np.abs(eff[dis & mover])
    p1, p2 = miss / dis.sum() <= 0.01, hit / mover.sum() >= 0.8
    print("  %s: flags %d of %d what-ifs (%.1f%%); dismisses %d, of which movers %d (%.2f%%; line 1%%) -> %s; finds %d of %d movers (%.1f%%; line 80%%) -> %s; missed movers' effect, cm: median %.1f, max %.1f" % (nm, fl.sum(), fl.size, 100 * fl.mean(), dis.sum(), miss, 100 * miss / dis.sum(), "pass" if p1 else "FAIL", hit, mover.sum(), 100 * hit / mover.sum(), "pass" if p2 else "FAIL", 100 * np.median(em) if len(em) else 0, 100 * em.max() if len(em) else 0))
    scr[nm[:6]] = (int(fl.sum()), int(miss), int(hit))
cm = mover & (CONF == 1); print("== confirmed movers (still movers when re-run alone or 300 m apart): %d of %d; rule 1 finds %d, rule 2 finds %d; rule 2 dismisses %d confirmed movers of %d dismissed (%.2f%%)" % (cm.sum(), mover.sum(), (cm & rule1).sum(), (cm & rule2).sum(), (cm & ~rule2).sum(), (~rule2).sum(), 100 * (cm & ~rule2).sum() / (~rule2).sum()))
print("   confirmed: distance median %.0f m, max %.0f m; effect median %.1f cm, max %.1f cm; deeper %d, shallower %d; blocks %d; buildings %d" % (np.median(dist[cm]), dist[cm].max(), 100 * np.median(np.abs(eff[cm])), 100 * np.abs(eff[cm]).max(), (eff[cm] > 0).sum(), (eff[cm] < 0).sum(), cm.any(0).sum(), len(set(rcp[cm]))))
np.savez("results/air/map_scored.npz", confirmed=cm, i=np.array([b[0] for b in B]), j=np.array([b[1] for b in B]), effect=eff, dist=dist, receptor=rcp, mover=mover, rule1=rule1, rule2=rule2, fill_change=F["fill_change"])
