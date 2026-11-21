"""Score the packed what-if check against docs/G_CRITERIA.md. No thresholds are chosen here."""
import glob, numpy as np
d = np.load("shared/p1_cases.npz"); pk = np.load("shared/pack_check.npz"); rc = np.load("shared/receptors.npz")["rc"]
base = np.load("results/air/p1_chunks/base.npz")["peak"].astype(np.float64); dS = np.load("results/air/p1_scored.npz")["dS"].astype(np.float64)
cen = np.c_[(d["rect"][:, 0] + d["rect"][:, 1] - 1) / 2, (d["rect"][:, 2] + d["rect"][:, 3] - 1) / 2]; dist = np.sqrt(((cen[:, None, :] - rc[None]) ** 2).sum(2)); N = (dist > 7.5) & (dist <= 60.0)
npk = int(pk["n_packs"]); P = np.full((npk, 3, 207), np.nan); wall = 0.0; imb = 0.0
for f in sorted(glob.glob("results/air/pack_check/packs_*.npz")):
    c = np.load(f); P[c["pack"], int(c["storm"])] = c["peak"]; wall += float(c["wall_s"]); imb = max(imb, float(np.abs(c["imbalance"]).max()))
assert not np.isnan(P).any()
dP = P[pk["pack_of"]] - base[None]                                       # (case, storm, receptor): packed change seen from each patch
flag = (np.abs(d["fill_changed_depth"] - d["fill_base_depth"][None]) >= 0.001).any((1, 2))
vs = (np.abs(np.where(N[:, None, :], dS, 0)) >= 0.01).any(2); vp = (np.abs(np.where(N[:, None, :], dP, 0)) >= 0.01).any(2)       # (case, storm)
keep = (vs == vp).all(1)
print("packed runs: %d terrains x 3 storms = %d runs for 120 patches (single: 360 runs); wall %.0f s; max mass imbalance %.1e" % (npk, 3 * npk, wall, imb))
print("FLAGGED patches keeping their single-run verdict in every storm: %d of %d (line: at least 30 of 33) -> %s" % (keep[flag].sum(), flag.sum(), "PASS" if keep[flag].sum() >= 30 else "FAIL"))
new = (vp & ~vs).any(1) & ~flag
print("DISMISSED and random patches (not flagged) showing a new 1 cm mover when packed: %d of %d (line: none) -> %s" % (new.sum(), (~flag).sum(), "PASS" if new.sum() == 0 else "FAIL"))
m = N[:, None, :] & (np.abs(dS) >= 0.001); diff = np.abs(dP - dS)[m]
print("packed minus single change, over %d receptor-patch-storm cases that moved 1 mm or more singly: median %.2f mm, p90 %.2f mm, max %.1f mm (line: median at most 1 mm) -> %s" % (m.sum(), np.median(diff) * 1e3, np.percentile(diff, 90) * 1e3, diff.max() * 1e3, "PASS" if np.median(diff) <= 0.001 else "FAIL"))
lost = flag & ~keep
for i in np.flatnonzero(lost): print("   flagged patch %d changed verdict: single %s packed %s; largest single %.1f mm, packed %.1f mm" % (i, vs[i].astype(int), vp[i].astype(int), np.abs(np.where(N[i], dS[i], 0)).max() * 1e3, np.abs(np.where(N[i], dP[i], 0)).max() * 1e3))
rec = 0; tot = 0; fp = 0; nx = 0
for f in sorted(glob.glob("results/air/pack_check/planted_*.npz")):
    c = np.load(f); s = int(c["storm"])
    for j, peak in zip(c["planted"], c["peak"]):
        mv = int(pk["planted_mover"][j]); ch = peak - base[s]; tot += 1; rec += int((np.abs(np.where(N[mv], ch, 0)) >= 0.01).any())
        for r, cc, dz in pk["planted_extra"][j]:
            if r < 0: continue
            dd = np.hypot(rc[:, 0] - r, rc[:, 1] - cc); nb = (dd > 7.5) & (dd <= 60) & ~N[mv]; nx += 1; fp += int((np.abs(ch[nb]) >= 0.01).any())
print("PLANTED movers recovered among 12 to 16 dismissed patches each: %d of %d (line: at least 19 of 20) -> %s | dismissed patches in those terrains showing a 1 cm change nearby: %d of %d" % (rec, tot, "PASS" if rec >= 19 else "FAIL", fp, nx))
print("what-ifs per run in this check: %.1f for the control repack; %.1f for the planted terrains" % (120 / npk, 1 + nx / max(tot, 1)))
