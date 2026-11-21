"""Score the control experiment against docs/P1_CRITERIA.md. No thresholds are chosen here; they are read from that document."""
import glob, numpy as np
from scipy.stats import spearmanr
d = np.load("shared/p1_cases.npz"); rc = np.load("shared/receptors.npz")["rc"]; kind = d["kind"]; n = len(kind)
base = np.load("results/air/p1_chunks/base.npz")["peak"]                         # (3, 207)
pk = np.full((n, 3, 207), np.nan); imb = []
for f in sorted(glob.glob("results/air/p1_chunks/chunk_*.npz")):
    c = np.load(f); pk[c["case"], int(c["storm"])] = c["peak"]; imb.append(np.abs(c["imbalance"]).max())
assert not np.isnan(pk).any(), "missing runs"
dS = pk - base[None]                                                              # solver change in peak depth (case, storm, receptor)
dF = d["fill_changed_depth"] - d["fill_base_depth"][None]                         # fill-predicted change
cen = np.c_[(d["rect"][:, 0] + d["rect"][:, 1] - 1) / 2, (d["rect"][:, 2] + d["rect"][:, 3] - 1) / 2]
dist = np.sqrt(((cen[:, None, :] - rc[None]) ** 2).sum(2))                        # (case, receptor)
far = dist > 5.0 + 2.5                                                            # receptor not inside or within 5 m of the 5x5 patch
print("runs: %d cases x 3 storms; max mass imbalance %.1e" % (n, max(imb)))
# ---- nulls
mv = (np.abs(dS) >= 0.01) & far[:, None, :]
def moved(k): return mv[kind == k].any((1, 2))
nm = moved("null")
print("NULL patches (fill model says no effect): %d of %d move some receptor's peak by >= 1 cm in some storm (%.0f%%). Pass line: at most 10%% (6) -> %s" % (nm.sum(), nm.size, 100 * nm.mean(), "PASS" if nm.mean() <= 0.10 else "FAIL"))
big = np.abs(np.where(far[:, None, :], dS, 0))[kind == "null"].max((1, 2)) * 100
print("   largest change per null patch, cm: median %.2f, p90 %.2f, max %.2f; nulls moving any receptor by >= 0.5 cm: %d" % (np.median(big), np.percentile(big, 90), big.max(), (big >= 0.5).sum()))
# ---- positives
P = np.flatnonzero(kind == "positive"); f, s_ = [], []
for i in P:
    a = np.abs(np.where(far[i][None, :], dF[i], 0)); st, r = np.unravel_index(a.argmax(), a.shape); f.append(dF[i, st, r]); s_.append(dS[i, st, r])
f, s_ = np.array(f) * 100, np.array(s_) * 100
sign = (np.sign(f) == np.sign(s_)) & (np.abs(s_) >= 0.05)
rho = spearmanr(f, s_)[0]; slope = np.polyfit(f, s_, 1)[0]; slope0 = (f @ s_) / (f @ f)
print("POSITIVE patches (%d): sign right %d of %d (line: at least 26 of 30, 85%%) -> %s | Spearman %.2f (line 0.7) -> %s | slope %.2f, through origin %.2f (line 0.45 to 0.75) -> %s" % (
    len(P), sign.sum(), len(P), "PASS" if sign.mean() >= 0.85 else "FAIL", rho, "PASS" if rho >= 0.7 else "FAIL", slope, slope0, "PASS" if 0.45 <= slope <= 0.75 else "FAIL"))
print("   predicted cm:", np.round(f, 1)); print("   simulated cm:", np.round(s_, 1))
print("   positives that move some receptor by >= 1 cm: %d of %d; median |simulated| %.1f cm vs |predicted| %.1f cm" % (moved("positive").sum(), len(P), np.median(np.abs(s_)), np.median(np.abs(f))))
for lo, hi in ((0, 3), (3, 8), (8, 100)):
    m = (np.abs(f) >= lo) & (np.abs(f) < hi)
    if m.sum() >= 3: print("   predicted %g-%g cm (%d cases): sign right %d, slope through origin %.2f" % (lo, hi, m.sum(), sign[m].sum(), (f[m] @ s_[m]) / (f[m] @ f[m])))
# per storm slope (Mythos asked)
for st in range(3):
    ff, ss = [], []
    for i in P:
        a = np.abs(np.where(far[i], dF[i, st], 0)); r = a.argmax()
        if a[r] >= 0.01: ff.append(dF[i, st, r]); ss.append(dS[i, st, r])
    ff, ss = np.array(ff), np.array(ss)
    if len(ff) >= 5: print("   storm %d (net %.0f mm): %d cases with >= 1 cm predicted; slope through origin %.2f, Spearman %.2f" % (st, d["net_mm"][st], len(ff), (ff @ ss) / (ff @ ff), spearmanr(ff, ss)[0]))
# ---- random
R = np.flatnonzero(kind == "random"); fp = np.abs(np.where(far[R][:, None, :], dF[R], 0)).max((1, 2)) * 100; sm = np.abs(np.where(far[R][:, None, :], dS[R], 0)).max((1, 2)) * 100
print("RANDOM patches (30, no pass line): fill predicts < 1 mm effect for %d; of those the solver moves a receptor >= 1 cm in %d. Fill predicts >= 1 mm for %d; of those the solver moves >= 1 cm in %d." % ((fp < 0.1).sum(), ((fp < 0.1) & (sm >= 1)).sum(), (fp >= 0.1).sum(), ((fp >= 0.1) & (sm >= 1)).sum()))
print("   random: largest solver change cm: median %.2f max %.2f" % (np.median(sm), sm.max()))
# screen as a classifier over all 120
pred = np.abs(np.where(far[:, None, :], dF, 0)).max((1, 2)) >= 0.001; act = mv.any((1, 2))
print("SCREEN over all 120 patches (fill predicts any change vs solver moves a receptor >= 1 cm): both %d, fill only %d, solver only %d, neither %d" % ((pred & act).sum(), (pred & ~act).sum(), (~pred & act).sum(), (~pred & ~act).sum()))
np.savez("results/air/p1_scored.npz", dS=dS.astype(np.float32), pos_pred_cm=f, pos_sim_cm=s_, null_moved=nm)
